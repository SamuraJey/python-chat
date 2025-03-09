from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user

from src.database import db
from src.database.models.user import User
from src.forms.auth import LoginForm, RegistrationForm

bp = Blueprint("auth", __name__)


@bp.route("/login", methods=["GET", "POST"])
def login():
    logger = current_app.logger
    logger.debug(f"Login route accessed. Method: {request.method}")
    if current_user.is_authenticated:
        current_app.logger.debug("Authenticated user accessing login page, redirecting to index")
        return redirect(url_for("index.index"))

    form = LoginForm()
    if form.validate_on_submit():
        logger.debug(f"Login attempt for user: {form.username.data}")
        try:
            user = User.query.filter_by(username=form.username.data).first()

            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember.data)
                logger.info(f"User {user.username} logged in successfully")
                return redirect(url_for("index.index"))
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


@bp.route("/register", methods=["GET", "POST"])
def register():
    logger = current_app.logger
    logger.debug(f"Register route accessed. Method: {request.method}")
    if current_user.is_authenticated:
        logger.debug("Authenticated user accessing register page, redirecting to index")
        return redirect(url_for("index.index"))

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
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering user: {e}")
            flash("An error occurred during registration. Please try again.", "error")

    for field, errors in form.errors.items():
        for error in errors:
            logger.warning(f"Form validation error in {field}: {error}")

    return render_template("register.html", form=form)


@bp.route("/logout")
def logout():
    logger = current_app.logger
    logger.debug(f"Logout route accessed by: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    logout_user()
    return redirect(url_for("auth.login"))
