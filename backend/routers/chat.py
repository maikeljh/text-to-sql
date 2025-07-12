from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ai_agent.ai_agent import AgentState, build_graph
from models.models import User, ChatHistory, ChatMessage, ChatFeedback
from models.schemas import QueryRequest, FeedbackRequest
from database.db import get_db
from utils.misc import generate_title
from utils.auth import get_current_user_id
from utils.enum import ENUM
from text_to_sql.core import GeneralLLM
from text_to_sql.common import LLMConfig
from text_to_sql.core import Summarization

import orjson
import pandas as pd
import re


router = APIRouter()


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

    # Configurations
    general_config = LLMConfig(
        type="api",
        model=req.model,
        provider=req.provider,
        api_key=ENUM.get(req.provider, ""),
    )

    # Initialize agents
    llm_agent = GeneralLLM(config=general_config)
    graph = build_graph(llm_agent)

    # Invoke the agent graph
    agent_input = AgentState(query=req.query, history=history, model=req.model, provider=req.provider, database=req.database)
    result = graph.invoke(agent_input)

    # Extract final response and data
    lang = result.get("Language", "en")
    intent = result.get("DetectIntent", "")
    detail = result.get("CheckDetails", "")
    summary = result.get("Summary", "")
    data = result.get("GenerateSQL", [])
    generated_sql_query = result.get("GeneratedQueryRaw", None)

    # Compose final agent response
    if intent == "other":
        response = {
            "response": "Maaf, saya hanya bisa membantu pertanyaan terkait bisnis dan data." if lang == "id" else
                        "Sorry, I can only help with business-related questions. Please ask something involving data insights.",
            "data": [],
        }
    elif detail == "no":
        response = {
            "response": "Bisa tolong berikan detail yang lebih spesifik agar saya bisa memberi insight data yang relevan?" if lang == "id" else
                        "Could you provide more specific details so I can give detailed data insights for you?",
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
        generated_query=generated_sql_query,
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
                "id": m.id,
                "user": m.user_input,
                "agent": (
                    orjson.loads(m.agent_response)
                    if isinstance(m.agent_response, str)
                    else m.agent_response
                ),
                "query": m.generated_query,
                "timestamp": m.timestamp.isoformat(),
                "feedback": m.feedback.feedback if m.feedback else None,
            }
            for m in messages
        ],
    }

@router.delete("/history/{chat_id}")
def delete_chat_history(
    chat_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    chat = db.query(ChatHistory).filter_by(id=chat_id, user_id=user_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    db.query(ChatMessage).filter_by(chat_id=chat_id).delete()
    db.delete(chat)
    db.commit()

    return {"detail": "Chat history deleted successfully"}

@router.post("/feedback")
def give_feedback(
    req: FeedbackRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    message = db.query(ChatMessage).filter_by(id=req.message_id).first()

    if not message:
        raise HTTPException(status_code=404, detail="Chat message not found")

    chat = db.query(ChatHistory).filter_by(id=message.chat_id, user_id=user_id).first()
    if not chat:
        raise HTTPException(status_code=403, detail="Not authorized to give feedback on this message")

    existing = db.query(ChatFeedback).filter_by(message_id=message.id).first()
    if existing:
        existing.feedback = req.feedback
    else:
        db.add(ChatFeedback(message_id=message.id, feedback=req.feedback))

    db.commit()
    
    # Add feedback to dataset
    if message.generated_query and req.feedback == "positive":
        general_config = LLMConfig(
            type="api",
            model=req.model,
            provider=req.provider,
            api_key=ENUM.get(req.provider, ""),
        )
        summarization = Summarization(config=general_config)
        dataset_path = f"./files/dataset/dataset_{req.database}.csv"
        
        # New data
        question = message.user_input
        answer = message.generated_query
        raw_summary = summarization.generate(message.generated_query)

        if raw_summary:
            raw_summary = re.sub(r"^```json|^```|```$", "", raw_summary.strip(), flags=re.MULTILINE).strip()

            try:
                if isinstance(raw_summary, str):
                    parsed = orjson.loads(raw_summary)
                else:
                    parsed = raw_summary

                summary = parsed.get("summary", "").strip()

            except (orjson.JSONDecodeError, AttributeError, TypeError) as e:
                summary = raw_summary
                print(f"Warning: Failed to parse summary JSON: {e}")

            # Add data
            df = pd.read_csv(dataset_path)
            new_row = {
                "Question": question,
                "Answer": answer,
                "Summary": summary
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

            # Save
            df.to_csv(dataset_path, index=False)

    return {"detail": f"Feedback '{req.feedback}' saved successfully"}
