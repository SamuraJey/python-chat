from datetime import UTC, datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from src.database import db


class User(UserMixin, db.Model):
    """User model for authentication and session management."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_blocked = db.Column(db.Boolean, default=False)
    blocked_at = db.Column(db.DateTime(timezone=True))
    blocked_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    chats = db.relationship("ChatMember", back_populates="user")
    messages = db.relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password):
        """Hash and set the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verify the user password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def block(self, reason=None):
        """Block the user with an optional reason."""
        self.is_blocked = True
        self.blocked_at = datetime.now(UTC)
        self.blocked_reason = reason

    def unblock(self):
        """Unblock the user."""
        self.is_blocked = False
        self.blocked_at = None
        self.blocked_reason = None

    def __repr__(self):
        return f"<User {self.username}>"
