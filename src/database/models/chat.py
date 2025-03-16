from datetime import UTC, datetime

from src.database import db
from src.database.models.chat_member import ChatMember


class Chat(db.Model):
    """Chat model for group and direct messaging."""

    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(127))
    is_group = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # Relationships
    members = db.relationship("ChatMember", back_populates="chat", cascade="all, delete-orphan")
    messages = db.relationship("ChatMessage", back_populates="chat", cascade="all, delete-orphan")

    def add_member(self, user, is_moderator=False):
        """Add a user to this chat."""
        member = ChatMember(user=user, chat=self, is_moderator=is_moderator)
        db.session.add(member)
        return member

    def remove_member(self, user):
        """Remove a user from this chat."""
        member = ChatMember.query.filter_by(user_id=user.id, chat_id=self.id).first()
        if member:
            db.session.delete(member)

    def is_member(self, user):
        """Check if a user is a member of this chat."""
        return ChatMember.query.filter_by(user_id=user.id, chat_id=self.id).first() is not None

    def get_members(self):
        """Get all users in this chat."""
        return [member.user for member in self.members]

    def get_moderators(self):
        """Get all moderators in this chat."""
        return [member.user for member in self.members if member.is_moderator]

    def __repr__(self):
        return f"<Chat {self.name} ({'group' if self.is_group else 'direct'})>"
