import time
from typing import Any

from flask import current_app, request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from src.database import db
from src.database.models.chat_message import ChatMessage

# Global dictionary to store connected users and their information
users: dict[str, dict[str, Any]] = {}


def init_socketio(socketio):
    """Initialize Socket.IO event handlers"""
    logger = current_app.logger

    @socketio.on("connect")
    def handle_connect():
        """Handle client connection"""
        current_app.logger.debug(f"Socket connection attempt. Authenticated: {current_user.is_authenticated}")
        if not current_user.is_authenticated:
            current_app.logger.warning("Unauthenticated socket connection attempt rejected")
            return False

        username = current_user.username
        users[request.sid] = {"username": username, "user_id": current_user.id}

        current_app.logger.info(f"User {username} connected with socket ID {request.sid}")
        emit("user_joined", {"username": username}, broadcast=True)
        emit("set_username", {"username": username})

        # Send current online users count
        emit("online_users", {"users": list(set(user["username"] for user in users.values()))}, broadcast=True)

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection"""
        user = users.pop(request.sid, None)
        if user:
            current_app.logger.info(f"User {user['username']} disconnected from socket ID {request.sid}")
            emit("user_left", {"username": user["username"]}, broadcast=True)
            # Update online users count
            emit("online_users", {"users": list(set(user["username"] for user in users.values()))}, broadcast=True)

    @socketio.on("send_message")
    def handle_message(data):
        """Handle incoming chat message"""
        user = users.get(request.sid)
        if not user:
            current_app.logger.warning(f"Message from unknown socket ID {request.sid}")
            return

        chat_id = data.get("chat_id")
        message = data.get("message", "")

        current_app.logger.debug(f"Message in chat {chat_id} from {user['username']}: {message[:20]}...")

        try:
            # You can save the message to database here if needed
            message_obj = ChatMessage(
                user_id=user["user_id"],
                chat_id=chat_id,
                content=message,
            )
            db.session.add(message_obj)
            db.session.commit()

            emit(
                "receive_message",
                {
                    "username": user["username"],
                    "user_id": user["user_id"],
                    "message": message,
                    "timestamp": int(time.time() * 1000),
                },
                room=str(chat_id),  # Convert to string if it's an integer
                broadcast=True,
            )
        except Exception as e:
            current_app.logger.error(f"Error sending message: {e}")
            emit("error", {"message": "Failed to send message"})

    @socketio.on("join")
    def handle_join(data):
        """Handle user joining a specific chat room"""
        user = users.get(request.sid)
        if not user:
            return

        chat_id = data.get("chat_id")
        if not chat_id:
            current_app.logger.warning(f"Join attempt without chat_id from {user['username']}")
            return

        # Store chat ID in user data
        users[request.sid]["chat_id"] = chat_id

        # Join the room
        join_room(chat_id)

        current_app.logger.info(f"User {user['username']} joined chat {chat_id}")

        # Notify others in the room
        emit(
            "user_joined_chat",
            {"username": user["username"], "chat_id": chat_id},
            room=chat_id,
            broadcast=True,
            include_self=False,
        )

    @socketio.on("leave")
    def handle_leave(data):
        """Handle user leaving a specific chat room"""
        user = users.get(request.sid)
        if not user:
            return

        chat_id = data.get("chat_id") or user.get("chat_id")
        if not chat_id:
            return

        # Leave the room
        leave_room(chat_id)

        # Remove chat_id from user data
        if "chat_id" in users[request.sid]:
            del users[request.sid]["chat_id"]

        current_app.logger.info(f"User {user['username']} left chat {chat_id}")

        # Notify others in the room
        emit("user_left_chat", {"username": user["username"], "chat_id": chat_id}, room=chat_id, broadcast=True)

    @socketio.on("typing")
    def handle_typing(data):
        """Handle typing status updates"""
        user = users.get(request.sid)
        if not user:
            return

        chat_id = user.get("chat_id")
        is_typing = data.get("isTyping", False)

        if chat_id:
            emit(
                "typing",
                {"username": user["username"], "isTyping": is_typing},
                room=chat_id,
                broadcast=True,
                include_self=False,
            )

    @socketio.on("update_username")
    def handle_update_username(data):
        """Handle username update request"""
        if request.sid not in users:
            emit("username_error", {"error": "User not found"})
            return

        old_username = users[request.sid]["username"]
        new_username = data.get("username")

        if not new_username or len(new_username) < 3:
            emit("username_error", {"error": "Username must be at least 3 characters"})
            return

        current_app.logger.info(f"Username update requested: {old_username} → {new_username}")

        # Update username in all rooms this user is in
        users[request.sid]["username"] = new_username

        current_app.logger.info(f"Username updated successfully: {old_username} → {new_username}")

        # Notify all users about the username change
        emit("username_updated", {"old_username": old_username, "new_username": new_username}, broadcast=True)

    @socketio.on("get_online_users")
    def handle_get_online_users():
        """Send list of online users"""
        unique_users = list(set(user["username"] for user in users.values()))
        emit("online_users", {"users": unique_users})

    return socketio
