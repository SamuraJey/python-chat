from collections.abc import Generator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_socketio import SocketIO, SocketIOTestClient
from sqlalchemy.orm import Session

from python_chat.database.models.chat import Chat
from python_chat.database.models.chat_member import ChatMember
from python_chat.database.models.chat_message import ChatMessage
from python_chat.database.models.user import User

# TODO To be honest, routes tests are not integration tests. (Even when they use db session)
# They are more like unit tests, because they test only one route at a time.
# Need to rearrange tests.


@pytest.fixture(scope="function")
def test_client(session: Session, app: Flask) -> Generator[FlaskClient, Any]:
    """Create a Flask test client for API tests."""
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for testing

    with app.test_client() as client, app.app_context():
        yield client


@pytest.fixture(scope="function")
def socket_client(session: Session, app: Flask) -> SocketIOTestClient:
    """Create a Socket.IO test client."""
    flask_test_client = app.test_client()
    socket_io = SocketIO(app)
    socket_test_client = socket_io.test_client(app, flask_test_client=flask_test_client)
    return socket_test_client


@pytest.fixture(scope="function")
def user(session: Session) -> User:
    """Create a test user."""
    user = User(username="testuser")
    user.set_password("password123")
    session.add(user)
    session.commit()
    return user


@pytest.fixture(scope="function")
def admin_user(session: Session) -> User:
    """Create an admin test user."""
    user = User(username="adminuser", is_admin=True)
    user.set_password("password123")
    session.add(user)
    session.commit()
    return user


@pytest.fixture(scope="function")
def authenticated_client(app: Flask, user: User) -> Generator[FlaskClient, Any]:
    """Create an authenticated test client."""
    with app.test_client() as client:
        with client.session_transaction() as sess:
            # Flask-Login's session key for storing user ID
            sess["_user_id"] = user.id
        yield client


@pytest.fixture(scope="function")
def chat(session: Session) -> Chat:
    """Create a test chat."""
    chat = Chat(name="Test Chat", is_group=True)
    session.add(chat)
    session.commit()
    return chat


@pytest.fixture(scope="function")
def chat_member(session: Session, user: User, chat: Chat) -> ChatMember:
    """Create a test chat membership."""
    chat_member = ChatMember(user_id=user.id, chat_id=chat.id)
    session.add(chat_member)
    session.commit()
    return chat_member


@pytest.fixture(scope="function")
def chat_message(session: Session, user: User, chat: Chat) -> ChatMessage:
    """Create a test message in chat."""
    message = ChatMessage(user_id=user.id, chat_id=chat.id, content="Test message")
    session.add(message)
    session.commit()
    return message
