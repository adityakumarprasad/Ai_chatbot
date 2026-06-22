from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str
    thread_id: Optional[str] = None

class ThreadCreateResponse(BaseModel):
    thread_id: str

class ThreadListResponse(BaseModel):
    threads: List[str]

class MessageResponse(BaseModel):
    role: str
    content: str
    name: Optional[str] = None

class HistoryResponse(BaseModel):
    messages: List[MessageResponse]
