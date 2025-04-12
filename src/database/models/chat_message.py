from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.database import BaseModel, db


class ChatMessage(BaseModel):
    """Message model for chat messages."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False) 
    #TODO ПОдумать Changing the deletion behavior from SET NULL to CASCADE for the user_id foreign key may lead to unintentional deletion of chat messages if a user is removed. Confirm that this behavior is intended for preserving chat history.
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    chat = db.relationship("Chat", back_populates="messages")
    user = db.relationship("User", back_populates="messages")

    def __repr__(self) -> str:
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"<ChatMessage id={self.id} chat={self.chat_id} user={self.user_id} content='{preview}'>"
