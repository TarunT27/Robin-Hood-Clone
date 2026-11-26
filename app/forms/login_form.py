from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, ValidationError

from sqlalchemy import func

from app.models import User


def credentials_match(form, field):
    # One message for a wrong email or a wrong password, so the form
    # doesn't reveal which emails have accounts.
    email = (form.data['email'] or '').strip().lower()
    user = User.query.filter(func.lower(User.email) == email).first()
    if not user or not user.check_password(field.data or ''):
        raise ValidationError('Invalid email or password.')


class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = StringField('password', validators=[
                           DataRequired(), credentials_match])
