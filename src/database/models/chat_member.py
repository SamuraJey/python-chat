from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from src.database import BaseModel, db


class ChatMember(BaseModel):
    """Association model between users and chats."""

    __tablename__ = "chat_members"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user = db.relationship("User", back_populates="chats")
    chat = db.relationship("Chat", back_populates="members")

    def __repr__(self) -> str:
        return f"<ChatMember user_id={self.user_id} chat_id={self.chat_id} is_moderator={self.is_moderator}>"
