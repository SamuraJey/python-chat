from collections.abc import Generator
from typing import Any

import pytest
from flask.app import Flask
from sqlalchemy.orm import scoped_session, sessionmaker
from testcontainers.postgres import PostgresContainer

from src.app import create_app
from src.database import db

# Add the project root directory to Python path
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, Any]:
    """Provide a PostgreSQL container for testing."""
    with PostgresContainer("postgres:17-alpine") as postgres:
        yield postgres


@pytest.fixture(scope="session")
def app(postgres_container) -> Generator[Flask, Any]:
    """Create a Flask application for testing."""
    # Create a test app with the container's connection URL
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": postgres_container.get_connection_url(), "SQLALCHEMY_TRACK_MODIFICATIONS": False, "SECRET_KEY": "test_secret_key"})

    # Create tables
    with app.app_context():
        db.create_all()

    yield app

    # Clean up after tests
    with app.app_context():
        db.drop_all()


@pytest.fixture(scope="function")
def session(app) -> Generator[scoped_session, Any]:
    """Create a new database session for a test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()

        # Create a session bound to the connection
        session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=connection))

        # Set the session for the app
        db.session = session

        yield session

        # Clean up
        session.close()
        transaction.rollback()
        connection.close()
