from src.database.models.chat import Chat
from src.database.models.chat_member import ChatMember


class TestIndexRoutes:
    """Tests for index routes."""

    def test_index_unauthenticated_redirect(self, test_client):
        """Test that unauthenticated users are redirected to login."""
        response = test_client.get("/", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.location

    def test_index_authenticated_shows_chats(self, authenticated_client, chat, chat_member):
        """Test that authenticated users see their chats."""
        response = authenticated_client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Test Chat" in response.data
        assert b"Available Chats" in response.data

    def test_index_no_chats(self, authenticated_client, user, session):
        """Test index view when user has no chats."""
        # Remove any existing chat memberships
        ChatMember.query.filter_by(user_id=user.id).delete()
        session.commit()

        response = authenticated_client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Available Chats" in response.data
        # Either a "No chats" message or an empty list should be displayed
        # Adjust the assertion based on your template
        assert b"No chats available" in response.data or b"chat-list-item" not in response.data

    def test_index_shows_multiple_chats(self, authenticated_client, user, session):
        """Test that multiple chats are displayed."""
        # Create multiple chats and memberships
        chat1 = Chat(name="Group Chat 1", is_group=True)
        chat2 = Chat(name="Direct Message", is_group=False)
        session.add_all([chat1, chat2])
        session.commit()

        # Add user to both chats
        membership1 = ChatMember(user_id=user.id, chat_id=chat1.id)
        membership2 = ChatMember(user_id=user.id, chat_id=chat2.id)
        session.add_all([membership1, membership2])
        session.commit()

        response = authenticated_client.get("/", follow_redirects=True)
        assert response.status_code == 200
        assert b"Group Chat 1" in response.data
        assert b"Direct Message" in response.data
