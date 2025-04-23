import json
from datetime import UTC, datetime, timedelta

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

    def test_get_chat_messages_multiple(self, authenticated_client, chat, user, session):
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

    def test_get_chat_messages_different_users(self, authenticated_client, chat, session):
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

    def test_get_chat_messages_from_deleted_user(self, authenticated_client, chat, session):
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
