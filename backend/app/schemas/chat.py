from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, field_serializer

from app.models.chat import MessageRole


class ChatMessageBase(BaseModel):
    role: MessageRole
    content: str
    agent_name: Optional[str] = None
    message_metadata: Optional[str] = None


class ChatMessageCreate(ChatMessageBase):
    session_id: int


class ChatMessageInDB(ChatMessageBase):
    id: int
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at')
    def serialize_created_at(self, dt: datetime, _info):
        """Serialize datetime as ISO format with UTC timezone"""
        # Ensure datetime is UTC-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class ChatMessage(ChatMessageInDB):
    agent_interactions: Optional[List[dict]] = None
    attachments: Optional[List[dict]] = None

    @classmethod
    def from_db_message(cls, db_message):
        """Convert database message to ChatMessage with parsed agent_interactions and attachments"""
        import json

        agent_interactions = None
        attachments = None

        if db_message.message_metadata:
            try:
                metadata = json.loads(db_message.message_metadata)
                agent_interactions = metadata.get("agent_interactions", None)
                attachments = metadata.get("attachments", None)
            except:
                pass

        return cls(
            id=db_message.id,
            session_id=db_message.session_id,
            role=db_message.role,
            content=db_message.content,
            agent_name=db_message.agent_name,
            message_metadata=db_message.message_metadata,
            created_at=db_message.created_at,
            agent_interactions=agent_interactions,
            attachments=attachments,
        )


class ChatSessionBase(BaseModel):
    title: Optional[str] = "New Chat"


class ChatSessionCreate(ChatSessionBase):
    project_id: int


class ChatSessionInDB(ChatSessionBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @field_serializer('created_at', 'updated_at')
    def serialize_datetime(self, dt: datetime, _info):
        """Serialize datetime as ISO format with UTC timezone"""
        # Ensure datetime is UTC-aware
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()


class ChatSession(ChatSessionInDB):
    pass


class ChatSessionWithMessages(ChatSession):
    messages: List[ChatMessage] = []


class FileAttachment(BaseModel):
    """Multimodal file attachment (image or PDF)"""
    type: str  # "image" or "pdf"
    mime_type: str
    data: str  # Base64 encoded data
    name: str


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None
    attachments: Optional[List[FileAttachment]] = None  # Multimodal support


class AgentInteraction(BaseModel):
    agent_name: str
    message_type: str  # "thought", "tool_call", "tool_response"
    content: str
    tool_name: Optional[str] = None
    tool_arguments: Optional[dict] = None
    timestamp: datetime


class ChatResponse(BaseModel):
    session_id: int
    message: ChatMessage
    code_changes: Optional[List[dict]] = None
    agent_interactions: Optional[List[AgentInteraction]] = None
