from flask import Blueprint, jsonify
from flask_login import current_user, login_required
from sqlalchemy import func, select

from python_chat.database import db
from python_chat.database.models.chat_member import ChatMember
from python_chat.database.models.chat_message import ChatMessage

bp = Blueprint("api_profile", __name__, url_prefix="/api/user")


@bp.route("/stats", methods=["GET"])
@login_required
def get_user_stats():
    """Get user statistics for the profile page"""
    try:
        # Get user statistics
        chats_count_stmt = select(func.count(ChatMember.user_id)).filter(ChatMember.user_id == current_user.id)
        messages_count_stmt = select(func.count(ChatMessage.user_id)).filter(ChatMessage.user_id == current_user.id)

        user_stats = {
            "chats_count": db.session.execute(chats_count_stmt).scalar_one(),
            "messages_count": db.session.execute(messages_count_stmt).scalar_one(),
        }

        # Return data for the React frontend
        return jsonify({"success": True, "user": {"username": current_user.username, "is_admin": current_user.is_admin}, "stats": user_stats})
    except Exception as e:
        # Log the error
        from flask import current_app

        current_app.logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({"success": False, "error": "Failed to retrieve user statistics"}), 500
