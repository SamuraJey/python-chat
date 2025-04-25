from datetime import UTC, datetime
from typing import cast

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base, db
from src.database.models.chat_member import ChatMember
from src.database.models.chat_message import ChatMessage
from src.database.models.user import User


class Chat(Base):
    """Chat model for group and direct messaging."""

    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(127), nullable=False)  # TODO maybe nullable=False?
    is_group: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    members: Mapped[list["ChatMember"]] = relationship("ChatMember", back_populates="chat", cascade="all, delete-orphan")
    messages: Mapped[list["ChatMessage"]] = relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")

    def add_member(self, user: User, is_moderator=False) -> ChatMember:
        """Add a user to this chat."""
        member = ChatMember(user_id=user.id, chat_id=self.id, is_moderator=is_moderator)  # noqa
        db.session.add(member)
        db.session.commit()
        return member

    def remove_member(self, user: User) -> None:
        """Remove a user from this chat."""
        member = db.session.query(ChatMember).filter_by(user_id=user.id, chat_id=self.id).first()
        if member:
            db.session.delete(member)
            db.session.commit()

    def ban_member(self, user: User, reason=None) -> None:
        """Ban a user from this chat."""
        member = db.session.query(ChatMember).filter_by(user_id=user.id, chat_id=self.id).first()
        if member:
            member.ban(reason)
            db.session.commit()
            return True
        return False

    def unban_member(self, user: User) -> None:
        """Unban a user from this chat."""
        member = db.session.query(ChatMember).filter_by(user_id=user.id, chat_id=self.id).first()
        if member:
            member.unban()
            db.session.commit()
            return True
        return False

    def is_member(self, user: User) -> bool:
        """Check if a user is a member of this chat."""
        # надо переписать на новый стиль, без легаси query
        member = db.session.query(ChatMember).filter_by(user_id=user.id, chat_id=self.id).first()
        return member is not None and not member.is_banned

    def is_banned(self, user: User) -> bool:
        """Check if a user is banned from this chat."""
        member = db.session.query(ChatMember).filter_by(user_id=user.id, chat_id=self.id).first()
        return member is not None and member.is_banned

    def get_members(self) -> list[User]:
        """Get all users in this chat."""
        return cast(list[User], [member.user for member in self.members if not member.is_banned])

    def get_banned_members(self) -> list[tuple[User, datetime, str]]:
        """Get all banned users in this chat with ban details."""
        banned_members = []
        for member in self.members:
            if member.is_banned:
                banned_members.append((member.user, member.banned_at, member.banned_reason))
        return banned_members

    def get_moderators(self) -> list[User]:
        """Get all moderators in this chat."""
        return cast(list[User], [member.user for member in self.members if member.is_moderator])

    def __repr__(self) -> str:
        return f"<Chat {self.name} ({'group' if self.is_group else 'direct'})>"
