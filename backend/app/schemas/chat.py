from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from app.models.chat import MessageRole

class ChatMessageBase(BaseModel):
    role: MessageRole
    content: str
    agent_name: Optional[str] = None
    metadata: Optional[str] = None

class ChatMessageCreate(ChatMessageBase):
    session_id: int

class ChatMessageInDB(ChatMessageBase):
    id: int
    session_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class ChatMessage(ChatMessageInDB):
    pass

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

class ChatResponse(BaseModel):
    session_id: int
    message: ChatMessage
    code_changes: Optional[List[dict]] = None
