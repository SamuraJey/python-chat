import time
from typing import Any

from flask import current_app, request
from flask_login import current_user
from flask_socketio import emit, join_room, leave_room

from python_chat.database import db
from python_chat.database.models.chat_message import ChatMessage

# Global dictionary to store connected users and their information
users: dict[str, dict[str, Any]] = {}


def init_socketio(socketio):
    """Initialize Socket.IO event handlers"""

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
        emit("online_users", {"users": list({user["username"] for user in users.values()})}, broadcast=True)

    @socketio.on("disconnect")
    def handle_disconnect():
        """Handle client disconnection"""
        user = users.pop(request.sid, None)
        if user:
            current_app.logger.info(f"User {user['username']} disconnected from socket ID {request.sid}")
            emit("user_left", {"username": user["username"]}, broadcast=True)
            # Update online users count
            emit("online_users", {"users": list({user["username"] for user in users.values()})}, broadcast=True)

    @socketio.on("send_message")
    def handle_message(data):
        """Handle incoming chat message"""
        user = users.get(request.sid)
        if not user:
            current_app.logger.warning(f"Message from unknown socket ID {request.sid}")
            return

        chat_id = data.get("chat_id")
        if not chat_id:
            current_app.logger.error(f"No chat_id provided for message from {user['username']}")
            emit("error", {"message": "No chat room selected"})
            return

        message = data.get("message", "")

        # For debug - log what room the user is in
        user_room = users[request.sid].get("chat_id")
        current_app.logger.debug(f"Message in chat {chat_id} from {user['username']} (currently in room {user_room}): {message[:20]}...")

        # Проверка, не забанен ли пользователь в чате
        try:
            from sqlalchemy import select

            from python_chat.database.models.chat_member import ChatMember

            # Проверяем, забанен ли пользователь
            banned_check = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == user["user_id"], ChatMember.is_banned)).scalar_one_or_none()

            if banned_check:
                current_app.logger.warning(f"Banned user {user['username']} attempted to send message to chat {chat_id}")
                emit("error", {"message": "You are banned from this chat", "chat_id": chat_id})
                return
        except Exception as e:
            current_app.logger.error(f"Error checking ban status: {e}")

        try:
            # Save the message to database
            message_obj = ChatMessage(
                user_id=user["user_id"],
                chat_id=chat_id,
                content=message,
            )
            db.session.add(message_obj)
            db.session.commit()

            # Convert chat_id to string for room name consistency
            room_name = str(chat_id)

            # Broadcast to the right room
            current_app.logger.debug(f"Emitting message to room {room_name}")
            emit(
                "receive_message",
                {
                    "username": user["username"],
                    "user_id": user["user_id"],
                    "message": message,
                    "timestamp": int(time.time() * 1000),
                    "message_id": message_obj.id,  # Add message ID to help with deduplication
                    "chat_id": chat_id,  # Include chat_id to filter messages by chat
                },
                room=room_name,
                broadcast=True,
            )
            current_app.logger.debug(f"Message broadcast completed to room {room_name}")
        except Exception as e:
            current_app.logger.error(f"Error sending message: {e}")
            db.session.rollback()
            emit("error", {"message": "Failed to send message"})

    @socketio.on("join")
    def handle_join(data):
        """Handle user joining a specific chat room"""
        user = users.get(request.sid)
        if not user:
            current_app.logger.warning(f"Join attempt from unknown socket ID {request.sid}")
            return

        chat_id = data.get("chat_id")
        if not chat_id:
            current_app.logger.warning(f"Join attempt without chat_id from {user['username']}")
            return

        # Check if user is banned from this chat
        try:
            from sqlalchemy import select

            from python_chat.database.models.chat_member import ChatMember

            # Check if the user exists in the chat member list and is banned
            banned_check = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == user["user_id"], ChatMember.is_banned)).scalar_one_or_none()

            if banned_check:
                current_app.logger.warning(f"Banned user {user['username']} attempted to join chat {chat_id}")
                emit("error", {"message": "You are banned from this chat", "chat_id": chat_id})
                return

            # Check if the user is a member of this chat
            member_check = db.session.execute(select(ChatMember).filter(ChatMember.chat_id == chat_id, ChatMember.user_id == user["user_id"])).scalar_one_or_none()

            if not member_check:
                current_app.logger.warning(f"Non-member {user['username']} attempted to join chat {chat_id}")
                emit("error", {"message": "You are not a member of this chat", "chat_id": chat_id})
                return
        except Exception as e:
            current_app.logger.error(f"Error checking ban status: {e}")

        # Store chat ID in user data
        users[request.sid]["chat_id"] = chat_id

        # Convert chat_id to string for room name
        room_name = str(chat_id)

        # Join the room
        join_room(room_name)

        current_app.logger.info(f"User {user['username']} joined chat {chat_id}, room: {room_name}")

        # Confirm joining to the client
        emit("joined_chat", {"chat_id": chat_id, "status": "success"})

        # Notify others in the room
        emit("user_joined_chat", {"username": user["username"], "chat_id": chat_id}, room=room_name, include_self=False)

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
        unique_users = list({user["username"] for user in users.values()})
        emit("online_users", {"users": unique_users})

    return socketio
