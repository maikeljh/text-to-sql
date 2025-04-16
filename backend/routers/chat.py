from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from ai_agent.ai_agent import AgentState, graph
from models.models import User, ChatHistory, ChatMessage
from database.db import get_db
from utils.misc import generate_title
from utils.auth import get_current_user_id

import orjson


router = APIRouter()


class QueryRequest(BaseModel):
    query: str
    chat_id: Optional[int] = None


@router.post("/query")
async def handle_query(
    req: QueryRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter_by(id=user_id).first()
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

    messages = (
        db.query(ChatMessage)
        .filter_by(chat_id=chat.id)
        .order_by(ChatMessage.timestamp)
        .all()
    )

    history = [
        {
            "user": m.user_input,
            "agent": orjson.loads(m.agent_response) if isinstance(m.agent_response, str) else m.agent_response,
        }
        for m in messages
    ]

    # Invoke the agent graph
    agent_input = AgentState(query=req.query, history=history)
    result = graph.invoke(agent_input)

    # Extract final response and data
    intent = result.get("DetectIntent", "")
    detail = result.get("CheckDetails", "")
    summary = result.get("Summary", "")
    data = result.get("GenerateSQL", [])

    # Compose final agent response
    if intent == "other":
        response = {
            "response": "Sorry, I can only help with business-related questions. Please ask something involving data insights.",
            "data": [],
        }
    elif detail == "no":
        response = {
            "response": "Could you provide more specific details so I can give detailed data insights for you?",
            "data": [],
        }
    else:
        response = {
            "response": summary,
            "data": data,
        }

    # Save chat message to history
    chat_msg = ChatMessage(
        chat_id=chat.id,
        user_input=req.query,
        agent_response=orjson.dumps(response, default=str).decode(),
    )
    db.add(chat_msg)
    db.commit()

    # Return response
    return {
        "chat_id": chat.id,
        **response
    }


@router.get("/histories")
def get_all_chat_histories(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    histories = (
        db.query(ChatHistory)
        .filter_by(user_id=user_id)
        .order_by(ChatHistory.created_at.desc())
        .all()
    )

    return [
        {
            "id": h.id,
            "title": h.title,
            "created_at": h.created_at.isoformat(),
        }
        for h in histories
    ]


@router.get("/history/{chat_id}")
def get_chat_history_by_id(
    chat_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    chat = db.query(ChatHistory).filter_by(id=chat_id, user_id=user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    messages = (
        db.query(ChatMessage)
        .filter_by(chat_id=chat_id)
        .order_by(ChatMessage.timestamp.asc())
        .all()
    )

    return {
        "chat_id": chat.id,
        "chat_title": chat.title,
        "messages": [
            {
                "user": m.user_input,
                "agent": (
                    orjson.loads(m.agent_response)
                    if isinstance(m.agent_response, str)
                    else m.agent_response
                ),
                "timestamp": m.timestamp.isoformat(),
            }
            for m in messages
        ],
    }
