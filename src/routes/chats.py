from flask import Blueprint, abort, current_app, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import select
from werkzeug.exceptions import HTTPException

from src.database import db
from src.database.models.chat import Chat
from src.database.models.chat_member import ChatMember
from src.database.models.chat_message import ChatMessage
from src.database.models.user import User

bp = Blueprint("chats", __name__)


@bp.route("/chat/<int:chat_id>")
@login_required
def chat_page(chat_id):
    """Render chat page for specific chat ID"""
    logger = current_app.logger
    try:
        chat = db.get_or_404(Chat, chat_id)

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
        chat = db.get_or_404(Chat, chat_id)
        # Используем left join чтобы включить сообщения удаленных пользователей
        stmt = select(ChatMessage, User.username).outerjoin(User, ChatMessage.user_id == User.id).filter(ChatMessage.chat_id == chat_id).order_by(ChatMessage.sent_at)
        messages = db.session.execute(stmt).all()
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


@bp.route("/api/search-users")
@login_required
def search_users():
    """Поиск пользователей по имени"""
    try:
        query = request.args.get("query", "")
        if not query or len(query) < 2:
            return jsonify({"users": []})

        # Поиск пользователей по имени (исключая текущего пользователя)
        stmt = select(User).filter(User.username.ilike(f"%{query}%"), User.id != current_user.id).limit(10)
        users = db.session.execute(stmt).scalars().all()

        return jsonify({"users": [{"id": user.id, "username": user.username} for user in users]})
    except Exception as e:
        current_app.logger.error(f"Error searching users: {e}")
        return jsonify({"error": "Failed to search users"}), 500


@bp.route("/api/chats/create", methods=["POST"])
@login_required
def create_chat():
    """Создание нового чата"""
    try:
        data = request.json
        chat_name = data.get("name")
        is_group = data.get("is_group", False)
        user_ids = data.get("user_ids", [])

        # Проверка данных
        if not chat_name:
            return jsonify({"error": "Chat name is required"}), 400

        if not is_group and len(user_ids) != 1:
            return jsonify({"error": "Private chat requires exactly one user"}), 400

        # Создаем новый чат
        new_chat = Chat(name=chat_name, is_group=is_group)
        db.session.add(new_chat)
        db.session.flush()  # Чтобы получить id чата

        # Добавляем текущего пользователя как модератора
        current_user_member = ChatMember(chat_id=new_chat.id, user_id=current_user.id, is_moderator=True)
        db.session.add(current_user_member)

        # Добавляем остальных участников
        for user_id in user_ids:
            # Проверяем, что пользователь существует
            user = db.session.get(User, user_id)
            if user:
                member = ChatMember(chat_id=new_chat.id, user_id=user_id, is_moderator=False)
                db.session.add(member)

        db.session.commit()

        return jsonify({"success": True, "chat": {"id": new_chat.id, "name": new_chat.name, "is_group": new_chat.is_group}})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating chat: {e}")
        return jsonify({"error": "Failed to create chat"}), 500


@bp.route("/api/chats")
@login_required
def get_user_chats():
    """Получить список чатов текущего пользователя"""
    try:
        # Получаем чаты, в которых пользователь является участником
        stmt = select(Chat).join(ChatMember).filter(ChatMember.user_id == current_user.id)
        chats = db.session.execute(stmt).scalars().all()

        return jsonify({"chats": [{"id": chat.id, "name": chat.name, "is_group": chat.is_group} for chat in chats]})
    except Exception as e:
        current_app.logger.error(f"Error retrieving user chats: {e}")

        return jsonify({"error": "Failed to retrieve chats"}), 500


@bp.route("/kek")
def kek():
    return render_template("kek.html")
