from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ChatCreate(BaseModel):
    title: str = Field(default="New Chat", max_length=200)
 
 
class ChatOut(BaseModel):
    id: str
    title: str
    session_id: Optional[str]
    pdf_filename: Optional[str]
    created_at: datetime
 
    model_config = {"from_attributes": True}

class MessageRequest(BaseModel):
    content: str = Field(..., min_length=1)
 
 
class MessageResponse(BaseModel):
    role: str
    content: str
    judge_verdict: Optional[str] = None
    judge_reason: Optional[str] = None
 
class UploadResponse(BaseModel):
    session_id: str
    chunks_ingested: int
    message: str
 
class ChatRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)