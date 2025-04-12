from datetime import UTC, datetime

from flask_login import UserMixin
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from werkzeug.security import check_password_hash, generate_password_hash

from src.database import BaseModel, db


class User(UserMixin, BaseModel):
    """User model for authentication and session management."""

    __tablename__ = "users"
    # TODO поменять на mapped coloumn
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    blocked_at = Column(DateTime(timezone=True))
    blocked_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    chats = db.relationship("ChatMember", back_populates="user", cascade="all, delete-orphan")
    messages = db.relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")

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
