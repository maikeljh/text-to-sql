from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ai_agent.ai_agent import graph
from models.models import User, ChatHistory, ChatMessage
from database.db import get_db
from utils.misc import generate_title

router = APIRouter()

class QueryRequest(BaseModel):
    user_id: int
    query: str
    chat_id: Optional[int] = None

@router.post("/query")
async def handle_query(req: QueryRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(id=req.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if req.chat_id:
        chat = db.query(ChatHistory).filter_by(id=req.chat_id, user_id=user.id).first()
        if not chat:
            raise HTTPException(status_code=404, detail="Chat not found")
    else:
        chat = ChatHistory(title=generate_title(req.query), user_id=user.id)
        db.add(chat)
        db.commit()
        db.refresh(chat)

    messages = db.query(ChatMessage).filter_by(chat_id=chat.id).order_by(ChatMessage.timestamp).all()
    history = [{"user": m.user_input, "agent": m.agent_response} for m in messages]

    result = await graph.invoke({"query": req.query, "history": history})
    response = result.get("GenerateSQL", "")

    chat_msg = ChatMessage(chat_id=chat.id, user_input=req.query, agent_response=response)
    db.add(chat_msg)
    db.commit()

    return {
        "chat_id": chat.id,
        "chat_title": chat.title,
        "result": response,
        "history": history + [{"user": req.query, "agent": response}]
    }
