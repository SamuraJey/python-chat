from python_chat.app import create_app
from python_chat.database import db
from python_chat.database.db_init import initialize_db

if __name__ == "__main__":
    app = create_app()
    success = initialize_db(app, db)
    print("Database initialization " + ("successful" if success else "failed"))  # noqa
