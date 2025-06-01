import json
from collections.abc import Generator
from typing import Any

import pytest
from flask import Flask
from flask.testing import FlaskClient
from sqlalchemy.orm import Session

from python_chat.database.models.chat import Chat
from python_chat.database.models.chat_message import ChatMessage
from python_chat.database.models.user import User


class TestAdminRoutes:
    """Tests for admin routes."""

    @pytest.fixture
    def admin_authenticated_client(self, app: Flask, admin_user: User) -> Generator[FlaskClient, Any]:
        """Create a test client authenticated with admin privileges."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess["_user_id"] = admin_user.id
            yield client

    def test_admin_dashboard_authorized(self, admin_authenticated_client: FlaskClient) -> None:
        """Test that admin users can access the admin dashboard."""
        response = admin_authenticated_client.get("/admin/dashboard")
        assert response.status_code == 200
        assert b"dashboard" in response.data.lower()

    def test_admin_dashboard_unauthorized(self, authenticated_client: FlaskClient) -> None:
        """Test that regular users cannot access the admin dashboard."""
        response = authenticated_client.get("/admin/dashboard")
        assert response.status_code == 403

    def test_admin_dashboard_unauthenticated(self, test_client: FlaskClient) -> None:
        """Test that unauthenticated users cannot access the admin dashboard."""
        response = test_client.get("/admin/dashboard")
        # Redirect to login page
        assert response.status_code == 302
        assert "/login" in response.location

    def test_analytics_overview_authorized(self, admin_authenticated_client: FlaskClient, session: Session, user: User, chat: Chat) -> None:
        """Test that admin users can get analytics overview data."""
        # Create some test data
        message = ChatMessage(user_id=user.id, chat_id=chat.id, content="Test message")
        session.add(message)
        session.commit()

        response = admin_authenticated_client.get("/api/analytics/overview")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "total_users" in data
        assert "total_chats" in data
        assert "total_messages" in data
        assert "active_users" in data
        assert "messages_today" in data

        # Verify counts match our test data
        assert data["total_users"] >= 2  # At least the admin and the test user
        assert data["total_chats"] >= 1  # At least the test chat
        assert data["total_messages"] >= 1  # At least the test message

    def test_analytics_overview_empty_data(self, admin_authenticated_client: FlaskClient, session: Session) -> None:
        """Test analytics overview with no data in database."""
        # Clear any existing messages
        session.query(ChatMessage).delete()
        session.commit()

        response = admin_authenticated_client.get("/api/analytics/overview")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "total_messages" in data
        assert data["total_messages"] == 0
        assert data["active_users"] == 0
        assert data["messages_today"] == 0

    def test_analytics_overview_unauthorized(self, authenticated_client: FlaskClient) -> None:
        """Test that regular users cannot get analytics overview data."""
        response = authenticated_client.get("/api/analytics/overview")
        assert response.status_code == 403

    def test_analytics_overview_unauthenticated(self, test_client: FlaskClient) -> None:
        """Test that unauthenticated users cannot get analytics overview data."""
        response = test_client.get("/api/analytics/overview")
        # Should redirect to login page
        assert response.status_code == 302
        assert "/login" in response.location

    def test_chat_activity_authorized(self, admin_authenticated_client: FlaskClient, session: Session, user: User, chat: Chat) -> None:
        """Test that admin users can get chat activity data."""
        # Create some test data
        message = ChatMessage(user_id=user.id, chat_id=chat.id, content="Test chat activity")
        session.add(message)
        session.commit()

        response = admin_authenticated_client.get("/api/analytics/chat-activity")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "labels" in data
        assert "datasets" in data
        assert len(data["datasets"]) > 0
        assert "label" in data["datasets"][0]
        assert "data" in data["datasets"][0]
        assert chat.name in data["labels"]

    def test_chat_activity_empty_data(self, admin_authenticated_client: FlaskClient, session: Session) -> None:
        """Test chat activity with no messages in database."""
        # Clear any existing messages
        session.query(ChatMessage).delete()
        session.commit()

        response = admin_authenticated_client.get("/api/analytics/chat-activity")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "labels" in data
        assert "datasets" in data
        assert len(data["labels"]) == 0  # No chat activity
        assert len(data["datasets"][0]["data"]) == 0  # No data points

    def test_chat_activity_unauthorized(self, authenticated_client: FlaskClient) -> None:
        """Test that regular users cannot get chat activity data."""
        response = authenticated_client.get("/api/analytics/chat-activity")
        assert response.status_code == 403

    def test_chat_activity_unauthenticated(self, test_client: FlaskClient) -> None:
        """Test that unauthenticated users cannot get chat activity data."""
        response = test_client.get("/api/analytics/chat-activity")
        # Should redirect to login page
        assert response.status_code == 302
        assert "/login" in response.location

    def test_user_activity_authorized(self, admin_authenticated_client: FlaskClient, session: Session, user: User, chat: Chat) -> None:
        """Test that admin users can get user activity data."""
        # Create some test data
        message = ChatMessage(user_id=user.id, chat_id=chat.id, content="Test user activity")
        session.add(message)
        session.commit()

        response = admin_authenticated_client.get("/api/analytics/user-activity")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "labels" in data
        assert "datasets" in data
        assert len(data["datasets"]) > 0
        assert "label" in data["datasets"][0]
        assert "data" in data["datasets"][0]
        assert len(data["labels"]) == 7  # 7 days of data
        assert len(data["datasets"][0]["data"]) == 7  # Data for 7 days

    def test_user_activity_empty_data(self, admin_authenticated_client: FlaskClient, session: Session) -> None:
        """Test user activity with no messages in database."""
        # Clear any existing messages
        session.query(ChatMessage).delete()
        session.commit()

        response = admin_authenticated_client.get("/api/analytics/user-activity")
        assert response.status_code == 200

        data = json.loads(response.data)
        assert "labels" in data
        assert "datasets" in data
        assert len(data["labels"]) == 7  # Still has 7 days
        # All days should have 0 messages
        assert all(count == 0 for count in data["datasets"][0]["data"])

    def test_user_activity_unauthorized(self, authenticated_client: FlaskClient) -> None:
        """Test that regular users cannot get user activity data."""
        response = authenticated_client.get("/api/analytics/user-activity")
        assert response.status_code == 403

    def test_user_activity_unauthenticated(self, test_client: FlaskClient) -> None:
        """Test that unauthenticated users cannot get user activity data."""
        response = test_client.get("/api/analytics/user-activity")
        # Should redirect to login page
        assert response.status_code == 302
        assert "/login" in response.location

    def test_admin_required_decorator(self, authenticated_client: FlaskClient) -> None:
        """Test that the admin_required decorator blocks non-admin users from all admin routes."""
        # Test all admin endpoints
        admin_endpoints = ["/admin/dashboard", "/api/analytics/overview", "/api/analytics/chat-activity", "/api/analytics/user-activity"]

        for endpoint in admin_endpoints:
            response = authenticated_client.get(endpoint)
            assert response.status_code == 403
