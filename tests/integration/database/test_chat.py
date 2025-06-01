from python_chat.database.models import Chat, ChatMember, ChatMessage, User


class TestChat:
    """Test suite for Chat model functionality."""

    def test_chat_creation(self, session):
        """Test creating a new chat."""
        # Create a new chat
        chat = Chat(name="Test Group Chat", is_group=True)

        session.add(chat)
        session.commit()

        # Retrieve chat and verify
        saved_chat = session.query(Chat).filter_by(name="Test Group Chat").first()

        assert saved_chat is not None
        assert saved_chat.name == "Test Group Chat"
        assert saved_chat.is_group is True
        assert saved_chat.created_at is not None

    def test_direct_chat_creation(self, session):
        """Test creating a direct (non-group) chat."""
        # Create a direct chat
        chat = Chat(name="Direct Message", is_group=False)

        session.add(chat)
        session.commit()

        # Retrieve chat and verify
        saved_chat = session.query(Chat).filter_by(name="Direct Message").first()

        assert saved_chat is not None
        assert saved_chat.is_group is False

    def test_add_member(self, session):
        """Test adding a member to a chat."""
        # Create chat and user
        chat = Chat(name="Member Test Chat", is_group=True)
        user = User(username="chatmember")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Add user to chat using the add_member method
        chat.add_member(user)
        session.commit()

        # Verify member is added
        assert chat.is_member(user) is True
        assert len(chat.get_members()) == 1
        assert chat.get_members()[0].id == user.id

        # Verify ChatMember properties
        chat_member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()

        assert chat_member is not None
        assert chat_member.is_moderator is False
        assert chat_member.joined_at is not None

    def test_add_moderator(self, session):
        """Test adding a moderator to a chat."""
        # Create chat and user
        chat = Chat(name="Moderator Test Chat", is_group=True)
        user = User(username="chatmod")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Add user as moderator
        member = chat.add_member(user, is_moderator=True)
        session.commit()

        # Verify moderator status
        assert member.is_moderator is True
        assert len(chat.get_moderators()) == 1
        assert chat.get_moderators()[0].id == user.id

    def test_remove_member(self, session):
        """Test removing a member from a chat."""
        # Create chat and user
        chat = Chat(name="Removal Test Chat", is_group=True)
        user = User(username="removeme")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Add and then remove member
        chat.add_member(user)
        session.commit()

        assert chat.is_member(user) is True

        chat.remove_member(user)
        session.commit()

        # Verify removal
        assert chat.is_member(user) is False
        assert len(chat.get_members()) == 0

    def test_chat_messages(self, session):
        """Test adding messages to a chat."""
        # Create chat, user, and message
        chat = Chat(name="Message Test Chat", is_group=True)
        user = User(username="messager")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Add user to chat
        chat.add_member(user)

        # Create messages
        message1 = ChatMessage(chat_id=chat.id, user_id=user.id, content="Test message 1")
        message2 = ChatMessage(chat_id=chat.id, user_id=user.id, content="Test message 2")

        session.add_all([message1, message2])
        session.commit()

        # Verify messages
        assert len(chat.messages) == 2
        assert chat.messages[0].content == "Test message 1"
        assert chat.messages[1].content == "Test message 2"

        # Verify relationship with user
        assert message1.user.id == user.id

    def test_chat_repr(self, session):
        """Test the string representation of Chat model."""
        group_chat = Chat(name="Group Chat Test", is_group=True)
        direct_chat = Chat(name="Direct Chat Test", is_group=False)

        assert repr(group_chat) == "<Chat Group Chat Test (group)>"
        assert repr(direct_chat) == "<Chat Direct Chat Test (direct)>"
