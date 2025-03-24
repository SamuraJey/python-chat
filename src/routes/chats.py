from flask import Blueprint, abort, current_app, render_template
from flask_login import current_user, login_required

from src.database.models.chat import Chat

bp = Blueprint("chats", __name__)
from src.database import db


@bp.route("/chat/<int:chat_id>")
def chat_page(chat_id):
    """Render chat page for specific chat ID"""
    logger = current_app.logger
    try:
        chat = Chat.query.get_or_404(chat_id)
        logger.debug(f"User {current_user.username} accessing chat {chat_id}")
        return render_template("chat_page.html", chat=chat)
    except Exception as e:
        logger.error(f"Error accessing chat {chat_id}: {e}\n type: {type(e)}")
        abort(500)


from flask import jsonify

from src.database.models.chat_message import ChatMessage
from src.database.models.user import User


# Add this new route
@bp.route("/api/messages/<int:chat_id>")
@login_required
def get_chat_messages(chat_id):
    """Get previous messages for a chat"""
    try:
        # Get messages and include username from User
        messages = db.session.query(ChatMessage, User.username).join(User, ChatMessage.user_id == User.id).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.sent_at).all()

        # Format messages for JSON response
        formatted_messages = [
            {
                "content": msg.ChatMessage.content,
                "username": msg.username,
                "timestamp": msg.ChatMessage.sent_at.isoformat(),
            }
            for msg in messages
        ]

        return jsonify({"messages": formatted_messages})
    except Exception as e:
        current_app.logger.error(f"Error retrieving messages for chat {chat_id}: {e}")
        return jsonify({"error": "Failed to retrieve messages"}), 500
