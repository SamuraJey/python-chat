from datetime import UTC, datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from werkzeug.security import check_password_hash, generate_password_hash

from src.database import Base, db


class User(UserMixin, Base):
    """User model for authentication and session management."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    blocked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    chats = db.relationship("ChatMember", back_populates="user", cascade="all, delete-orphan")
    messages = db.relationship("ChatMessage", back_populates="user", passive_deletes=True)

    def set_password(self, password) -> None:
        """Hash and set the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password) -> bool:
        """Verify the user password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def block(self, reason=None) -> None:
        """Block the user with an optional reason."""
        self.is_blocked = True
        self.blocked_at = datetime.now(UTC)
        self.blocked_reason = reason

    def unblock(self) -> None:
        """Unblock the user."""
        self.is_blocked = False
        self.blocked_at = None
        self.blocked_reason = None

    def __repr__(self) -> str:
        return f"<User {self.username}>"
