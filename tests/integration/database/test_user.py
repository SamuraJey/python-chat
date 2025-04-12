from src.database.models import Chat, ChatMember, ChatMessage, User


class TestUser:
    """Test suite for User model functionality."""

    def test_user_creation(self, session):
        """Test creating a new user."""
        # Create a new user
        user = User(username="testuser")
        user.set_password("password123")

        session.add(user)
        session.commit()

        # Retrieve user and verify
        saved_user = session.query(User).filter_by(username="testuser").first()

        assert saved_user is not None
        assert saved_user.username == "testuser"
        assert saved_user.is_admin is False
        assert saved_user.is_blocked is False

    def test_password_hashing(self, session):
        """Test password hashing and verification."""
        user = User(username="passwordtest")
        user.set_password("secret123")

        session.add(user)
        session.commit()

        # Verify correct password works
        assert user.check_password("secret123") is True

        # Verify incorrect password fails
        assert user.check_password("wrongpass") is False

        # Verify the password is stored as a hash, not plaintext
        assert user.password_hash != "secret123"

    def test_user_blocking(self, session):
        """Test blocking and unblocking a user."""
        user = User(username="blockme")
        user.set_password("testpass")

        session.add(user)
        session.commit()

        # Block the user
        reason = "Violated community guidelines"
        user.block(reason)

        assert user.is_blocked is True
        assert user.blocked_reason == reason
        assert user.blocked_at is not None

        # Unblock the user
        user.unblock()

        assert user.is_blocked is False
        assert user.blocked_reason is None
        assert user.blocked_at is None

    def test_user_relationships(self, session):
        """Test user relationships with chats and messages."""
        # Create user and chat
        user = User(username="relationuser")
        user.set_password("testpass")

        chat = Chat(name="Test Chat", is_group=True)

        session.add_all([user, chat])
        session.flush()

        # Add user to chat
        chat_member = ChatMember(user_id=user.id, chat_id=chat.id)
        session.add(chat_member)

        # Add message
        message = ChatMessage(user_id=user.id, chat_id=chat.id, content="Hello, world!")
        session.add(message)
        session.commit()

        # Verify relationships
        assert len(user.chats) == 1
        assert user.chats[0].chat_id == chat.id

        assert len(user.messages) == 1
        assert user.messages[0].content == "Hello, world!"

    def test_user_repr(self, session):
        """Test the string representation of the User model."""
        user = User(username="reprtest")

        assert repr(user) == "<User reprtest>"
