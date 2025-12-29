from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models import ChatSession, ChatMessage, MessageRole, ProjectFile
from app.schemas import ChatSessionCreate, ChatMessageCreate, ChatRequest
from app.agents import get_orchestrator
from app.services.filesystem_service import FileSystemService
from fastapi import HTTPException, status
from autogen_core import CancellationToken
from datetime import datetime
import logging

# Configure logging for agent interactions
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class ChatService:
    """Service for managing chat sessions and AI interactions"""

    @staticmethod
    def create_session(db: Session, session_data: ChatSessionCreate) -> ChatSession:
        """Create a new chat session"""

        db_session = ChatSession(**session_data.model_dump())
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        return db_session

    @staticmethod
    def get_session(db: Session, session_id: int, project_id: int) -> ChatSession:
        """Get a chat session by ID"""

        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.project_id == project_id
        ).first()

        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )

        return session

    @staticmethod
    def get_sessions(db: Session, project_id: int) -> List[ChatSession]:
        """Get all chat sessions for a project"""

        return db.query(ChatSession).filter(
            ChatSession.project_id == project_id
        ).order_by(ChatSession.updated_at.desc()).all()

    @staticmethod
    def add_message(db: Session, message_data: ChatMessageCreate) -> ChatMessage:
        """Add a message to a chat session"""

        db_message = ChatMessage(**message_data.model_dump())
        db.add(db_message)
        db.commit()
        db.refresh(db_message)
        return db_message

    @staticmethod
    def get_messages(db: Session, session_id: int, limit: int = 100) -> List[ChatMessage]:
        """Get messages for a session"""

        return db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).limit(limit).all()

    @staticmethod
    async def process_chat_message(
        db: Session,
        project_id: int,
        chat_request: ChatRequest
    ) -> Dict:
        """
        Process a chat message and generate AI response

        Args:
            db: Database session
            project_id: Project ID
            chat_request: Chat request with message and optional session_id

        Returns:
            Dict with session_id, message, and code_changes
        """

        # Get or create chat session
        if chat_request.session_id:
            session = ChatService.get_session(db, chat_request.session_id, project_id)
        else:
            session = ChatService.create_session(
                db,
                ChatSessionCreate(project_id=project_id)
            )

        # Save user message
        user_message = ChatService.add_message(
            db,
            ChatMessageCreate(
                session_id=session.id,
                role=MessageRole.USER,
                content=chat_request.message
            )
        )

        # Get project context (existing files from filesystem)
        project_files = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id
        ).all()

        context = {
            "project_id": project_id,
            "files": [
                {
                    "filename": f.filename,
                    "filepath": f.filepath,
                    "language": f.language,
                    "content": (FileSystemService.read_file(project_id, f.filepath) or "")[:500],  # First 500 chars for context
                }
                for f in project_files
            ]
        }

        # Generate AI response using agents
        try:
            orchestrator = get_orchestrator()
        except ValueError as e:
            # API key not configured
            error_message = ChatService.add_message(
                db,
                ChatMessageCreate(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=str(e)
                )
            )
            return {
                "session_id": session.id,
                "message": error_message,
                "code_changes": [],
            }

        try:
            # Set working directory to the project directory so agent tools work correctly
            import os
            from pathlib import Path
            from app.core.config import settings

            project_dir = Path(settings.PROJECTS_BASE_DIR) / f"project_{project_id}"
            original_cwd = os.getcwd()

            try:
                os.chdir(project_dir)
                logger.info(f"📂 Changed working directory to: {project_dir}")

                # Build task description with context for the agents
                task_description = f"""User Request: {chat_request.message}

Project Context:
- Project ID: {project_id}
- Working Directory: {project_dir}
- Existing Files: {len(context['files'])} files
- Files: {', '.join([f['filepath'] for f in context['files']])}

IMPORTANT: You are working in the project directory. All file operations will be relative to this directory.
Please analyze the request, create a plan if needed, and implement the solution."""

                logger.info("="*80)
                logger.info("🤖 STARTING MULTI-AGENT TEAM EXECUTION")
                logger.info("="*80)
                logger.info(f"📝 User Request: {chat_request.message}")
                logger.info(f"📁 Project Files: {len(context['files'])}")
                logger.info("="*80)

                # List to collect agent interactions as events stream in
                agent_interactions = []

                # Run the agent team using run_stream to capture events in real-time
                async for message in orchestrator.main_team.run_stream(
                    task=task_description,
                    cancellation_token=CancellationToken()
                ):
                    # Get event type
                    event_type = type(message).__name__
                    msg_source = message.source if hasattr(message, 'source') else "Unknown"
                    msg_timestamp = message.created_at if hasattr(message, 'created_at') else datetime.now()

                    logger.info(f"📨 Event: {event_type} from {msg_source}")

                    # TextMessage - Agent thoughts/responses
                    if event_type == "TextMessage":
                        content_preview = message.content[:200] if len(message.content) > 200 else message.content
                        logger.info(f"💭 {msg_source}: {content_preview}")

                        if msg_source != "user" and "TASK_COMPLETED" not in message.content:
                            agent_interactions.append({
                                "agent_name": msg_source,
                                "message_type": "thought",
                                "content": message.content,
                                "tool_name": None,
                                "tool_arguments": None,
                                "timestamp": msg_timestamp
                            })

                    # ToolCallRequestEvent - Tool calls
                    elif event_type == "ToolCallRequestEvent":
                        for tool_call in message.content:
                            logger.info(f"🔧 Tool: {tool_call.name}")
                            tool_args = {}
                            try:
                                import json
                                tool_args = json.loads(tool_call.arguments) if isinstance(tool_call.arguments, str) else tool_call.arguments
                            except:
                                tool_args = {"raw": str(tool_call.arguments)}

                            agent_interactions.append({
                                "agent_name": msg_source,
                                "message_type": "tool_call",
                                "content": f"Calling: {tool_call.name}",
                                "tool_name": tool_call.name,
                                "tool_arguments": tool_args,
                                "timestamp": msg_timestamp
                            })

                    # ToolCallExecutionEvent - Tool results
                    elif event_type == "ToolCallExecutionEvent":
                        for tool_result in message.content:
                            result_preview = str(tool_result.content)[:200]
                            logger.info(f"✅ Result ({tool_result.name}): {result_preview}")

                            agent_interactions.append({
                                "agent_name": "System",
                                "message_type": "tool_response",
                                "content": tool_result.content,
                                "tool_name": tool_result.name,
                                "tool_arguments": None,
                                "timestamp": msg_timestamp
                            })

                    # TaskResult - Final
                    elif event_type == "TaskResult":
                        result = message
                        logger.info("="*80)
                        logger.info("✅ EXECUTION COMPLETED")
                        logger.info("="*80)
            finally:
                # Always restore original working directory
                os.chdir(original_cwd)
                logger.info(f"📂 Restored working directory to: {original_cwd}")

            # Extract the final response from the result
            response_content = ""
            agent_name = "Team"

            # Get the final response from the last message
            if result.messages:
                # Get the last message from the team
                last_message = result.messages[-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                agent_name = last_message.source if hasattr(last_message, 'source') else "Team"

                logger.info("="*80)
                logger.info(f"📤 FINAL RESPONSE (from {agent_name}):")
                logger.info("="*80)
                logger.info(response_content[:1000])
                logger.info("="*80)
            else:
                response_content = "I processed your request successfully."
                logger.warning("⚠️  No messages in result, using default response")

            # Note: File changes are now handled by the Coder agent's tools
            # We don't need to manually create/update files anymore
            # The agent uses write_file, edit_file tools directly

            # Save assistant message with the team's response
            assistant_message = ChatService.add_message(
                db,
                ChatMessageCreate(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=response_content,
                    agent_name=agent_name
                )
            )

            return {
                "session_id": session.id,
                "message": assistant_message,
                "code_changes": [],  # Changes are handled by agent tools, not tracked here
                "agent_interactions": agent_interactions,
            }

        except Exception as e:
            logger.error("="*80)
            logger.error("❌ ERROR DURING AGENT EXECUTION")
            logger.error("="*80)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error message: {str(e)}")
            logger.error("="*80)

            # Log full traceback
            import traceback
            logger.error("Full traceback:")
            logger.error(traceback.format_exc())

            # Save error message
            error_message = ChatService.add_message(
                db,
                ChatMessageCreate(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=f"I encountered an error: {str(e)}. Please try again.",
                    agent_name="System"
                )
            )

            return {
                "session_id": session.id,
                "message": error_message,
                "code_changes": [],
            }

    @staticmethod
    async def process_chat_message_stream(
        db: Session,
        project_id: int,
        chat_request: ChatRequest
    ):
        """
        Process a chat message and stream AI response events in real-time

        Yields events for:
        - Agent thoughts (thought)
        - Tool calls (tool_call)
        - Tool execution results (tool_response)
        - Final response (complete)
        """

        # Get or create chat session
        if chat_request.session_id:
            session = ChatService.get_session(db, chat_request.session_id, project_id)
        else:
            session = ChatService.create_session(
                db,
                ChatSessionCreate(project_id=project_id)
            )

        # Save user message
        user_message = ChatService.add_message(
            db,
            ChatMessageCreate(
                session_id=session.id,
                role=MessageRole.USER,
                content=chat_request.message
            )
        )

        # Yield initial event
        yield {
            "type": "start",
            "data": {
                "session_id": session.id,
                "user_message_id": user_message.id
            }
        }

        # Get project context
        project_files = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id
        ).all()

        context = {
            "project_id": project_id,
            "files": [
                {
                    "filename": f.filename,
                    "filepath": f.filepath,
                    "language": f.language,
                    "content": (FileSystemService.read_file(project_id, f.filepath) or "")[:500],
                }
                for f in project_files
            ]
        }

        # Generate AI response using agents
        try:
            orchestrator = get_orchestrator()
        except ValueError as e:
            # API key not configured
            yield {
                "type": "error",
                "data": {"message": str(e)}
            }
            return

        try:
            import os
            from pathlib import Path
            from app.core.config import settings

            project_dir = Path(settings.PROJECTS_BASE_DIR) / f"project_{project_id}"
            original_cwd = os.getcwd()

            try:
                os.chdir(project_dir)
                logger.info(f"📂 Changed working directory to: {project_dir}")

                # Build task description
                task_description = f"""User Request: {chat_request.message}

Project Context:
- Project ID: {project_id}
- Working Directory: {project_dir}
- Existing Files: {len(context['files'])} files
- Files: {', '.join([f['filepath'] for f in context['files']])}

IMPORTANT: You are working in the project directory. All file operations will be relative to this directory.
Please analyze the request, create a plan if needed, and implement the solution."""

                logger.info("="*80)
                logger.info("🤖 STARTING MULTI-AGENT TEAM EXECUTION (STREAMING)")
                logger.info("="*80)

                # Load saved agent state if it exists
                state_loaded = await orchestrator.load_state(project_id)
                if state_loaded:
                    logger.info(f"♻️  Restored agent state from previous session")

                # List to collect all agent interactions for database storage
                agent_interactions = []

                # Stream agent events in real-time
                async for message in orchestrator.main_team.run_stream(
                    task=task_description,
                    cancellation_token=CancellationToken()
                ):
                    event_type = type(message).__name__
                    msg_source = message.source if hasattr(message, 'source') else "Unknown"
                    msg_timestamp = message.created_at if hasattr(message, 'created_at') else datetime.now()

                    logger.info(f"📨 Event: {event_type} from {msg_source}")

                    # TextMessage - Agent thoughts/responses
                    if event_type == "TextMessage":
                        if msg_source != "user" and "TASK_COMPLETED" not in message.content:
                            interaction_data = {
                                "agent_name": msg_source,
                                "message_type": "thought",
                                "content": message.content,
                                "tool_name": None,
                                "tool_arguments": None,
                                "timestamp": msg_timestamp.isoformat() if hasattr(msg_timestamp, 'isoformat') else str(msg_timestamp)
                            }
                            # Add to list for database storage
                            agent_interactions.append(interaction_data)
                            # Stream to frontend
                            yield {
                                "type": "agent_interaction",
                                "data": interaction_data
                            }

                    # ToolCallRequestEvent - Tool calls
                    elif event_type == "ToolCallRequestEvent":
                        for tool_call in message.content:
                            tool_args = {}
                            try:
                                import json
                                tool_args = json.loads(tool_call.arguments) if isinstance(tool_call.arguments, str) else tool_call.arguments
                            except:
                                tool_args = {"raw": str(tool_call.arguments)}

                            interaction_data = {
                                "agent_name": msg_source,
                                "message_type": "tool_call",
                                "content": f"Calling: {tool_call.name}",
                                "tool_name": tool_call.name,
                                "tool_arguments": tool_args,
                                "timestamp": msg_timestamp.isoformat() if hasattr(msg_timestamp, 'isoformat') else str(msg_timestamp)
                            }
                            # Add to list for database storage
                            agent_interactions.append(interaction_data)
                            # Stream to frontend
                            yield {
                                "type": "agent_interaction",
                                "data": interaction_data
                            }

                    # ToolCallExecutionEvent - Tool results
                    elif event_type == "ToolCallExecutionEvent":
                        for tool_result in message.content:
                            interaction_data = {
                                "agent_name": "System",
                                "message_type": "tool_response",
                                "content": str(tool_result.content),
                                "tool_name": tool_result.name,
                                "tool_arguments": None,
                                "timestamp": msg_timestamp.isoformat() if hasattr(msg_timestamp, 'isoformat') else str(msg_timestamp)
                            }
                            # Add to list for database storage
                            agent_interactions.append(interaction_data)
                            # Stream to frontend
                            yield {
                                "type": "agent_interaction",
                                "data": interaction_data
                            }

                    # TaskResult - Final
                    elif event_type == "TaskResult":
                        result = message
                        logger.info("="*80)
                        logger.info("✅ EXECUTION COMPLETED")
                        logger.info("="*80)

            finally:
                os.chdir(original_cwd)
                logger.info(f"📂 Restored working directory to: {original_cwd}")

            # Extract final response
            response_content = ""
            agent_name = "Team"

            if result.messages:
                last_message = result.messages[-1]
                response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
                agent_name = last_message.source if hasattr(last_message, 'source') else "Team"
            else:
                response_content = "I processed your request successfully."

            # Save assistant message with agent_interactions in metadata
            import json
            assistant_message = ChatService.add_message(
                db,
                ChatMessageCreate(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=response_content,
                    agent_name=agent_name,
                    message_metadata=json.dumps({"agent_interactions": agent_interactions})
                )
            )

            # Save agent state to disk for future sessions
            await orchestrator.save_state(project_id)

            # Yield final completion event
            yield {
                "type": "complete",
                "data": {
                    "session_id": session.id,
                    "message": {
                        "id": assistant_message.id,
                        "session_id": assistant_message.session_id,
                        "role": assistant_message.role.value,
                        "content": assistant_message.content,
                        "agent_name": assistant_message.agent_name,
                        "created_at": assistant_message.created_at.isoformat()
                    },
                    "code_changes": []
                }
            }

        except Exception as e:
            logger.error("="*80)
            logger.error("❌ ERROR DURING AGENT EXECUTION")
            logger.error("="*80)
            logger.error(f"Error: {str(e)}")
            logger.error("="*80)

            import traceback
            logger.error(traceback.format_exc())

            yield {
                "type": "error",
                "data": {"message": str(e)}
            }

    @staticmethod
    def delete_session(db: Session, session_id: int, project_id: int) -> bool:
        """Delete a chat session"""

        session = ChatService.get_session(db, session_id, project_id)
        db.delete(session)
        db.commit()
        return True
