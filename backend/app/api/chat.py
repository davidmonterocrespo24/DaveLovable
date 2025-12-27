from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    ChatSession,
    ChatSessionCreate,
    ChatSessionWithMessages,
    ChatMessage,
    ChatRequest,
    ChatResponse,
)
from app.services import ChatService

router = APIRouter()


@router.post("/{project_id}", response_model=ChatResponse)
async def send_chat_message(
    project_id: int,
    chat_request: ChatRequest,
    db: Session = Depends(get_db)
):
    """
    Send a chat message and get AI response

    This endpoint:
    - Creates a new session if session_id is not provided
    - Saves the user message
    - Generates AI response using AutoGen agents
    - Updates project files based on AI response
    - Returns the assistant's message and code changes
    """
    return await ChatService.process_chat_message(db, project_id, chat_request)


@router.post("/{project_id}/sessions", response_model=ChatSession, status_code=status.HTTP_201_CREATED)
def create_chat_session(
    project_id: int,
    session_data: ChatSessionCreate,
    db: Session = Depends(get_db)
):
    """Create a new chat session"""
    return ChatService.create_session(db, session_data)


@router.get("/{project_id}/sessions", response_model=List[ChatSession])
def get_chat_sessions(
    project_id: int,
    db: Session = Depends(get_db)
):
    """Get all chat sessions for a project"""
    return ChatService.get_sessions(db, project_id)


@router.get("/{project_id}/sessions/{session_id}", response_model=ChatSessionWithMessages)
def get_chat_session(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific chat session with all messages"""
    session = ChatService.get_session(db, session_id, project_id)
    messages = ChatService.get_messages(db, session_id)

    return {
        "id": session.id,
        "project_id": session.project_id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": messages,
    }


@router.get("/{project_id}/sessions/{session_id}/messages", response_model=List[ChatMessage])
def get_session_messages(
    project_id: int,
    session_id: int,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get messages for a chat session"""
    # Verify session belongs to project
    ChatService.get_session(db, session_id, project_id)
    return ChatService.get_messages(db, session_id, limit)


@router.delete("/{project_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    project_id: int,
    session_id: int,
    db: Session = Depends(get_db)
):
    """Delete a chat session"""
    ChatService.delete_session(db, session_id, project_id)
    return None
