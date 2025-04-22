import enum
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    chats = relationship("ChatHistory", back_populates="user")


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True)
    title = Column(String(100))
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())

    user = relationship("User", back_populates="chats")
    messages = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chat_histories.id", ondelete="CASCADE"), nullable=False)
    user_input = Column(Text)
    agent_response = Column(Text)
    timestamp = Column(DateTime, server_default=func.now())

    chat = relationship("ChatHistory", back_populates="messages")
    feedback = relationship("ChatFeedback", back_populates="message", cascade="all, delete-orphan", uselist=False)


class FeedbackType(str, enum.Enum):
    positive = "positive"
    negative = "negative"


class ChatFeedback(Base):
    __tablename__ = "chat_feedback"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(Integer, ForeignKey("chat_messages.id", ondelete="CASCADE"), nullable=False)
    feedback = Column(Enum(FeedbackType), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    message = relationship("ChatMessage", back_populates="feedback")
