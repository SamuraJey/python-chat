import datetime
import functools

from flask import Blueprint, abort, jsonify, render_template
from flask_login import current_user, login_required
from sqlalchemy import func, text

from python_chat.database import db
from python_chat.database.models.chat import Chat
from python_chat.database.models.chat_message import ChatMessage
from python_chat.database.models.user import User

bp = Blueprint("admin", __name__)


def admin_required(func):
    """Decorator to ensure the user is an admin."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)  # Forbidden
        return func(*args, **kwargs)

    return wrapper


@bp.route("/admin/dashboard")
@login_required
@admin_required
def admin_dashboard():
    """Админ-панель с аналитикой (только для админов)"""
    return render_template("dashboard.html", user=current_user)


@bp.route("/api/analytics/overview")
@login_required
@admin_required
def get_analytics_overview():
    """Получить обзорные аналитические данные на основе существующих таблиц"""

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
@admin_required
def get_chat_activity():
    """Получить данные об активности чатов"""
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
@admin_required
def get_user_activity():
    """Получить данные о пользовательской активности"""

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
