from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func, select
from werkzeug.security import check_password_hash, generate_password_hash

from python_chat.database import db
from python_chat.database.models.chat_member import ChatMember
from python_chat.database.models.chat_message import ChatMessage
from python_chat.database.models.user import User

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


@bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    """Change the user's password"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        current_password = data.get("current_password")
        new_password = data.get("new_password")
        confirm_password = data.get("confirm_password")

        # Validate input
        if not current_password or not new_password or not confirm_password:
            return jsonify({"success": False, "error": "All fields are required"}), 400

        if new_password != confirm_password:
            return jsonify({"success": False, "error": "New passwords don't match"}), 400

        if len(new_password) < 8:
            return jsonify({"success": False, "error": "Password must be at least 8 characters"}), 400

        # Check if the current password is correct
        user = User.query.get(current_user.id)
        if not check_password_hash(user.password_hash, current_password):
            return jsonify({"success": False, "error": "Current password is incorrect"}), 401

        # Update the password
        user.password_hash = generate_password_hash(new_password)
        db.session.commit()

        return jsonify({"success": True, "message": "Password changed successfully"})
    except Exception as e:
        from flask import current_app

        current_app.logger.error(f"Error changing password: {str(e)}")
        return jsonify({"success": False, "error": "Failed to change password"}), 500
