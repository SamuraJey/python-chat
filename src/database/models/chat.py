from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from src.database import BaseModel, db
from src.database.models.chat_member import ChatMember
from src.database.models.user import User


class Chat(BaseModel):
    """Chat model for group and direct messaging."""

    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    name = Column(String(length=127))
    is_group = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    members = db.relationship("ChatMember", back_populates="chat", cascade="all, delete-orphan")
    messages = db.relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")

    def add_member(self, user: User, is_moderator=False) -> ChatMember:
        """Add a user to this chat."""
        member = ChatMember(user_id=user.id, chat_id=self.id, is_moderator=is_moderator)
        db.session.add(member)
        return member

    def remove_member(self, user: User) -> None:
        """Remove a user from this chat."""
        member = ChatMember.query.filter_by(user_id=user.id, chat_id=self.id).first()
        if member:
            db.session.delete(member)

    def is_member(self, user: User) -> bool:
        """Check if a user is a member of this chat."""
        return ChatMember.query.filter_by(user_id=user.id, chat_id=self.id).first() is not None

    def get_members(self) -> list:
        """Get all users in this chat."""
        return [member.user for member in self.members]

    def get_moderators(self) -> list:
        """Get all moderators in this chat."""
        return [member.user for member in self.members if member.is_moderator]

    def __repr__(self) -> str:
        return f"<Chat {self.name} ({'group' if self.is_group else 'direct'})>"
