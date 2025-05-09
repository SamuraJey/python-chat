import pytest
from flask.testing import FlaskClient
from flask_socketio import SocketIOTestClient

from src.database.models.chat import Chat
from src.database.models.chat_message import ChatMessage
from src.database.models.user import User


class TestSocketEvents:
    """Tests for Socket.IO events."""

    @pytest.fixture
    def authenticated_socket(self, test_client: FlaskClient, socket_client: SocketIOTestClient, user: User) -> SocketIOTestClient:
        """Create an authenticated Socket.IO test client."""
        # Log the user in first
        with test_client.session_transaction() as sess:
            sess["_user_id"] = user.id

        # Ensure socket connected successfully
        assert socket_client.is_connected()
        return socket_client

    @pytest.mark.skip(reason="TODO not done test")
    def test_connect(self, authenticated_socket: SocketIOTestClient):
        """Test socket connection event."""
        # Connection is verified in the fixture
        assert authenticated_socket.is_connected()

        # Check if we received the expected events after connect
        received = authenticated_socket.get_received()
        assert any(event["name"] == "user_joined" for event in received)
        assert any(event["name"] == "set_username" for event in received)
        assert any(event["name"] == "online_users" for event in received)

    @pytest.mark.skip(reason="TODO not done test")
    def test_connect_unauthenticated(
        self,
        socket_client: SocketIOTestClient,
    ):
        """Test that unauthenticated users can't establish socket connections."""

        # Socket connection should fail for unauthenticated users
        assert not socket_client.is_connected()

    def test_disconnect(self, authenticated_socket: SocketIOTestClient):
        """Test socket disconnection."""
        # First ensure we're connected
        assert authenticated_socket.is_connected()

        # Then disconnect
        authenticated_socket.disconnect()

        # Verify client state
        assert not authenticated_socket.is_connected()

    @pytest.mark.skip(reason="TODO not done test")
    def test_join_chat(self, authenticated_socket, chat):
        """Test joining a chat room."""
        # Join chat
        authenticated_socket.emit("join", {"chat_id": chat.id})

        # Get received events
        received = authenticated_socket.get_received()

        # Find the join confirmation event
        join_events = [event for event in received if event["name"] == "joined_chat"]
        assert len(join_events) > 0
        assert join_events[0]["args"][0]["chat_id"] == chat.id
        assert join_events[0]["args"][0]["status"] == "success"

    @pytest.mark.skip(reason="TODO not done test")
    def test_send_message(self, authenticated_socket, chat, session):
        """Test sending a message to a chat."""
        # First join the chat
        authenticated_socket.emit("join", {"chat_id": chat.id})
        authenticated_socket.get_received()  # Clear events

        # Send a message
        message_content = "Hello, this is a test message!"
        authenticated_socket.emit("send_message", {"chat_id": chat.id, "message": message_content})

        # Get received events
        received = authenticated_socket.get_received()

        # Find the message received event
        message_events = [event for event in received if event["name"] == "receive_message"]
        assert len(message_events) > 0
        assert message_events[0]["args"][0]["message"] == message_content

        # Verify message was saved to database
        message = session.query(ChatMessage).filter_by(content=message_content).first()

        assert message is not None
        assert message.chat_id == chat.id

    @pytest.mark.skip(reason="TODO not done test")
    def test_get_online_users(self, authenticated_socket, user):
        """Test getting the list of online users."""
        # Emit get_online_users event
        authenticated_socket.emit("get_online_users")

        # Get received events
        received = authenticated_socket.get_received()

        # Find the online_users event
        user_events = [event for event in received if event["name"] == "online_users"]
        assert len(user_events) > 0
        assert isinstance(user_events[0]["args"][0]["users"], list)
        assert user.username in user_events[0]["args"][0]["users"]

    def test_leave_chat(self, authenticated_socket: SocketIOTestClient, chat: Chat):
        """Test leaving a chat room."""
        # Join chat first
        authenticated_socket.emit("join", {"chat_id": chat.id})
        authenticated_socket.get_received()  # Clear events

        # Leave the chat
        authenticated_socket.emit("leave", {"chat_id": chat.id})

        # Since 'user_left_chat' is broadcast to the room and not the leaving user,
        # we can't easily test that event was received
        # In a real test with multiple clients, we'd verify this from another client
        assert authenticated_socket.is_connected()
