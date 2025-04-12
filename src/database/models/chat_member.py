from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer

from src.database import BaseModel, db


class ChatMember(BaseModel):
    """Association model between users and chats."""

    __tablename__ = "chat_members"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    is_moderator = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    user = db.relationship("User", back_populates="chats")
    chat = db.relationship("Chat", back_populates="members")

    def __repr__(self) -> str:
        return f"<ChatMember user_id={self.user_id} chat_id={self.chat_id} is_moderator={self.is_moderator}>"
