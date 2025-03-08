import logging
from models import User, Chat, ChatMember

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def initialize_db(app, db):
    with app.app_context():
        try:
            # Drop all tables and recreate them
            db.drop_all()
            db.create_all()

            # Create sample users
            user1 = User(username="ali")
            user1.set_password("aaaaaaaa")
            user2 = User(username="bob")
            user2.set_password("bbbbbbbb")
            user3 = User(username="caly")
            user3.set_password("cccccccc")

            db.session.add_all([user1, user2, user3])
            db.session.commit()

            # Create sample chats
            chat1 = Chat(name="General Chat")
            chat2 = Chat(name="Project Discussion")

            db.session.add_all([chat1, chat2])
            db.session.commit()

            # Add users to chats
            chat_member1 = ChatMember(user_id=user1.id, chat_id=chat1.id)
            chat_member2 = ChatMember(user_id=user2.id, chat_id=chat1.id)
            chat_member3 = ChatMember(user_id=user3.id, chat_id=chat1.id)
            chat_member4 = ChatMember(user_id=user1.id, chat_id=chat2.id)
            chat_member5 = ChatMember(user_id=user2.id, chat_id=chat2.id)

            db.session.add_all([chat_member1, chat_member2, chat_member3, chat_member4, chat_member5])
            db.session.commit()

            logger.info("Database initialized with sample data successfully")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error initializing database: {e}")
