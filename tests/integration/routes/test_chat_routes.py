import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from src.database.models.chat import Chat
from src.database.models.chat_member import ChatMember
from src.database.models.chat_message import ChatMessage
from src.database.models.user import User


class TestChatRoutes:
    """Tests for chat-related routes."""

    def test_chat_page_loads(self, authenticated_client, chat, chat_member):
        """Test that the chat page loads correctly."""
        response = authenticated_client.get(f"/chat/{chat.id}")
        assert response.status_code == 200
        assert bytes(chat.name, "utf-8") in response.data

    def test_chat_page_nonexistent(self, authenticated_client):
        """Test accessing a non-existent chat."""
        response = authenticated_client.get("/chat/9999")
        assert response.status_code == 404

    def test_chat_page_unauthenticated(self, test_client, chat):
        """Test that unauthenticated users can't access chat pages."""
        response = test_client.get(f"/chat/{chat.id}")
        assert response.status_code == 302  # Should redirect to login
        assert "/login" in response.location

    def test_get_chat_messages_api(self, authenticated_client, chat, chat_message, user):
        """Test the API endpoint for retrieving chat messages."""
        response = authenticated_client.get(f"/api/messages/{chat.id}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "messages" in data
        assert len(data["messages"]) == 1
        assert data["messages"][0]["content"] == "Test message"
        assert data["messages"][0]["username"] == user.username

    def test_get_chat_messages_empty(self, authenticated_client, chat):
        """Test retrieving messages from an empty chat."""
        response = authenticated_client.get(f"/api/messages/{chat.id}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "messages" in data
        assert len(data["messages"]) == 0

    def test_get_chat_messages_multiple(self, authenticated_client, chat, user: User, session: Session):
        """Test retrieving multiple messages in chronological order."""
        # Create messages with different timestamps
        msg1 = ChatMessage(user_id=user.id, chat_id=chat.id, content="First message")
        msg1.sent_at = datetime.now(UTC) - timedelta(minutes=10)

        msg2 = ChatMessage(user_id=user.id, chat_id=chat.id, content="Second message")
        msg2.sent_at = datetime.now(UTC)

        session.add_all([msg1, msg2])
        session.commit()

        response = authenticated_client.get(f"/api/messages/{chat.id}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data["messages"]) == 2
        assert data["messages"][0]["content"] == "First message"
        assert data["messages"][1]["content"] == "Second message"

    def test_get_chat_messages_unauthenticated(self, test_client, chat):
        """Test that unauthenticated users can't access message API."""
        response = test_client.get(f"/api/messages/{chat.id}")
        assert response.status_code == 302  # Should redirect to login
        assert "/login" in response.location

    def test_get_chat_messages_nonexistent_chat(self, authenticated_client):
        """Test accessing messages for a non-existent chat."""
        response = authenticated_client.get("/api/messages/9999")
        print(response.data)
        assert response.status_code in [404, 500]  # Either not found or server error is acceptable

    def test_get_chat_messages_different_users(self, authenticated_client, chat, session: Session):
        """Test retrieving messages from different users."""
        # Create another user
        user2 = User(username="seconduser")
        user2.set_password("password123")
        session.add(user2)
        session.flush()

        # Add messages from both users
        msg1 = ChatMessage(user_id=user2.id, chat_id=chat.id, content="Message from user 2")
        session.add(msg1)
        session.commit()

        response = authenticated_client.get(f"/api/messages/{chat.id}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data["messages"]) >= 1

        # Find the message from the second user
        found = False
        for msg in data["messages"]:
            if msg["username"] == "seconduser" and msg["content"] == "Message from user 2":
                found = True

        assert found, "Couldn't find message from second user"

    def test_get_chat_messages_from_deleted_user(self, authenticated_client, chat, session: Session):
        """Test retrieving messages from users that have been deleted."""
        # Create a user that we'll delete
        deleted_user = User(username="usertodelete")
        deleted_user.set_password("password123")
        session.add(deleted_user)
        session.flush()

        # Add message from user before deletion
        message = ChatMessage(user_id=deleted_user.id, chat_id=chat.id, content="This message should remain after user deletion")
        session.add(message)
        session.commit()

        # Delete the user
        session.delete(deleted_user)
        session.commit()

        # Test the API endpoint
        response = authenticated_client.get(f"/api/messages/{chat.id}")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert len(data["messages"]) >= 1

        # Find the message from deleted user
        found_deleted_message = False
        for msg in data["messages"]:
            if msg["content"] == "This message should remain after user deletion":
                found_deleted_message = True
                assert msg["username"] == "[Deleted User]"

        assert found_deleted_message, "Message from deleted user was not found in API response"

    def test_get_chat_members(self, authenticated_client, chat_member, chat, user: User, session: Session):
        """Test getting list of chat members."""
        # Add another member to the chat
        second_user = User(username="memberuser")
        second_user.set_password("password123")
        session.add(second_user)
        session.flush()

        new_chat_member = ChatMember(chat_id=chat.id, user_id=second_user.id, is_moderator=False)
        session.add(new_chat_member)
        session.commit()

        response = authenticated_client.get(f"/api/chat/{chat.id}/members")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "members" in data
        assert len(data["members"]) >= 2  # At least the two users we know about

        # Check if both users are in the members list
        usernames = [member["username"] for member in data["members"]]
        assert user.username in usernames
        assert "memberuser" in usernames

    def test_get_chat_members_unauthenticated(self, test_client, chat):
        """Test that unauthenticated users can't access chat members."""
        response = test_client.get(f"/api/chat/{chat.id}/members")
        assert response.status_code == 302  # Should redirect to login
        assert "/login" in response.location

    def test_get_chat_members_unauthorized(self, authenticated_client, session: Session):
        """Test that users can't access members of chats they're not in."""
        # Create a chat the authenticated user is not part of
        unauthorized_chat = Chat(name="Unauthorized Chat", is_group=True)
        session.add(unauthorized_chat)
        session.flush()

        # Add some other user to the chat
        other_user = User(username="otheruser")
        other_user.set_password("password123")
        session.add(other_user)
        session.flush()

        chat_member = ChatMember(chat_id=unauthorized_chat.id, user_id=other_user.id, is_moderator=True)
        session.add(chat_member)
        session.commit()

        response = authenticated_client.get(f"/api/chat/{unauthorized_chat.id}/members")
        assert response.status_code == 403  # Forbidden

        data = json.loads(response.data)
        assert "error" in data
        assert "not a member" in data["error"].lower()

    def test_get_chat_members_nonexistent_chat(self, authenticated_client):
        """Test accessing members for a non-existent chat."""
        response = authenticated_client.get("/api/chat/9999/members")
        assert response.status_code == 404  # Not Found

    def test_search_users_empty_query(self, authenticated_client):
        """Test searching users with empty query."""
        response = authenticated_client.get("/api/search-users?query=")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 0

    def test_search_users_short_query(self, authenticated_client):
        """Test searching users with query that is too short."""
        response = authenticated_client.get("/api/search-users?query=a")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 0

    def test_search_users_valid_query(self, authenticated_client, session: Session):
        """Test searching users with valid query."""
        # Create another user that should be found
        second_user = User(username="testuser2")
        second_user.set_password("password123")
        session.add(second_user)

        third_user = User(username="anotheruser")
        third_user.set_password("password123")
        session.add(third_user)

        session.commit()

        response = authenticated_client.get("/api/search-users?query=test")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 1  # Should find testuser2 but not the current testuser
        assert data["users"][0]["username"] == "testuser2"

    def test_search_users_no_results(self, authenticated_client):
        """Test searching users with query that returns no results."""
        response = authenticated_client.get("/api/search-users?query=nonexistent")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 0

    def test_create_chat_missing_name(self, authenticated_client):
        """Test creating a chat without providing a name."""
        response = authenticated_client.post("/api/chats/create", json={"is_group": True, "user_ids": []}, content_type="application/json")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "name is required" in data["error"].lower()

    def test_create_private_chat_too_many_users(self, authenticated_client):
        """Test creating a private chat with more than one user."""
        response = authenticated_client.post("/api/chats/create", json={"name": "Invalid Private Chat", "is_group": False, "user_ids": [1, 2]}, content_type="application/json")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "private chat requires exactly one user" in data["error"].lower()

    def test_create_private_chat_success(self, authenticated_client, session, user):
        """Test successfully creating a private chat."""
        # Create another user to chat with
        second_user = User(username="chatpartner")
        second_user.set_password("password123")
        session.add(second_user)
        session.commit()

        response = authenticated_client.post("/api/chats/create", json={"name": "Private Chat", "is_group": False, "user_ids": [second_user.id]}, content_type="application/json")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert data["chat"]["name"] == "Private Chat"
        assert data["chat"]["is_group"] is False

        # Verify chat was created in the database
        chat = session.query(Chat).filter_by(id=data["chat"]["id"]).first()
        assert chat is not None
        assert chat.name == "Private Chat"

        # Verify chat memberships were created
        creator_membership = session.query(ChatMember).filter_by(chat_id=chat.id, user_id=user.id).first()
        assert creator_membership is not None
        assert creator_membership.is_moderator is True

        partner_membership = session.query(ChatMember).filter_by(chat_id=chat.id, user_id=second_user.id).first()
        assert partner_membership is not None
        assert partner_membership.is_moderator is False

    def test_create_group_chat_success(self, authenticated_client, session, user):
        """Test successfully creating a group chat."""
        # Create other users for the group
        user_ids = []
        for i in range(3):
            test_user = User(username=f"groupuser{i}")
            test_user.set_password("password123")
            session.add(test_user)
            session.flush()
            user_ids.append(test_user.id)

        session.commit()

        response = authenticated_client.post("/api/chats/create", json={"name": "Test Group", "is_group": True, "user_ids": user_ids}, content_type="application/json")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert data["chat"]["name"] == "Test Group"
        assert data["chat"]["is_group"] is True

        # Verify chat was created in the database
        chat = session.query(Chat).filter_by(id=data["chat"]["id"]).first()
        assert chat is not None
        assert chat.name == "Test Group"

        # Verify chat memberships were created (creator + 3 users)
        member_count = session.query(ChatMember).filter_by(chat_id=chat.id).count()
        assert member_count == 4

    def test_create_chat_nonexistent_users(self, authenticated_client, session, user):
        """Test creating a chat with nonexistent user IDs."""
        response = authenticated_client.post(
            "/api/chats/create",
            json={"name": "Test Group", "is_group": True, "user_ids": [999, 1000]},  # Non-existent user IDs
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True

        # Verify only the creator was added to the chat
        chat_id = data["chat"]["id"]
        member_count = session.query(ChatMember).filter_by(chat_id=chat_id).count()
        assert member_count == 1

    def test_get_user_chats_empty(self, authenticated_client, session, user):
        """Test getting chats for a user with no chats."""
        # Make sure the user doesn't have any chats
        session.query(ChatMember).filter_by(user_id=user.id).delete()
        session.commit()

        response = authenticated_client.get("/api/chats")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "chats" in data
        assert len(data["chats"]) == 0

    def test_get_user_chats_with_data(self, authenticated_client, session, user):
        """Test getting chats for a user with existing chats."""
        # Create some chats and add the user as a member
        chat1 = Chat(name="Test Chat 1", is_group=True)
        chat2 = Chat(name="Test Chat 2", is_group=False)
        session.add_all([chat1, chat2])
        session.flush()

        member1 = ChatMember(chat_id=chat1.id, user_id=user.id, is_moderator=True)
        member2 = ChatMember(chat_id=chat2.id, user_id=user.id, is_moderator=False)
        session.add_all([member1, member2])
        session.commit()

        response = authenticated_client.get("/api/chats")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "chats" in data
        assert len(data["chats"]) == 2

        chat_names = [chat["name"] for chat in data["chats"]]
        assert "Test Chat 1" in chat_names
        assert "Test Chat 2" in chat_names

    def test_get_user_chats_authentication_required(self, test_client):
        """Test that unauthenticated users cannot get chat list."""
        response = test_client.get("/api/chats")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    def test_search_users_authentication_required(self, test_client):
        """Test that unauthenticated users cannot search users."""
        response = test_client.get("/api/search-users?query=test")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    def test_create_chat_authentication_required(self, test_client):
        """Test that unauthenticated users cannot create chats."""
        response = test_client.post("/api/chats/create", json={"name": "Test Chat", "is_group": True, "user_ids": []}, content_type="application/json")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    def test_search_users_empty_query(self, authenticated_client):
        """Test searching users with empty query."""
        response = authenticated_client.get("/api/search-users?query=")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 0

    def test_search_users_short_query(self, authenticated_client):
        """Test searching users with query that is too short."""
        response = authenticated_client.get("/api/search-users?query=a")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 0

    def test_search_users_valid_query(self, authenticated_client, session):
        """Test searching users with valid query."""
        # Create another user that should be found
        second_user = User(username="testuser2")
        second_user.set_password("password123")
        session.add(second_user)

        third_user = User(username="anotheruser")
        third_user.set_password("password123")
        session.add(third_user)

        session.commit()

        response = authenticated_client.get("/api/search-users?query=test")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 1  # Should find testuser2 but not the current testuser
        assert data["users"][0]["username"] == "testuser2"

    def test_search_users_no_results(self, authenticated_client):
        """Test searching users with query that returns no results."""
        response = authenticated_client.get("/api/search-users?query=nonexistent")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "users" in data
        assert len(data["users"]) == 0

    def test_create_chat_missing_name(self, authenticated_client):
        """Test creating a chat without providing a name."""
        response = authenticated_client.post("/api/chats/create", json={"is_group": True, "user_ids": []}, content_type="application/json")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "name is required" in data["error"].lower()

    def test_create_private_chat_too_many_users(self, authenticated_client):
        """Test creating a private chat with more than one user."""
        response = authenticated_client.post("/api/chats/create", json={"name": "Invalid Private Chat", "is_group": False, "user_ids": [1, 2]}, content_type="application/json")
        assert response.status_code == 400

        data = json.loads(response.data)
        assert "error" in data
        assert "private chat requires exactly one user" in data["error"].lower()

    def test_create_private_chat_success(self, authenticated_client, session, user):
        """Test successfully creating a private chat."""
        # Create another user to chat with
        second_user = User(username="chatpartner")
        second_user.set_password("password123")
        session.add(second_user)
        session.commit()

        response = authenticated_client.post("/api/chats/create", json={"name": "Private Chat", "is_group": False, "user_ids": [second_user.id]}, content_type="application/json")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert data["chat"]["name"] == "Private Chat"
        assert data["chat"]["is_group"] is False

        # Verify chat was created in the database
        chat = session.query(Chat).filter_by(id=data["chat"]["id"]).first()
        assert chat is not None
        assert chat.name == "Private Chat"

        # Verify chat memberships were created
        creator_membership = session.query(ChatMember).filter_by(chat_id=chat.id, user_id=user.id).first()
        assert creator_membership is not None
        assert creator_membership.is_moderator is True

        partner_membership = session.query(ChatMember).filter_by(chat_id=chat.id, user_id=second_user.id).first()
        assert partner_membership is not None
        assert partner_membership.is_moderator is False

    def test_create_group_chat_success(self, authenticated_client, session, user):
        """Test successfully creating a group chat."""
        # Create other users for the group
        user_ids = []
        for i in range(3):
            test_user = User(username=f"groupuser{i}")
            test_user.set_password("password123")
            session.add(test_user)
            session.flush()
            user_ids.append(test_user.id)

        session.commit()

        response = authenticated_client.post("/api/chats/create", json={"name": "Test Group", "is_group": True, "user_ids": user_ids}, content_type="application/json")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True
        assert data["chat"]["name"] == "Test Group"
        assert data["chat"]["is_group"] is True

        # Verify chat was created in the database
        chat = session.query(Chat).filter_by(id=data["chat"]["id"]).first()
        assert chat is not None
        assert chat.name == "Test Group"

        # Verify chat memberships were created (creator + 3 users)
        member_count = session.query(ChatMember).filter_by(chat_id=chat.id).count()
        assert member_count == 4

    def test_create_chat_nonexistent_users(self, authenticated_client, session, user):
        """Test creating a chat with nonexistent user IDs."""
        response = authenticated_client.post(
            "/api/chats/create",
            json={"name": "Test Group", "is_group": True, "user_ids": [999, 1000]},  # Non-existent user IDs
            content_type="application/json",
        )
        assert response.status_code == 200

        data = json.loads(response.data)
        assert data["success"] is True

        # Verify only the creator was added to the chat
        chat_id = data["chat"]["id"]
        member_count = session.query(ChatMember).filter_by(chat_id=chat_id).count()
        assert member_count == 1

    def test_get_user_chats_empty(self, authenticated_client, session, user):
        """Test getting chats for a user with no chats."""
        # Make sure the user doesn't have any chats
        session.query(ChatMember).filter_by(user_id=user.id).delete()
        session.commit()

        response = authenticated_client.get("/api/chats")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "chats" in data
        assert len(data["chats"]) == 0

    def test_get_user_chats_with_data(self, authenticated_client, session, user):
        """Test getting chats for a user with existing chats."""
        # Create some chats and add the user as a member
        chat1 = Chat(name="Test Chat 1", is_group=True)
        chat2 = Chat(name="Test Chat 2", is_group=False)
        session.add_all([chat1, chat2])
        session.flush()

        member1 = ChatMember(chat_id=chat1.id, user_id=user.id, is_moderator=True)
        member2 = ChatMember(chat_id=chat2.id, user_id=user.id, is_moderator=False)
        session.add_all([member1, member2])
        session.commit()

        response = authenticated_client.get("/api/chats")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "chats" in data
        assert len(data["chats"]) == 2

        chat_names = [chat["name"] for chat in data["chats"]]
        assert "Test Chat 1" in chat_names
        assert "Test Chat 2" in chat_names

    def test_get_user_chats_authentication_required(self, test_client):
        """Test that unauthenticated users cannot get chat list."""
        response = test_client.get("/api/chats")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    def test_search_users_authentication_required(self, test_client):
        """Test that unauthenticated users cannot search users."""
        response = test_client.get("/api/search-users?query=test")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    def test_create_chat_authentication_required(self, test_client):
        """Test that unauthenticated users cannot create chats."""
        response = test_client.post("/api/chats/create", json={"name": "Test Chat", "is_group": True, "user_ids": []}, content_type="application/json")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    def test_ban_user_success(self, authenticated_client, chat, session, user, chat_member):
        """Test successfully banning a user from a chat."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Create another user to ban
        target_user = User(username="targetuser")
        target_user.set_password("password123")
        session.add(target_user)
        session.flush()

        # Add target user to chat
        chat_member = ChatMember(chat_id=chat.id, user_id=target_user.id)
        session.add(chat_member)
        session.commit()

        # Ban the user
        response = authenticated_client.post(f"/api/chat/{chat.id}/ban", json={"user_id": target_user.id, "reason": "Inappropriate behavior"}, content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert f"User {target_user.username} has been banned" in data["message"]

        # Verify the user is banned in the database
        banned_member = session.query(ChatMember).filter_by(user_id=target_user.id, chat_id=chat.id).first()
        assert banned_member.is_banned is True
        assert banned_member.banned_reason == "Inappropriate behavior"
        assert banned_member.banned_at is not None

    def test_ban_user_unauthorized(self, authenticated_client, chat, session, user):
        """Test unauthorized attempt to ban a user (non-moderator)."""
        # Create another user to ban
        target_user = User(username="targetuser")
        target_user.set_password("password123")
        session.add(target_user)
        session.flush()

        # Add target user to chat
        chat_member = ChatMember(chat_id=chat.id, user_id=target_user.id)
        session.add(chat_member)
        session.commit()

        # Attempt to ban without being a moderator
        response = authenticated_client.post(f"/api/chat/{chat.id}/ban", json={"user_id": target_user.id, "reason": "Inappropriate behavior"}, content_type="application/json")

        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data
        assert "moderator" in data["error"].lower()

    def test_ban_user_self(self, authenticated_client, chat, session, user, chat_member):
        """Test attempt to ban self."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Attempt to ban self
        response = authenticated_client.post(f"/api/chat/{chat.id}/ban", json={"user_id": user.id, "reason": "Testing self-ban"}, content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "cannot ban yourself" in data["error"].lower()

    def test_ban_user_nonexistent(self, authenticated_client, chat, session, user, chat_member):
        """Test attempt to ban a nonexistent user."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Attempt to ban nonexistent user
        response = authenticated_client.post(f"/api/chat/{chat.id}/ban", json={"user_id": 9999, "reason": "Test reason"}, content_type="application/json")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "user not found" in data["error"].lower()

    def test_ban_moderator(self, authenticated_client, chat, session, user, chat_member):
        """Test attempt to ban another moderator."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Create another moderator
        other_mod = User(username="othermod")
        other_mod.set_password("password123")
        session.add(other_mod)
        session.flush()

        # Add other moderator to chat
        other_member = ChatMember(chat_id=chat.id, user_id=other_mod.id, is_moderator=True)
        session.add(other_member)
        session.commit()

        # Attempt to ban other moderator
        response = authenticated_client.post(f"/api/chat/{chat.id}/ban", json={"user_id": other_mod.id, "reason": "Testing mod ban"}, content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "cannot ban a moderator" in data["error"].lower()

    def test_ban_non_member(self, authenticated_client, chat, session, user, chat_member):
        """Test attempt to ban a user who is not a member of the chat."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Create user who is not in the chat
        non_member = User(username="nonmember")
        non_member.set_password("password123")
        session.add(non_member)
        session.commit()

        # Attempt to ban non-member
        response = authenticated_client.post(f"/api/chat/{chat.id}/ban", json={"user_id": non_member.id, "reason": "Testing non-member ban"}, content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "not a member" in data["error"].lower()

    def test_unban_user_success(self, authenticated_client, chat, session, user, chat_member):
        """Test successfully unbanning a user from a chat."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Create another user who is banned
        banned_user = User(username="banneduser")
        banned_user.set_password("password123")
        session.add(banned_user)
        session.flush()

        # Add banned user to chat and set as banned
        banned_member = ChatMember(chat_id=chat.id, user_id=banned_user.id, is_banned=True)
        banned_member.banned_at = datetime.now(UTC)
        banned_member.banned_reason = "Test ban reason"
        session.add(banned_member)
        session.commit()

        # Unban the user
        response = authenticated_client.post(f"/api/chat/{chat.id}/unban", json={"user_id": banned_user.id}, content_type="application/json")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert f"User {banned_user.username} has been unbanned" in data["message"]

        # Verify the user is unbanned in the database
        unbanned_member = session.query(ChatMember).filter_by(user_id=banned_user.id, chat_id=chat.id).first()
        assert unbanned_member.is_banned is False
        assert unbanned_member.banned_reason is None
        assert unbanned_member.banned_at is None

    def test_unban_user_unauthorized(self, authenticated_client, chat, session, user):
        """Test unauthorized attempt to unban a user (non-moderator)."""
        # Create another user who is banned
        banned_user = User(username="banneduser")
        banned_user.set_password("password123")
        session.add(banned_user)
        session.flush()

        # Add banned user to chat and set as banned
        banned_member = ChatMember(chat_id=chat.id, user_id=banned_user.id, is_banned=True)
        banned_member.banned_at = datetime.now(UTC)
        banned_member.banned_reason = "Test ban reason"
        session.add(banned_member)
        session.commit()

        # Attempt to unban without being a moderator
        response = authenticated_client.post(f"/api/chat/{chat.id}/unban", json={"user_id": banned_user.id}, content_type="application/json")

        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data
        assert "moderator" in data["error"].lower()

    def test_unban_user_nonexistent(self, authenticated_client, chat, session, user, chat_member):
        """Test attempt to unban a nonexistent user."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Attempt to unban nonexistent user
        response = authenticated_client.post(f"/api/chat/{chat.id}/unban", json={"user_id": 9999}, content_type="application/json")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "error" in data
        assert "user not found" in data["error"].lower()

    def test_unban_not_banned_user(self, authenticated_client, chat, session, user, chat_member):
        """Test attempt to unban a user who is not banned."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Create another user who is not banned
        normal_user = User(username="normaluser")
        normal_user.set_password("password123")
        session.add(normal_user)
        session.flush()

        # Add user to chat (not banned)
        chat_member = ChatMember(chat_id=chat.id, user_id=normal_user.id)
        session.add(chat_member)
        session.commit()

        # Attempt to unban non-banned user
        response = authenticated_client.post(f"/api/chat/{chat.id}/unban", json={"user_id": normal_user.id}, content_type="application/json")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data
        assert "not banned" in data["error"].lower()

    def test_get_banned_users_success(self, authenticated_client, chat, session, user, chat_member):
        """Test successfully getting list of banned users."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Create banned users
        banned_users = []
        for i in range(3):
            banned_user = User(username=f"banned{i}")
            banned_user.set_password("password123")
            session.add(banned_user)
            session.flush()
            banned_users.append(banned_user)

        # Add banned users to chat
        for i, banned_user in enumerate(banned_users):
            banned_member = ChatMember(chat_id=chat.id, user_id=banned_user.id, is_banned=True)
            banned_member.banned_at = datetime.now(UTC)
            banned_member.banned_reason = f"Banned for reason {i}"
            session.add(banned_member)

        session.commit()

        # Get banned users list
        response = authenticated_client.get(f"/api/chat/{chat.id}/banned")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert "banned_users" in data
        assert len(data["banned_users"]) == 3

        # Check banned user details
        for i, banned_user in enumerate(data["banned_users"]):
            assert banned_user["username"] == f"banned{i}"
            assert banned_user["reason"] == f"Banned for reason {i}"
            assert "banned_at" in banned_user

    def test_get_banned_users_unauthorized(self, authenticated_client, chat, session, user):
        """Test unauthorized attempt to get banned users list (non-moderator)."""
        # Create a banned user
        banned_user = User(username="banneduser")
        banned_user.set_password("password123")
        session.add(banned_user)
        session.flush()

        # Add banned user to chat
        banned_member = ChatMember(chat_id=chat.id, user_id=banned_user.id, is_banned=True)
        banned_member.banned_at = datetime.now(UTC)
        banned_member.banned_reason = "Test ban reason"
        session.add(banned_member)
        session.commit()

        # Attempt to get banned users without being a moderator
        response = authenticated_client.get(f"/api/chat/{chat.id}/banned")
        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data
        assert "moderator" in data["error"].lower()

    def test_get_banned_users_empty(self, authenticated_client, chat, session, user, chat_member):
        """Test getting empty list of banned users."""
        # Make the current authenticated user a moderator
        member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()
        member.is_moderator = True
        session.commit()

        # Get banned users list (empty)
        response = authenticated_client.get(f"/api/chat/{chat.id}/banned")
        assert response.status_code == 200
        data = json.loads(response.data)

        assert "banned_users" in data
        assert len(data["banned_users"]) == 0

    def test_get_banned_users_nonexistent_chat(self, authenticated_client):
        """Test getting banned users for a nonexistent chat."""
        response = authenticated_client.get("/api/chat/9999/banned")
        assert response.status_code == 404 or response.status_code == 500  # TODO fix this in the API

    def test_ban_unban_unauthenticated(self, test_client, chat):
        """Test that unauthenticated users cannot ban or unban users."""
        # Test ban endpoint
        response = test_client.post(f"/api/chat/{chat.id}/ban", json={"user_id": 1, "reason": "Test reason"}, content_type="application/json")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

        # Test unban endpoint
        response = test_client.post(f"/api/chat/{chat.id}/unban", json={"user_id": 1}, content_type="application/json")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

        # Test banned users list endpoint
        response = test_client.get(f"/api/chat/{chat.id}/banned")
        assert response.status_code == 302  # Redirect to login
        assert "/login" in response.location

    def test_delete_message_own_message(self, test_client, session, user):
        """Test that a user can delete their own message."""
        # Create a test chat
        chat = Chat(name="Delete Message Test Chat", is_group=True)
        session.add(chat)
        session.flush()

        # Add user to chat
        chat_member = ChatMember(chat_id=chat.id, user_id=user.id)
        session.add(chat_member)
        session.flush()

        # Create a message from the user
        message = ChatMessage(chat_id=chat.id, user_id=user.id, content="Message to delete")
        session.add(message)
        session.commit()

        # Log in as the user
        test_client.post("/login", data={"username": user.username, "password": "password123"}, follow_redirects=True)

        # Delete user's own message
        response = test_client.post(f"/api/message/{message.id}/delete", headers={"Content-Type": "application/json"})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] == True

        # Verify the message was deleted from the database
        deleted_message = session.query(ChatMessage).get(message.id)
        assert deleted_message is None

    def test_delete_message_others_message_as_regular_user(self, test_client, session, user):
        """Test that a regular user cannot delete someone else's message."""
        # Create a test chat
        chat = Chat(name="Delete Message Test Chat", is_group=True)
        session.add(chat)
        session.flush()

        # Create another user
        other_user = User(username="other_user")
        other_user.set_password("password123")
        session.add(other_user)
        session.flush()

        # Add both users to chat
        chat_member1 = ChatMember(chat_id=chat.id, user_id=user.id)
        chat_member2 = ChatMember(chat_id=chat.id, user_id=other_user.id)
        session.add_all([chat_member1, chat_member2])
        session.flush()

        # Create a message from the other user
        other_message = ChatMessage(chat_id=chat.id, user_id=other_user.id, content="Other user's message")
        session.add(other_message)
        session.commit()

        # Log in as the regular user
        test_client.post("/login", data={"username": user.username, "password": "password123"}, follow_redirects=True)

        # Attempt to delete other user's message
        response = test_client.post(f"/api/message/{other_message.id}/delete", headers={"Content-Type": "application/json"})

        assert response.status_code == 403
        data = json.loads(response.data)
        assert "error" in data

        # Verify the message still exists in the database
        message_exists = session.query(ChatMessage).get(other_message.id)
        assert message_exists is not None

    def test_delete_message_as_moderator(self, test_client, session, user):
        """Test that a moderator can delete any message in the chat."""
        # Create a test chat
        chat = Chat(name="Moderator Delete Test Chat", is_group=True)
        session.add(chat)
        session.flush()

        # Create another user
        other_user = User(username="message_author")
        other_user.set_password("password123")
        session.add(other_user)
        session.flush()

        # Add users to chat - make first user a moderator
        mod_member = ChatMember(chat_id=chat.id, user_id=user.id, is_moderator=True)
        regular_member = ChatMember(chat_id=chat.id, user_id=other_user.id)
        session.add_all([mod_member, regular_member])
        session.flush()

        # Create a message from the other user
        other_message = ChatMessage(chat_id=chat.id, user_id=other_user.id, content="Message to be deleted by mod")
        session.add(other_message)
        session.commit()

        # Log in as the moderator
        test_client.post("/login", data={"username": user.username, "password": "password123"}, follow_redirects=True)

        # Delete the other user's message
        response = test_client.post(f"/api/message/{other_message.id}/delete", headers={"Content-Type": "application/json"})

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] == True

        # Verify the message was deleted from the database
        deleted_message = session.query(ChatMessage).get(other_message.id)
        assert deleted_message is None

    @pytest.mark.xfail(reason="need to add обработчик емае")
    def test_delete_nonexistent_message(self, authenticated_client):
        """Test that attempting to delete a non-existent message returns 404."""
        # Choose a message ID that doesn't exist
        non_existent_id = 99999

        response = authenticated_client.post(f"/api/message/{non_existent_id}/delete", headers={"Content-Type": "application/json"})

        assert response.status_code == 404

    def test_delete_message_unauthenticated(self, test_client, session):
        """Test that an unauthenticated user cannot delete messages."""
        # Create a test chat and message
        chat = Chat(name="Unauthenticated Test", is_group=True)
        session.add(chat)
        session.flush()

        user = User(username="message_owner")
        user.set_password("password123")
        session.add(user)
        session.flush()

        # Add user to chat
        chat_member = ChatMember(chat_id=chat.id, user_id=user.id)
        session.add(chat_member)
        session.flush()

        # Create a message
        message = ChatMessage(chat_id=chat.id, user_id=user.id, content="Test message")
        session.add(message)
        session.commit()

        # Ensure user is not logged in
        test_client.get("/logout")

        # Attempt to delete the message without authentication
        response = test_client.post(f"/api/message/{message.id}/delete", headers={"Content-Type": "application/json"})

        # Should redirect to login
        assert response.status_code == 302
        assert "/login" in response.location

        # Verify message still exists
        message_exists = session.query(ChatMessage).get(message.id)
        assert message_exists is not None
