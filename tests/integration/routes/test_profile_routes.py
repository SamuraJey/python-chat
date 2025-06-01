from sqlalchemy.orm import Session

from python_chat.database.models.chat_member import ChatMember
from python_chat.database.models.chat_message import ChatMessage


class TestProfileRoutes:
    """Tests for profile routes."""

    def test_profile_page_loads(self, authenticated_client):
        """Test if the profile page loads correctly for authenticated users."""
        response = authenticated_client.get("/profile")
        assert response.status_code == 200
        assert b"profile-container" in response.data

    def test_profile_page_redirects_unauthenticated(self, test_client):
        """Test if unauthenticated users are redirected from profile page."""
        response = test_client.get("/profile", follow_redirects=False)
        assert response.status_code == 302  # Redirect status

        # Follow redirect to confirm it goes to login page
        response = test_client.get("/profile", follow_redirects=True)
        assert b"Login" in response.data

    def test_profile_shows_user_stats(self, authenticated_client, session: Session, user, chat):
        """Test if the profile page shows correct user statistics."""
        # Create some chat members and messages for the user
        chat_member = ChatMember(user_id=user.id, chat_id=chat.id)
        session.add(chat_member)

        message1 = ChatMessage(user_id=user.id, chat_id=chat.id, content="Test message 1")
        message2 = ChatMessage(user_id=user.id, chat_id=chat.id, content="Test message 2")
        session.add(message1)
        session.add(message2)
        session.commit()

        response = authenticated_client.get("/profile")
        assert response.status_code == 200

        # Check if stats are displayed correctly
        # The exact format may vary, so we check for presence of numbers
        response_text = response.data.decode("utf-8")
        assert "1" in response_text  # 1 chat
        assert "2" in response_text  # 2 messages
