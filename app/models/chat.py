from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class Message(BaseModel):
    role: str = Field(..., description="Sender role: 'user' or 'assistant'")
    content: str = Field(..., description="Message text")
    timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow)


class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique chat ID")
    user_id: str = Field(..., description="ID of the user who owns this chat")
    title: str = Field(default="New Chat", description="Chat title or preview text")
    language: str = Field(default="en", description="Language code for translations")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True
