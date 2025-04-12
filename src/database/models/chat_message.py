from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text

from src.database import BaseModel, db


class ChatMessage(BaseModel):
    """Message model for chat messages."""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    chat = db.relationship("Chat", back_populates="messages")
    user = db.relationship("User", back_populates="messages")

    def __repr__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"<ChatMessage id={self.id} chat={self.chat_id} user={self.user_id} content='{preview}'>"
