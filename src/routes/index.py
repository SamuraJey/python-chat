from flask import Blueprint, current_app, redirect, render_template, url_for
from flask_login import current_user

from src.database.models.chat import Chat
from src.database.models.chat_member import ChatMember

bp = Blueprint("index", __name__)

# TODO из-за уникальной соли хешей каждого запуска бека. Пароли соханёные в бд становятся невалидыми.
# уже не так уверен так ли это


@bp.route("/")
def index():
    logger = current_app.logger
    logger.info(f"Index route accessed. Authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        user_chats = Chat.query.join(ChatMember).filter(ChatMember.user_id == current_user.id).all()

        logger.debug(f"User {current_user.username} chats is {user_chats}")
        return render_template("index.html", chats=user_chats)
    return redirect(url_for("auth.login"))
