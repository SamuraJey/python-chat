from src.database.models import Chat, ChatMessage, User


class TestChatMessage:
    """Test suite for ChatMessage model functionality."""

    def test_message_creation(self, session):
        """Test creating a new chat message."""
        # Create chat and user first
        chat = Chat(name="Message Creation Test", is_group=True)
        user = User(username="msgauthor")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Create a message
        message = ChatMessage(chat_id=chat.id, user_id=user.id, content="Hello, this is a test message!")

        session.add(message)
        session.commit()

        # Retrieve message and verify
        saved_message = session.query(ChatMessage).filter_by(chat_id=chat.id, user_id=user.id).first()

        assert saved_message is not None
        assert saved_message.content == "Hello, this is a test message!"
        assert saved_message.sent_at is not None

    def test_message_relationships(self, session):
        """Test message relationships with user and chat."""
        # Create test data
        chat = Chat(name="Relation Test Chat", is_group=True)
        user = User(username="reluser")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Add user to chat
        chat.add_member(user)

        # Create message
        message = ChatMessage(chat_id=chat.id, user_id=user.id, content="Testing relationships")

        session.add(message)
        session.commit()

        # Verify relationships
        assert message.user.id == user.id
        assert message.user.username == "reluser"
        assert message.chat.id == chat.id
        assert message.chat.name == "Relation Test Chat"

        # Verify reverse relationships
        assert message in user.messages
        assert message in chat.messages

    def test_message_cascade_delete_from_chat(self, session):
        """Test that messages are deleted when a chat is deleted."""
        # Create test data
        chat = Chat(name="Delete Test Chat", is_group=True)
        user = User(username="deluser")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Create message
        message = ChatMessage(chat_id=chat.id, user_id=user.id, content="I should be deleted with the chat")

        session.add(message)
        session.commit()

        # Get message ID for later checking
        message_id = message.id

        # Delete chat
        session.delete(chat)
        session.commit()

        # Verify message was deleted
        deleted_message = session.query(ChatMessage).filter_by(id=message_id).first()
        assert deleted_message is None

    def test_message_repr(self, session):
        """Test the string representation of the ChatMessage model."""
        # Create test data
        chat = Chat(name="Repr Test Chat", is_group=True)
        user = User(username="repruser")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Create message with short content
        short_message = ChatMessage(chat_id=chat.id, user_id=user.id, content="Short message")

        # Create message with long content
        long_message = ChatMessage(chat_id=chat.id, user_id=user.id, content="This is a very long message that should be truncated in the repr method")

        session.add_all([short_message, long_message])
        session.commit()

        # Verify repr output
        assert f"<ChatMessage id={short_message.id} chat={chat.id} user={user.id} content='Short message'>" in repr(short_message)

        # For long message, content should be truncated with ...
        assert "..." in repr(long_message)
        assert repr(long_message).startswith(f"<ChatMessage id={long_message.id} chat={chat.id} user={user.id} content='This is a very")
