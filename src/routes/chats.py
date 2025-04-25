from typing import cast

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


@bp.route("/api/chat/<int:chat_id>/members")
@login_required
def get_chat_members(chat_id):
    """Get all members of a chat"""
    try:
        # Проверяем, что чат существует
        chat = db.get_or_404(Chat, chat_id)

        # Проверяем, что пользователь является участником этого чата
        member_check = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == current_user.id)).scalar_one_or_none()

        if not member_check:
            return jsonify({"error": "You are not a member of this chat"}), 403

        # Получаем всех участников чата с информацией о пользователе
        # Исключаем забаненных пользователей из списка
        stmt = select(User.id, User.username, ChatMember.is_moderator).join(ChatMember, User.id == ChatMember.user_id).filter(ChatMember.chat_id == chat_id, ChatMember.is_banned == False)

        members = db.session.execute(stmt).all()

        formatted_members = [{"id": member.id, "username": member.username, "is_moderator": member.is_moderator} for member in members]

        return jsonify({"members": formatted_members})
    except HTTPException as e:
        current_app.logger.error(f"HTTP error retrieving members for chat {chat_id}: {e}")
        raise
    except Exception as e:
        current_app.logger.error(f"Error retrieving chat members: {e}")
        return jsonify({"error": "Failed to retrieve chat members"}), 500


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
        data = cast(dict, request.get_json())
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


@bp.route("/kek")
def kek():  # pragma: no cover
    return render_template("kek.html")


@bp.route("/api/chat/<int:chat_id>/ban", methods=["POST"])
@login_required
def ban_chat_user(chat_id):
    """Ban a user from a chat (moderator only)"""
    try:
        chat = db.get_or_404(Chat, chat_id)

        # Check if current user is a moderator
        moderator_check = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == current_user.id, ChatMember.is_moderator == True)).scalar_one_or_none()

        if not moderator_check:
            return jsonify({"error": "You are not a moderator of this chat"}), 403

        # Get user to ban
        data = request.get_json()
        user_id = data.get("user_id")
        reason = data.get("reason", "No reason provided")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Can't ban yourself
        if int(user_id) == current_user.id:
            return jsonify({"error": "You cannot ban yourself"}), 400

        # Check if the user to ban is also a moderator
        target_user = db.session.get(User, user_id)
        if not target_user:
            return jsonify({"error": "User not found"}), 404

        target_member = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id)).scalar_one_or_none()

        if not target_member:
            return jsonify({"error": "User is not a member of this chat"}), 400

        if target_member.is_moderator:
            return jsonify({"error": "Cannot ban a moderator"}), 400

        # Ban the user
        chat.ban_member(target_user, reason)

        # Получаем socket ID пользователя, чтобы принудительно удалить его из комнаты
        from src.app import socketio
        from src.routes.events import users

        # Найдем все активные соединения этого пользователя
        user_socket_ids = [sid for sid, user_data in users.items() if user_data.get("user_id") == int(user_id)]

        # Отправляем уведомление о бане на все соединения пользователя
        for socket_id in user_socket_ids:
            # Отправляем уведомление о бане
            socketio.emit("banned_from_chat", {"chat_id": chat_id, "chat_name": chat.name}, room=socket_id)

            # Принудительно исключаем пользователя из комнаты чата
            room_name = str(chat_id)
            socketio.server.leave_room(socket_id, room_name)

            # Удалить чат из текущего чата пользователя
            if users.get(socket_id) and users[socket_id].get("chat_id") == chat_id:
                users[socket_id].pop("chat_id", None)

        # Отправляем уведомление всем в чате о бане пользователя
        room_name = str(chat_id)
        socketio.emit("user_banned", {"username": target_user.username, "banned_by": current_user.username}, room=room_name)

        return jsonify({"success": True, "message": f"User {target_user.username} has been banned from the chat"})
    except Exception as e:
        current_app.logger.error(f"Error banning user from chat: {e}")
        return jsonify({"error": "Failed to ban user"}), 500


@bp.route("/api/chat/<int:chat_id>/unban", methods=["POST"])
@login_required
def unban_chat_user(chat_id):
    """Unban a user from a chat (moderator only)"""
    try:
        chat = db.get_or_404(Chat, chat_id)

        # Check if current user is a moderator
        moderator_check = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == current_user.id, ChatMember.is_moderator == True)).scalar_one_or_none()

        if not moderator_check:
            return jsonify({"error": "You are not a moderator of this chat"}), 403

        # Get user to unban
        data = request.get_json()
        user_id = data.get("user_id")

        if not user_id:
            return jsonify({"error": "User ID is required"}), 400

        # Check if user exists
        target_user = db.session.get(User, user_id)
        if not target_user:
            return jsonify({"error": "User not found"}), 404

        # Check if user is banned
        target_member = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == user_id, ChatMember.is_banned == True)).scalar_one_or_none()

        if not target_member:
            return jsonify({"error": "User is not banned from this chat"}), 400

        # Unban the user
        chat.unban_member(target_user)

        # Отправляем уведомление всем в чате о разбане пользователя
        from src.app import socketio

        room_name = str(chat_id)
        socketio.emit("user_unbanned", {"username": target_user.username, "unbanned_by": current_user.username}, room=room_name)

        return jsonify({"success": True, "message": f"User {target_user.username} has been unbanned from the chat"})
    except Exception as e:
        current_app.logger.error(f"Error unbanning user from chat: {e}")
        return jsonify({"error": "Failed to unban user"}), 500


@bp.route("/api/chat/<int:chat_id>/banned")
@login_required
def get_banned_users(chat_id):
    """Get list of banned users in a chat (moderator only)"""
    try:
        chat = db.get_or_404(Chat, chat_id)

        # Check if current user is a moderator
        moderator_check = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == current_user.id, ChatMember.is_moderator == True)).scalar_one_or_none()

        if not moderator_check:
            return jsonify({"error": "You are not a moderator of this chat"}), 403

        # Get banned users with ban details
        banned_members = db.session.execute(
            select(User.id, User.username, ChatMember.banned_at, ChatMember.banned_reason)
            .join(ChatMember, User.id == ChatMember.user_id)
            .filter(ChatMember.chat_id == chat_id, ChatMember.is_banned == True)
        ).all()

        formatted_banned = [
            {"id": member.id, "username": member.username, "banned_at": member.banned_at.isoformat() if member.banned_at else None, "reason": member.banned_reason} for member in banned_members
        ]

        return jsonify({"banned_users": formatted_banned})
    except Exception as e:
        current_app.logger.error(f"Error getting banned users: {e}")
        return jsonify({"error": "Failed to get banned users"}), 500
