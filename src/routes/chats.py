import datetime

from flask import Blueprint, abort, current_app, jsonify, render_template, request
from flask_login import current_user, login_required
from sqlalchemy import func, text
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


@bp.route("/api/search-users")
@login_required
def search_users():
    """Поиск пользователей по имени"""
    try:
        query = request.args.get("query", "")
        if not query or len(query) < 2:
            return jsonify({"users": []})

        # Поиск пользователей по имени (исключая текущего пользователя)
        users = db.session.query(User).filter(User.username.ilike(f"%{query}%"), User.id != current_user.id).limit(10).all()

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
            user = db.session.query(User).get(user_id)
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
        chats = db.session.query(Chat).join(ChatMember).filter(ChatMember.user_id == current_user.id).all()

        return jsonify({"chats": [{"id": chat.id, "name": chat.name, "is_group": chat.is_group} for chat in chats]})
    except Exception as e:
        current_app.logger.error(f"Error retrieving user chats: {e}")
        return jsonify({"error": "Failed to retrieve chats"}), 500


@bp.route("/profile")
@login_required
def profile():
    """Личный кабинет пользователя"""
    # Получаем статистику пользователя
    user_stats = {
        "chats_count": db.session.query(ChatMember).filter(ChatMember.user_id == current_user.id).count(),
        "messages_count": db.session.query(ChatMessage).filter(ChatMessage.user_id == current_user.id).count(),
    }
    return render_template("profile.html", user=current_user, stats=user_stats)


@bp.route("/admin/dashboard")
@login_required
def admin_dashboard():
    """Админ-панель с аналитикой (только для админов)"""
    if not current_user.is_admin:
        abort(403)  # Запрет доступа

    return render_template("dashboard.html", user=current_user)


@bp.route("/api/analytics/overview")
@login_required
def get_analytics_overview():
    """Получить обзорные аналитические данные на основе существующих таблиц"""
    if not current_user.is_admin:
        abort(403)

    # Запросы к существующим таблицам
    total_users = db.session.query(User).count()
    total_chats = db.session.query(Chat).count()
    total_messages = db.session.query(ChatMessage).count()

    # Пользователи с сообщениями за последние 24 часа
    yesterday = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
    active_users = db.session.query(ChatMessage.user_id).distinct().filter(ChatMessage.sent_at >= yesterday).count()

    # Сообщения за сегодня
    today = datetime.datetime.now(datetime.UTC).date()
    messages_today = db.session.query(ChatMessage).filter(func.date(ChatMessage.sent_at) == today).count()

    data = {"total_users": total_users, "total_chats": total_chats, "total_messages": total_messages, "active_users": active_users, "messages_today": messages_today}

    return jsonify(data)


@bp.route("/api/analytics/chat-activity")
@login_required
def get_chat_activity():
    """Получить данные об активности чатов"""
    if not current_user.is_admin:
        abort(403)

    # Находим самые активные чаты (по количеству сообщений)
    chat_activity = (
        db.session.query(Chat.name, func.count(ChatMessage.id).label("message_count"))
        .join(ChatMessage, Chat.id == ChatMessage.chat_id)
        .group_by(Chat.id)
        .order_by(text("message_count DESC"))
        .limit(5)
        .all()
    )

    # Преобразуем в формат для графика
    chart_data = {"labels": [chat.name for chat in chat_activity], "datasets": [{"label": "Количество сообщений", "data": [chat.message_count for chat in chat_activity]}]}

    return jsonify(chart_data)


@bp.route("/api/analytics/user-activity")
@login_required
def get_user_activity():
    """Получить данные о пользовательской активности"""
    if not current_user.is_admin:
        abort(403)

    # Данные по активности пользователей за последние 7 дней
    days = 7
    today = datetime.datetime.now(datetime.UTC).date()

    # Подготавливаем список дат (последние 7 дней)
    date_labels = [(today - datetime.timedelta(days=i)) for i in range(days - 1, -1, -1)]
    date_labels_str = [d.strftime("%d.%m") for d in date_labels]

    # Запрос количества сообщений по дням
    message_counts = []
    for date in date_labels:
        count = db.session.query(func.count(ChatMessage.id)).filter(func.date(ChatMessage.sent_at) == date).scalar() or 0
        message_counts.append(count)

    data = {"labels": date_labels_str, "datasets": [{"label": "Сообщения", "data": message_counts}]}

    return jsonify(data)
