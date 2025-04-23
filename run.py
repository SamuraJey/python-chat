from src.app import create_app, socketio

if __name__ == "__main__":
    app = create_app()
    app.logger.info("Starting Flask application")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
