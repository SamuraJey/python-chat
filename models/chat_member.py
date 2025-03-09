from datetime import datetime, timezone
from . import BaseModel, db

class ChatMember(BaseModel):
    __tablename__ = "chat_members"

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chats.id'), primary_key=True)
    is_moderator = db.Column(db.Boolean, default=False)
    blocked = db.Column(db.Boolean, default=False)
    joined_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ChatMember user_id={self.user_id} chat_id={self.chat_id}>"
