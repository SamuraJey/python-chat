from unittest.mock import MagicMock, patch

import pytest


# TODO Эти тесты не ГОТОВЫ и вообще неопнятно что я пытался сделать. Надо сделать хорошие тесты чуть попозже
@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    from src.app import create_app

    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SQLALCHEMY_TRACK_MODIFICATIONS": False,
            "WTF_CSRF_ENABLED": False,  # Disable CSRF for testing
            "SECRET_KEY": "test_secret_key",
        }
    )

    # Create application context
    with app.app_context():
        from src.database import db

        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def mock_db_session():
    """Mock the db.session to avoid actual database operations"""
    with patch("src.database.db.session") as mock_session:
        yield mock_session


@pytest.fixture
def mock_form():
    """Create a mock registration form"""
    mock = MagicMock()
    mock.username.data = "testuser"
    mock.password.data = "password123"
    mock.validate_on_submit.return_value = True
    return mock


@pytest.fixture
def authenticated_user():
    """Mock authenticated user"""
    user = MagicMock()
    user.is_authenticated = True
    user.username = "testuser"
    return user


def test_register_get(client):
    """Test GET request to /register returns the register template"""
    response = client.get("/register")
    assert response.status_code == 200
    # Check if the page contains the registration form
    assert b"Register" in response.data


def test_register_authenticated_user(client):
    """Test that authenticated users are redirected to index"""
    with patch("src.routes.auth.current_user") as mock_current_user:
        mock_current_user.is_authenticated = True
        response = client.get("/register")
        assert response.status_code == 302
        assert "index" in response.location


def test_register_post_success(client):
    """Test successful user registration"""
    with patch("src.routes.auth.RegistrationForm") as mock_form_class:
        mock_form = MagicMock()
        mock_form.username.data = "testuser"
        mock_form.password.data = "password123"
        mock_form.validate_on_submit.return_value = True
        mock_form_class.return_value = mock_form

        with patch("src.routes.auth.User") as mock_user_class:
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_user_class.return_value = mock_user

            with patch("src.routes.auth.db.session.add"), patch("src.routes.auth.db.session.commit"):
                response = client.post(
                    "/register",
                    data={"username": "testuser", "password": "password123", "confirm_password": "password123"},
                )

                # Check for redirect to login page
                assert response.status_code == 302
                assert "login" in response.location


def test_register_form_validation_error(client):
    """Test form validation error handling"""
    with patch("src.routes.auth.RegistrationForm") as mock_form_class:
        mock_form = MagicMock()
        mock_form.validate_on_submit.return_value = False
        mock_form.errors = {"username": ["Username already exists."]}
        mock_form_class.return_value = mock_form

        response = client.post("/register", data={"username": "existinguser", "password": "password123"})

        # Check that we stayed on the registration page
        assert response.status_code == 200


def test_register_database_error(client):
    """Test database exception handling during registration"""
    with patch("src.routes.auth.RegistrationForm") as mock_form_class:
        mock_form = MagicMock()
        mock_form.username.data = "testuser"
        mock_form.password.data = "password123"
        mock_form.validate_on_submit.return_value = True
        mock_form_class.return_value = mock_form

        with patch("src.routes.auth.User") as mock_user_class:
            mock_user = MagicMock()
            mock_user_class.return_value = mock_user

            # Simulate database error
            with (
                patch("src.routes.auth.db.session.add"),
                patch("src.routes.auth.db.session.commit", side_effect=Exception("Database error")),
                patch("src.routes.auth.db.session.rollback") as mock_rollback,
            ):
                response = client.post(
                    "/register",
                    data={"username": "testuser", "password": "password123", "confirm_password": "password123"},
                )

                # Verify rollback was called
                mock_rollback.assert_called_once()
                # Check we stayed on registration page
                assert response.status_code == 200


def test_register_flash_message_on_success(client):
    """Test that a success flash message is shown after successful registration"""
    with patch("src.routes.auth.RegistrationForm") as mock_form_class:
        mock_form = MagicMock()
        mock_form.username.data = "testuser"
        mock_form.password.data = "password123"
        mock_form.validate_on_submit.return_value = True
        mock_form_class.return_value = mock_form

        with patch("src.routes.auth.User") as mock_user_class:
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_user_class.return_value = mock_user

            with (
                patch("src.routes.auth.db.session.add"),
                patch("src.routes.auth.db.session.commit"),
                patch("src.routes.auth.flash") as mock_flash,
            ):
                client.post("/register", data={"username": "testuser", "password": "password123"})

                # Check that flash was called with success message
                mock_flash.assert_called_with("Your account has been created! You can now login.", "success")


def test_login_get(client):
    """Test GET request to /login returns the login template"""
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Login" in response.data


def test_login_authenticated_user(client):
    """Test that authenticated users are redirected to index"""
    with patch("src.routes.auth.current_user") as mock_current_user:
        mock_current_user.is_authenticated = True
        response = client.get("/login")
        assert response.status_code == 302
        assert "index" in response.location


def test_login_success(client):
    """Test successful login"""
    with patch("src.routes.auth.LoginForm") as mock_form_class:
        mock_form = MagicMock()
        mock_form.username.data = "testuser"
        mock_form.password.data = "password123"
        mock_form.remember.data = True
        mock_form.validate_on_submit.return_value = True
        mock_form_class.return_value = mock_form

        with patch("src.routes.auth.User.query") as mock_query:
            mock_user = MagicMock()
            mock_user.username = "testuser"
            mock_user.check_password.return_value = True
            mock_query.filter_by.return_value.first.return_value = mock_user

            with patch("src.routes.auth.login_user") as mock_login:
                response = client.post(
                    "/login", data={"username": "testuser", "password": "password123", "remember": True}
                )

                # Check that login_user was called
                mock_login.assert_called_once_with(mock_user, remember=True)

                # Check for redirect to index page
                assert response.status_code == 302
                assert "index" in response.location


def test_login_invalid_credentials(client):
    """Test login with invalid credentials"""
    with patch("src.routes.auth.LoginForm") as mock_form_class:
        mock_form = MagicMock()
        mock_form.username.data = "testuser"
        mock_form.password.data = "wrongpassword"
        mock_form.validate_on_submit.return_value = True
        mock_form_class.return_value = mock_form

        with patch("src.routes.auth.User.query") as mock_query:
            # User exists but password check fails
            mock_user = MagicMock()
            mock_user.check_password.return_value = False
            mock_query.filter_by.return_value.first.return_value = mock_user

            with patch("src.routes.auth.flash") as mock_flash:
                response = client.post("/login", data={"username": "testuser", "password": "wrongpassword"})

                # Check that flash was called with error message
                mock_flash.assert_called_with("Login failed. Please check your username and password.", "error")

                # Check we stayed on login page
                assert response.status_code == 200


def test_logout(client):
    """Test logout functionality"""
    with patch("src.routes.auth.current_user") as mock_current_user:
        mock_current_user.is_authenticated = True
        mock_current_user.username = "testuser"

        with patch("src.routes.auth.logout_user") as mock_logout:
            response = client.get("/logout")

            # Check that logout_user was called
            mock_logout.assert_called_once()

            # Check for redirect to login page
            assert response.status_code == 302
            assert "login" in response.location
