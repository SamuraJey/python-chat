from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_user, logout_user

from python_chat.database import db
from python_chat.database.models.user import User

bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")


@bp.route("/login", methods=["POST"])
def login():
    logger = current_app.logger
    logger.debug("API login route accessed")

    # Log all headers for debugging
    headers = {key: value for key, value in request.headers.items()}
    logger.debug(f"Login request headers: {headers}")

    if current_user.is_authenticated:
        return jsonify({"success": True, "message": "Already logged in", "username": current_user.username})

    # Try to get data from various sources - JSON, form, or direct params
    if request.is_json:
        data = request.get_json()
        logger.debug("Request contains JSON data")
    elif request.form:
        data = request.form
        logger.debug("Request contains form data")
    else:
        data = request.values  # Combined args and form
        logger.debug("Using request values")

    if not data:
        logger.warning("Login attempt with no usable data")
        return jsonify({"success": False, "error": "No data provided"}), 400

    username = data.get("username")
    password = data.get("password")
    remember = data.get("remember", False)

    # Convert remember to boolean if it comes as string
    if isinstance(remember, str):
        remember = remember.lower() in ("true", "t", "yes", "y", "1")

    # Log request data for debugging (excluding passwords)
    logger.debug(f"Login API request: username={username}, has_password={'Yes' if password else 'No'}, remember={remember}")

    if not username or not password:
        logger.warning("Login attempt with missing username or password")
        return jsonify({"success": False, "error": "Username and password are required"}), 400

    try:
        user = db.session.query(User).filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            logger.info(f"User {user.username} logged in successfully via API")
            return jsonify({"success": True, "message": "Login successful", "username": user.username})
        else:
            logger.warning(f"Failed API login attempt for user: {username}")
            return jsonify({"success": False, "error": "Invalid username or password"}), 401
    except Exception as e:
        logger.error(f"Error during API login: {e}")
        return jsonify({"success": False, "error": "An error occurred during login"}), 500


@bp.route("/register", methods=["POST"])
def register():
    logger = current_app.logger
    logger.debug("API register route accessed")

    # Log all headers for debugging
    headers = {key: value for key, value in request.headers.items()}
    logger.debug(f"Register request headers: {headers}")

    if current_user.is_authenticated:
        return jsonify({"success": False, "error": "Already logged in"}), 400

    # Try to get data from various sources - JSON, form, or direct params
    if request.is_json:
        data = request.get_json()
        logger.debug("Register request contains JSON data")
    elif request.form:
        data = request.form
        logger.debug("Register request contains form data")
    else:
        data = request.values  # Combined args and form
        logger.debug("Using request values for registration")

    if not data:
        logger.warning("Registration attempt with no usable data")
        return jsonify({"success": False, "error": "No data provided"}), 400

    username = data.get("username")
    password = data.get("password")
    # Accept either password2 or confirm_password
    password2 = data.get("password2") or data.get("confirm_password")

    # Log request data for debugging (excluding passwords)
    logger.debug(f"Register API request: username={username}, has_password={'Yes' if password else 'No'}, has_confirm_password={'Yes' if password2 else 'No'}")

    if not username or not password or not password2:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    if password != password2:
        return jsonify({"success": False, "error": "Passwords do not match"}), 400

    try:
        # Check if username already exists
        existing_user = db.session.query(User).filter_by(username=username).first()
        if existing_user:
            return jsonify({"success": False, "error": "Username already exists"}), 400

        # Create new user
        user = User(username=username)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        logger.info(f"User {username} registered successfully via API")
        return jsonify({"success": True, "message": "Registration successful"})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error during API registration: {e}")
        return jsonify({"success": False, "error": "An error occurred during registration"}), 500


@bp.route("/logout", methods=["POST"])
def logout():
    logger = current_app.logger
    logger.debug(f"API logout route accessed by: {current_user.username if current_user.is_authenticated else 'Anonymous'}")

    if current_user.is_authenticated:
        logout_user()
        return jsonify({"success": True, "message": "Logout successful"})
    else:
        return jsonify({"success": False, "error": "Not logged in"}), 401


@bp.route("/status", methods=["GET"])
def status():
    """Check if user is authenticated and return user info"""
    if current_user.is_authenticated:
        return jsonify({"isAuthenticated": True, "username": current_user.username, "userId": current_user.id, "is_admin": current_user.is_admin})
    else:
        return jsonify({"isAuthenticated": False}), 401
