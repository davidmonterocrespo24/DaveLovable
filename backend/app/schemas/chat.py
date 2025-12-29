from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
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

class ChatMessage(ChatMessageInDB):
    agent_interactions: Optional[List[dict]] = None

    @classmethod
    def from_db_message(cls, db_message):
        """Convert database message to ChatMessage with parsed agent_interactions"""
        import json
        agent_interactions = None

        if db_message.message_metadata:
            try:
                metadata = json.loads(db_message.message_metadata)
                agent_interactions = metadata.get("agent_interactions", None)
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
            agent_interactions=agent_interactions
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

class ChatSession(ChatSessionInDB):
    pass

class ChatSessionWithMessages(ChatSession):
    messages: List[ChatMessage] = []

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[int] = None

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
