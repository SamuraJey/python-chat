import logging
import os

from flask import Flask, flash, redirect, render_template, request, url_for
from flask_login import LoginManager, current_user, login_user, logout_user
from flask_socketio import SocketIO, emit

from forms import LoginForm, RegistrationForm
from models import User, db

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key-here")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize extensions
socketio = SocketIO(app)
db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# Create tables
with app.app_context():
    try:
        db.create_all()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")

# Store connected users. Key is socket id, value is username and avatarUrl
users = {}


@login_manager.user_loader
def load_user(user_id):
    try:
        user = User.query.get(int(user_id))
        logger.debug(f"Loading user {user_id}: {'Found' if user else 'Not found'}")
        return user
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None


@app.route("/")
def index():
    print("Index route accessed")
    logger.info(f"Index route accessed. Authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        return render_template("index.html")
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    logger.debug(f"Register route accessed. Method: {request.method}")
    if current_user.is_authenticated:
        logger.debug("Authenticated user accessing register page, redirecting to index")
        return redirect(url_for("index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        logger.info(f"Registering new user: {form.username.data}")
        try:
            user = User(username=form.username.data)
            user.set_password(form.password.data)

            db.session.add(user)
            db.session.commit()

            flash("Your account has been created! You can now login.", "success")
            logger.info(f"User {user.username} registered successfully")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            flash("An error occurred during registration. Please try again.", "error")

    for field, errors in form.errors.items():
        for error in errors:
            logger.warning(f"Form validation error in {field}: {error}")

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    logger.debug(f"Login route accessed. Method: {request.method}")
    if current_user.is_authenticated:
        logger.debug("Authenticated user accessing login page, redirecting to index")
        return redirect(url_for("index"))

    form = LoginForm()
    if form.validate_on_submit():
        logger.debug(f"Login attempt for user: {form.username.data}")
        try:
            user = User.query.filter_by(username=form.username.data).first()

            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                logger.info(f"User {user.username} logged in successfully")
                return redirect(url_for("index"))
            else:
                logger.warning(f"Failed login attempt for user: {form.username.data}")
                flash("Login failed. Please check your username and password.", "error")
        except Exception as e:
            logger.error(f"Error during login: {e}")
            flash("An error occurred during login. Please try again.", "error")

    for field, errors in form.errors.items():
        for error in errors:
            logger.warning(f"Form validation error in {field}: {error}")

    return render_template("login.html", form=form)


@app.route("/logout")
def logout():
    logger.debug(f"Logout route accessed by: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    logout_user()
    return redirect(url_for("login"))


# Socket.IO event handlers
@socketio.on("connect")
def handle_connect():
    logger.debug(f"Socket connection attempt. Authenticated: {current_user.is_authenticated}")
    if not current_user.is_authenticated:
        logger.warning("Unauthenticated socket connection attempt rejected")
        return False

    username = current_user.username

    users[request.sid] = {"username": username}

    logger.info(f"User {username} connected with socket ID {request.sid}")
    emit("user_joined", {"username": username}, broadcast=True)
    emit("set_username", {"username": username})


@socketio.on("disconnect")
def handle_disconnect():
    user = users.pop(request.sid, None)
    if user:
        logger.info(f"User {user['username']} disconnected from socket ID {request.sid}")
        emit("user_left", {"username": user["username"]}, broadcast=True)


@socketio.on("send_message")
def handle_message(data):
    user = users.get(request.sid)
    if user:
        logger.debug(f"Message from {user['username']}: {data.get('message', '')[:20]}...")
        try:
            avatar = user.get("avatar", "default-avatar")
            emit(
                "new_message",
                {"username": user["username"], "avatar": avatar, "message": data["message"]},
                broadcast=True,
            )
        except Exception as e:
            logger.error(f"Error sending message: {e}")


@socketio.on("update_username")
def handle_update_username(data):
    try:
        old_username = users[request.sid]["username"]
        new_username = data["username"]

        logger.info(f"Username update requested: {old_username} → {new_username}")

        # Check if username already exists in database
        existing_user = User.query.filter_by(username=new_username).first()
        if existing_user and existing_user.id != current_user.id:
            logger.warning(f"Username update rejected: {new_username} already exists")
            emit("username_error", {"error": "Username already taken"})
            return

        # Update database
        current_user.username = new_username
        db.session.commit()

        # Update in-memory users dict
        users[request.sid]["username"] = new_username

        logger.info(f"Username updated successfully: {old_username} → {new_username}")
        emit("username_updated", {"old_username": old_username, "new_username": new_username}, broadcast=True)
    except Exception as e:
        logger.error(f"Error updating username: {e}")
        emit("username_error", {"error": "An error occurred while updating username"})


# Custom error handlers
@app.errorhandler(404)
def page_not_found(e):
    logger.error(f"404 error: {request.url}")
    return render_template("404.html"), 404


@app.errorhandler(500)
def internal_server_error(e):
    logger.error(f"500 error: {str(e)}")
    return render_template("500.html"), 500


print("Registered routes:")
for rule in app.url_map.iter_rules():
    print(f"{rule.endpoint}: {rule}")

if __name__ == "__main__":
    logger.info("Starting Flask application")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
