from datetime import UTC, datetime

from src.database import db


class ChatMember(db.Model):
    """Association model between users and chats."""

    __tablename__ = "chat_members"

    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id", ondelete="CASCADE"), primary_key=True)
    is_moderator = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    user = db.relationship("User", back_populates="chats")
    chat = db.relationship("Chat", back_populates="members")

    def __repr__(self):
        return f"<ChatMember user_id={self.user_id} chat_id={self.chat_id} is_moderator={self.is_moderator}>"
