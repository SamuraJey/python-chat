from flask import Blueprint, current_app, render_template
from flask_login import current_user, login_required
from sqlalchemy import func, select

from src.database import db
from src.database.models.chat_member import ChatMember
from src.database.models.chat_message import ChatMessage

bp = Blueprint("profile", __name__)


# TODO test for profile route
@bp.route("/profile")
@login_required
def profile():
    """Личный кабинет пользователя"""
    # Получаем статистику пользователя
    chats_count_stmt = select(func.count(ChatMember.user_id)).filter(ChatMember.user_id == current_user.id)

    # chats_count_stmt = select(ChatMember).filter(ChatMember.user_id == current_user.id)
    messages_count_stmt = select(func.count(ChatMessage.user_id)).filter(ChatMessage.user_id == current_user.id)
    # messages_count_stmt = select(ChatMessage).filter(ChatMessage.user_id == current_user.id)
    current_app.logger.debug(f"Query for chats count: {chats_count_stmt}")
    current_app.logger.debug(f"Query for messages count: {messages_count_stmt}")

    user_stats = {
        "chats_count": db.session.execute(chats_count_stmt).scalar_one(),
        "messages_count": db.session.execute(messages_count_stmt).scalar_one(),
    }
    return render_template("profile.html", user=current_user, stats=user_stats)
