# src/models.py (New file for Pydantic models)
from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None

class ChatResponse(BaseModel):
    response: str
    session_id: UUID
    is_complete: bool  # True if satisfaction reached or session ended