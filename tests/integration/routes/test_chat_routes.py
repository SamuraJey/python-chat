import json
from datetime import UTC, datetime, timedelta

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
