from app import app, db, socketio

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    socketio.run(app)

# Gunicorn and WSGI (Web Server Gateway Interface) are both components used in deploying and serving Python web applications, particularly those built with web frameworks like Flask and Django.
