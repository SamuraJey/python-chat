import logging
import os
import sys

from src.database import db
from src.database.models.chat import Chat, ChatMember
from src.database.models.chat_message import ChatMessage
from src.database.models.user import User

# Add the project root to Python path to fix import issues
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))


logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def initialize_db(app, db):
    """Initialize database with sample data"""
    with app.app_context():
        try:
            # Drop all tables and recreate them
            db.drop_all()
            db.create_all()

            logger.info("Created database tables")

            # Create sample users
            user1 = User(username="ali", is_admin=True)
            user1.set_password("aaa")
            user2 = User(username="bob")
            user2.set_password("bbb")
            user3 = User(username="caly")
            user3.set_password("ccc")

            db.session.add_all([user1, user2, user3])
            db.session.commit()
            logger.info("Created sample users")

            # Create sample chats
            chat1 = Chat(name="General Chat", is_group=True)
            chat2 = Chat(name="Project Discussion", is_group=False)

            db.session.add_all([chat1, chat2])
            db.session.commit()
            logger.info("Created sample chats")

            # Add users to chats
            chat_member1 = ChatMember(user_id=user1.id, chat_id=chat1.id)
            chat_member2 = ChatMember(user_id=user2.id, chat_id=chat1.id)
            chat_member3 = ChatMember(user_id=user3.id, chat_id=chat1.id)
            chat_member4 = ChatMember(user_id=user1.id, chat_id=chat2.id)
            chat_member5 = ChatMember(user_id=user2.id, chat_id=chat2.id)

            db.session.add_all([chat_member1, chat_member2, chat_member3, chat_member4, chat_member5])
            db.session.commit()

            # Add sample messages
            message1 = ChatMessage(content="Welcome to the general chat!", user_id=user1.id, chat_id=chat1.id)
            message2 = ChatMessage(content="Hello everyone!", user_id=user2.id, chat_id=chat1.id)
            message3 = ChatMessage(content="Project kickoff tomorrow", user_id=user1.id, chat_id=chat2.id)

            db.session.add_all([message1, message2, message3])
            db.session.commit()
            logger.info("Added sample messages")

            logger.info("Database initialized with sample data successfully")
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error initializing database: {e}")
            return False


if __name__ == "__main__":
    # Execute as standalone script
    from src.app import create_app

    app = create_app()
    success = initialize_db(app, db)
    sys.exit(0 if success else 1)
