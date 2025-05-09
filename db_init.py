from src.app import create_app  # pragma: no cover
from src.database import db  # pragma: no cover
from src.database.db_init import initialize_db  # pragma: no cover

if __name__ == "__main__":  # pragma: no cover
    app = create_app()
    success = initialize_db(app, db)
    print("Database initialization " + ("successful" if success else "failed"))  # noqa
