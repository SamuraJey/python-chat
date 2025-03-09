from datetime import UTC, datetime

from src.database import db


class ChatMessage(db.Model):
    """Message model for chat messages."""

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sent_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    chat = db.relationship("Chat", back_populates="messages")
    user = db.relationship("User", back_populates="messages")

    def __repr__(self):
        preview = self.content[:20] + "..." if len(self.content) > 20 else self.content
        return f"<ChatMessage id={self.id} chat={self.chat_id} user={self.user_id} content='{preview}'>"
