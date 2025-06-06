from python_chat.app import create_app, socketio  # pragma: no cover

if __name__ == "__main__":
    app = create_app()
    app.logger.info("Starting Flask application")
    socketio.run(app, host="127.0.0.1", port=5000, debug=True)
