from python_chat.database.models.user import User


class TestAuthRoutes:
    """Tests for authentication routes."""

    def test_login_page_loads(self, test_client):
        """Test if the login page loads correctly."""
        response = test_client.get("/login")
        assert response.status_code == 200
        assert b"Login" in response.data

    def test_register_page_loads(self, test_client):
        """Test if the register page loads correctly."""
        response = test_client.get("/register")
        assert response.status_code == 200
        assert b"Register" in response.data

    def test_login_success(self, test_client, user, session):
        """Test successful login."""
        response = test_client.post("/login", data={"username": "testuser", "password": "password123"}, follow_redirects=True)
        assert response.status_code == 200
        # Should redirect to index after successful
        assert b"Chat Selection" in response.data

    def test_login_invalid_credentials(self, test_client, user):
        """Test login with invalid credentials."""
        response = test_client.post("/login", data={"username": "testuser", "password": "wrongpassword"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Login failed" in response.data

    def test_login_nonexistent_user(self, test_client):
        """Test login with non-existent user."""
        response = test_client.post("/login", data={"username": "nonexistentuser", "password": "password123"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Login failed" in response.data

    def test_register_success(self, test_client, session):
        """Test successful user registration."""
        response = test_client.post("/register", data={"username": "newuser", "password": "password123", "confirm_password": "password123"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Your account has been created" in response.data

        # Verify the user was created in the database
        user = session.query(User).filter_by(username="newuser").first()
        assert user is not None

    def test_register_username_taken(self, test_client, user):
        """Test registration with an existing username."""
        response = test_client.post(
            "/register",
            data={
                "username": "testuser",  # Same as fixture user
                "password": "password123",
                "confirm_password": "password123",
            },
            follow_redirects=True,
        )
        assert response.status_code == 200
        assert b"Username already exists" in response.data or b"already taken" in response.data

    def test_register_password_mismatch(self, test_client):
        """Test registration with mismatched passwords."""
        response = test_client.post("/register", data={"username": "newuser", "password": "password123", "confirm_password": "differentpassword"}, follow_redirects=True)
        assert response.status_code == 200
        assert b"Passwords must match" in response.data or b"Field must be equal to" in response.data

    def test_logout(self, authenticated_client):
        """Test user logout."""
        response = authenticated_client.get("/logout", follow_redirects=True)
        assert response.status_code == 200
        assert b"Login" in response.data  # Should redirect to login page

    def test_authenticated_user_redirect(self, authenticated_client):
        """Test that authenticated users are redirected from login/register to index."""
        # Test login page redirect
        response = authenticated_client.get("/login")
        assert response.status_code == 302  # Redirect status

        # Test register page redirect
        response = authenticated_client.get("/register")
        assert response.status_code == 302  # Redirect status
