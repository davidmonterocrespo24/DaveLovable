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

                # Run the agent team (Planner + Coder)
                # The Coder agent will use tools to create/modify files directly
                result = await orchestrator.main_team.run(
                    task=task_description,
                    cancellation_token=CancellationToken()
                )

                logger.info("="*80)
                logger.info("✅ MULTI-AGENT TEAM EXECUTION COMPLETED")
                logger.info("="*80)
            finally:
                # Always restore original working directory
                os.chdir(original_cwd)
                logger.info(f"📂 Restored working directory to: {original_cwd}")

            # Extract the final response from the team's messages
            # The last message should contain the summary or completion status
            response_content = ""
            agent_name = "Team"

            logger.info(f"\n📨 Processing {len(result.messages)} messages from agents...")

            # Log all messages from the conversation
            for i, msg in enumerate(result.messages, 1):
                msg_source = msg.source if hasattr(msg, 'source') else "Unknown"
                msg_content = msg.content if hasattr(msg, 'content') else str(msg)

                logger.info("─" * 80)
                logger.info(f"💬 Message {i}/{len(result.messages)} - From: {msg_source}")
                logger.info("─" * 80)

                # Check if this is a tool call message
                if hasattr(msg, 'content') and isinstance(msg.content, list):
                    for item in msg.content:
                        if hasattr(item, 'name'):  # Tool call
                            logger.info(f"🔧 TOOL CALL: {item.name}")
                            if hasattr(item, 'arguments'):
                                logger.info(f"   Arguments: {item.arguments}")
                        else:
                            logger.info(f"   Content: {str(item)[:200]}")
                else:
                    # Regular text message
                    content_preview = msg_content[:500] + "..." if len(msg_content) > 500 else msg_content
                    logger.info(f"   {content_preview}")

                logger.info("")

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
    def delete_session(db: Session, session_id: int, project_id: int) -> bool:
        """Delete a chat session"""

        session = ChatService.get_session(db, session_id, project_id)
        db.delete(session)
        db.commit()
        return True
