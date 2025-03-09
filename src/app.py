import os

from flask import Flask, render_template, request
from flask_login import LoginManager
from flask_socketio import SocketIO

from src.database import db
from src.database.models.user import User
from src.utils.logger import setup_logger

# Create SocketIO instance
socketio = SocketIO()


def create_app(test_config=None) -> Flask:
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Load config
    if test_config is None:
        app.config.from_mapping(
            SECRET_KEY=os.environ.get("SECRET_KEY", "dev"),
            SQLALCHEMY_DATABASE_URI=os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost"),
            SQLALCHEMY_TRACK_MODIFICATIONS=False,
        )
    else:
        app.config.from_mapping(test_config)

    # Initialize extensions
    db.init_app(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Setup login manager
    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        try:
            user = User.query.get(int(user_id))
            return user
        except Exception as e:
            app.logger.error(f"Error loading user {user_id}: {e}")
            return None

    # Setup logger
    logger = setup_logger(app)

    # Initialize database
    with app.app_context():
        db.create_all()
        app.logger.info("Database tables created successfully")

    # Register blueprints
    from src.routes import auth, chats, index

    app.register_blueprint(auth.bp)
    app.register_blueprint(index.bp)
    app.register_blueprint(chats.bp)

    # Initialize Socket.IO event handlers
    with app.app_context():
        from src.routes.events import init_socketio

        init_socketio(socketio)

    # Register error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        app.logger.error(f"404 error: {request.url}")
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"500 error: {str(e)}")
        return render_template("500.html"), 500

    # Log registered routes
    app.logger.debug("Registered routes:")
    for rule in app.url_map.iter_rules():
        app.logger.debug(f"{rule.endpoint}: {rule}")

    return app
