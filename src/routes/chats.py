from werkzeug.exceptions import HTTPException
from flask import Blueprint, abort, current_app, jsonify, render_template
from flask_login import current_user, login_required

from src.database import db
from src.database.models.chat import Chat
from src.database.models.chat_message import ChatMessage
from src.database.models.user import User

bp = Blueprint("chats", __name__)


@bp.route("/chat/<int:chat_id>")
@login_required
def chat_page(chat_id):
    """Render chat page for specific chat ID"""
    logger = current_app.logger
    try:
        chat = Chat.query.get_or_404(chat_id)
        logger.debug(f"User {current_user.username} accessing chat {chat_id}")
        return render_template("chat_page.html", chat=chat)
    except HTTPException as e:
        logger.error(f"HTTP error accessing chat {chat_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error accessing chat {chat_id}: {e}\n type: {type(e)}")
        abort(500)


@bp.route("/api/messages/<int:chat_id>")
@login_required
def get_chat_messages(chat_id):
    """Get previous messages for a chat"""
    try:
        chat = Chat.query.get_or_404(chat_id)
        # Используем left join чтобы включить сообщения удаленных пользователей
        messages = db.session.query(ChatMessage, User.username).outerjoin(User, ChatMessage.user_id == User.id).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.sent_at).all()
        # Format messages for JSON response
        formatted_messages = [
            {
                "content": msg.ChatMessage.content,
                "username": msg.username if msg.username else "[Deleted User]",
                "timestamp": msg.ChatMessage.sent_at.isoformat(),
            }
            for msg in messages
        ]

        return jsonify({"messages": formatted_messages})
    except HTTPException as e:
        current_app.logger.error(f"HTTP error retrieving messages for chat {chat_id}: {e}")
        raise
    except Exception as e:
        current_app.logger.error(f"Error retrieving messages for chat {chat_id}: {e}")
        abort(404)
        # return jsonify({"error": "Failed to retrieve messages"})
