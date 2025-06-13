from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from python_chat.database import db
from python_chat.database.models.user import User


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember Me")
    submit = SubmitField("Login")


class RegistrationForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=64)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=3)])
    confirm_password = PasswordField("Confirm Password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Register")

    def validate_username(self, username):
        user = db.session.query(User).filter_by(username=username.data).first()
        if user:
            raise ValidationError("Username is already taken. Please choose a different one.")


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField("Текущий пароль", validators=[DataRequired()])
    new_password = PasswordField("Новый пароль", validators=[DataRequired(), Length(min=3, message="Пароль должен содержать минимум 3 символа")])
    confirm_password = PasswordField("Подтвердите новый пароль", validators=[DataRequired(), EqualTo("new_password", message="Пароли должны совпадать")])
    submit = SubmitField("Изменить пароль")
