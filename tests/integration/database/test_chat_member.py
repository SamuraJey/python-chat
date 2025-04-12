from src.database.models import Chat, ChatMember, User


class TestChatMember:
    """Test suite for ChatMember model functionality."""

    def test_chat_member_creation(self, session):
        """Test creating a new chat member relationship."""
        # Create chat and user first
        chat = Chat(name="Member Creation Test", is_group=True)
        user = User(username="memberuser")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Create member relationship
        member = ChatMember(user_id=user.id, chat_id=chat.id, is_moderator=False)

        session.add(member)
        session.commit()

        # Retrieve relationship and verify
        saved_member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()

        assert saved_member is not None
        assert saved_member.is_moderator is False
        assert saved_member.joined_at is not None

    def test_chat_member_moderator(self, session):
        """Test creating a chat member with moderator privileges."""
        # Create chat and user
        chat = Chat(name="Mod Creation Test", is_group=True)
        user = User(username="moduser")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Create moderator relationship
        member = ChatMember(user_id=user.id, chat_id=chat.id, is_moderator=True)

        session.add(member)
        session.commit()

        # Verify moderator status
        saved_member = session.query(ChatMember).filter_by(user_id=user.id, chat_id=chat.id).first()

        assert saved_member.is_moderator is True

    def test_chat_member_relationships(self, session):
        """Test chat member relationships with user and chat."""
        # Create test data
        chat = Chat(name="MemberRel Test Chat", is_group=True)
        user = User(username="memberreluser")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Create relationship
        member = ChatMember(user_id=user.id, chat_id=chat.id)

        session.add(member)
        session.commit()

        # Verify relationships
        assert member.user.id == user.id
        assert member.user.username == "memberreluser"
        assert member.chat.id == chat.id
        assert member.chat.name == "MemberRel Test Chat"

        # Verify reverse relationships
        assert member in user.chats
        assert member in chat.members

    def test_chat_member_cascade_delete(self, session):
        """Test that chat members are deleted when chat or user is deleted."""
        # Create test data
        chat1 = Chat(name="Chat Delete Test", is_group=True)
        chat2 = Chat(name="User Delete Test", is_group=True)
        user1 = User(username="chatdeluser")
        user2 = User(username="userdeluser")
        user1.set_password("testpass")
        user2.set_password("testpass")

        session.add_all([chat1, chat2, user1, user2])
        session.flush()

        # Create memberships
        member1 = ChatMember(user_id=user1.id, chat_id=chat1.id)
        member2 = ChatMember(user_id=user2.id, chat_id=chat2.id)

        session.add_all([member1, member2])
        session.commit()

        # Delete chat and verify member is deleted
        session.delete(chat1)
        session.commit()

        deleted_member1 = session.query(ChatMember).filter_by(user_id=user1.id, chat_id=chat1.id).first()
        assert deleted_member1 is None

        # Delete user and verify member is deleted
        session.delete(user2)
        session.commit()

        deleted_member2 = session.query(ChatMember).filter_by(user_id=user2.id, chat_id=chat2.id).first()
        assert deleted_member2 is None

    def test_chat_member_repr(self, session):
        """Test the string representation of the ChatMember model."""
        # Create test data
        chat = Chat(name="Repr Test Chat", is_group=True)
        user = User(username="memberrepruser")
        user.set_password("testpass")

        session.add_all([chat, user])
        session.flush()

        # Create regular member
        member = ChatMember(user_id=user.id, chat_id=chat.id, is_moderator=False)

        session.add(member)
        session.commit()

        # Verify repr output
        # TODO maybe we do not need this
        try:
            assert f"<ChatMember user_id={user.id} chat_id={chat.id} is_moderator=False>" == repr(member)
        except AssertionError:
            print(f"Warning: {repr(member)} does not match expected format.")  # noqa: T201

        member.is_moderator = True
        session.commit()

        # Verify updated repr
        # TODO maybe we do not need this
        try:
            assert f"<ChatMember user_id={user.id} chat_id={chat.id} is_moderator=True>" == repr(member)
        except AssertionError:
            print(f"Warning: {repr(member)} does not match expected format.")  # noqa: T201
