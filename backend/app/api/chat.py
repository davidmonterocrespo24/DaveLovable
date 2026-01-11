import json
from typing import List

from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ChatSession,
    ChatSessionCreate,
    ChatSessionWithMessages,
)
from app.services import ChatService

router = APIRouter()


@router.post("/{project_id}/stream")
async def send_chat_message_stream(project_id: int, chat_request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a chat message and stream AI response with real-time agent interactions

    This endpoint uses Server-Sent Events (SSE) to stream:
    - Agent thoughts and decisions
    - Tool calls and their arguments
    - Tool execution results
    - Final response with code changes
    """

    async def event_generator():
        import asyncio
        from datetime import datetime as dt

        last_heartbeat = dt.now()

        try:
            async for event in ChatService.process_chat_message_stream(db, project_id, chat_request):
                # Send keep-alive comment if it's been more than 15 seconds since last event
                now = dt.now()
                if (now - last_heartbeat).total_seconds() > 15:
                    # Send SSE comment to keep connection alive (starts with :)
                    yield ": keep-alive\n\n"
                    last_heartbeat = now

                # Format as SSE event
                yield f"data: {json.dumps(event)}\n\n"

                # Update heartbeat time after sending event
                last_heartbeat = dt.now()

                # Small delay to prevent overwhelming the client
                await asyncio.sleep(0.01)

        except Exception as e:
            # Send error event
            error_event = {"type": "error", "data": {"message": str(e)}}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.post("/{project_id}", response_model=ChatResponse)
async def send_chat_message(project_id: int, chat_request: ChatRequest, db: Session = Depends(get_db)):
    """
    Send a chat message and get AI response (non-streaming, backward compatible)

    This endpoint:
    - Creates a new session if session_id is not provided
    - Saves the user message
    - Generates AI response using AutoGen agents
    - Updates project files based on AI response
    - Returns the assistant's message and code changes
    """
    return await ChatService.process_chat_message(db, project_id, chat_request)


@router.post("/{project_id}/sessions", response_model=ChatSession, status_code=status.HTTP_201_CREATED)
def create_chat_session(project_id: int, session_data: ChatSessionCreate, db: Session = Depends(get_db)):
    """Create a new chat session"""
    return ChatService.create_session(db, session_data)


@router.get("/{project_id}/sessions", response_model=List[ChatSession])
def get_chat_sessions(project_id: int, db: Session = Depends(get_db)):
    """Get all chat sessions for a project"""
    return ChatService.get_sessions(db, project_id)


@router.get("/{project_id}/sessions/{session_id}", response_model=ChatSessionWithMessages)
def get_chat_session(project_id: int, session_id: int, db: Session = Depends(get_db)):
    """Get a specific chat session with all messages"""
    from app.schemas.chat import ChatMessage as ChatMessageSchema

    session = ChatService.get_session(db, session_id, project_id)
    db_messages = ChatService.get_messages(db, session_id)

    # Parse agent_interactions from message_metadata for each message
    messages = [ChatMessageSchema.from_db_message(msg) for msg in db_messages]

    return {
        "id": session.id,
        "project_id": session.project_id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": messages,
    }


@router.get("/{project_id}/sessions/{session_id}/messages", response_model=List[ChatMessage])
def get_session_messages(project_id: int, session_id: int, limit: int = 100, db: Session = Depends(get_db)):
    """Get messages for a chat session"""
    # Verify session belongs to project
    ChatService.get_session(db, session_id, project_id)
    return ChatService.get_messages(db, session_id, limit)


@router.get("/{project_id}/sessions/{session_id}/reconnect")
async def reconnect_to_session(
    project_id: int, session_id: int, since_message_id: int = 0, db: Session = Depends(get_db)
):
    """
    Reconnect to a session and get any new messages since the last known message

    This endpoint helps recover from interrupted streams:
    - Returns messages created after since_message_id
    - Includes partial/ongoing AI responses
    - Allows frontend to catch up after refresh/disconnection
    """
    from app.schemas.chat import ChatMessage as ChatMessageSchema

    # Verify session belongs to project
    session = ChatService.get_session(db, session_id, project_id)

    # Get all messages after the specified message_id
    all_messages = ChatService.get_messages(db, session_id, limit=1000)

    # Filter messages that come after since_message_id
    new_messages = [msg for msg in all_messages if msg.id > since_message_id]

    # Parse agent_interactions from message_metadata
    messages = [ChatMessageSchema.from_db_message(msg) for msg in new_messages]

    return {
        "session_id": session_id,
        "project_id": project_id,
        "new_messages": messages,
        "total_messages": len(all_messages),
        "has_more": len(new_messages) > 0,
    }


@router.delete("/{project_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(project_id: int, session_id: int, db: Session = Depends(get_db)):
    """Delete a chat session"""
    ChatService.delete_session(db, session_id, project_id)
    return None
