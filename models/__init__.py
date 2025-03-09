# Create the db instance to be imported by other modules
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
from typing import TYPE_CHECKING

# Type handling for mypy
if TYPE_CHECKING:
    from flask_sqlalchemy.model import Model

    BaseModel = Model
else:
    BaseModel = db.Model

from .chat import Chat
from .chat_member import ChatMember
from .user import User

__all__ = ["db", "User", "Chat", "ChatMember"]
