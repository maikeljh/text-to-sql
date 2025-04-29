from pydantic import BaseModel
from typing import Optional, Literal


class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class QueryRequest(BaseModel):
    query: str
    chat_id: Optional[int] = None
    model: str
    provider: str
    database: str

class FeedbackRequest(BaseModel):
    message_id: int
    feedback: Literal["positive", "negative"]