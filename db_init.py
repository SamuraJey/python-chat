from src.app import create_app
from src.database import db
from src.database.db_init import initialize_db

if __name__ == "__main__":
    app = create_app()
    success = initialize_db(app, db)
    print("Database initialization " + ("successful" if success else "failed"))  # noqa
