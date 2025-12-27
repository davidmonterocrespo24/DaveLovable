from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models import ChatSession, ChatMessage, MessageRole, ProjectFile
from app.schemas import ChatSessionCreate, ChatMessageCreate, ChatRequest
from app.agents import get_orchestrator
from fastapi import HTTPException, status
import json


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

        # Get project context (existing files)
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
                    "content": f.content[:500],  # First 500 chars for context
                }
                for f in project_files
            ]
        }

        # Generate AI response using agents
        orchestrator = get_orchestrator()

        try:
            # Use quick generation for now (can be enhanced with full orchestration)
            result = orchestrator.generate_code(chat_request.message, context)

            # Prepare response content
            response_content = "I've generated the code based on your request."
            code_changes = []

            if result.get("success") and result.get("code"):
                code_changes = result["code"]

                # Update or create files in the project
                for code_block in code_changes:
                    filename = code_block.get("filename")
                    content = code_block.get("content")
                    language = code_block.get("language")

                    # Check if file exists
                    existing_file = db.query(ProjectFile).filter(
                        ProjectFile.project_id == project_id,
                        ProjectFile.filename == filename
                    ).first()

                    if existing_file:
                        existing_file.content = content
                        if language:
                            existing_file.language = language
                    else:
                        # Create new file
                        new_file = ProjectFile(
                            project_id=project_id,
                            filename=filename,
                            filepath=f"src/{filename}",
                            content=content,
                            language=language
                        )
                        db.add(new_file)

                db.commit()

                response_content += f"\n\nI've created/updated {len(code_changes)} file(s) for you."

            # Save assistant message
            assistant_message = ChatService.add_message(
                db,
                ChatMessageCreate(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=response_content,
                    agent_name="CodingAgent",
                    metadata=json.dumps({"code_changes": code_changes})
                )
            )

            return {
                "session_id": session.id,
                "message": assistant_message,
                "code_changes": code_changes,
            }

        except Exception as e:
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
