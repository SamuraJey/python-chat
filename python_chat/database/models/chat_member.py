from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from python_chat.database import Base, db


class ChatMember(Base):
    """Association model between users and chats."""

    __tablename__ = "chat_members"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    is_moderator: Mapped[bool] = mapped_column(Boolean, default=False)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    banned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    banned_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = db.relationship("User", back_populates="chats")
    chat = db.relationship("Chat", back_populates="members")

    def ban(self, reason=None) -> None:
        """Ban a user from this chat."""
        self.is_banned = True
        self.banned_at = datetime.now(UTC)
        self.banned_reason = reason

    def unban(self) -> None:
        """Unban a user from this chat."""
        self.is_banned = False
        self.banned_at = None
        self.banned_reason = None

    def __repr__(self) -> str:
        return f"<ChatMember user_id={self.user_id} chat_id={self.chat_id} is_moderator={self.is_moderator} is_banned={self.is_banned}>"
