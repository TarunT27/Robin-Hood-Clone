from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

from sqlalchemy import func

from app.models import User


def strip(value):
    return value.strip() if isinstance(value, str) else value


def email_free(form, field):
    email = (field.data or '').strip().lower()
    if User.query.filter(func.lower(User.email) == email).first():
        raise ValidationError('Email address is already in use.')


class SignUpForm(FlaskForm):
    first_name = StringField('first_name', filters=[strip], validators=[
        DataRequired(), Length(max=50)])
    last_name = StringField('last_name', filters=[strip], validators=[
        DataRequired(), Length(max=50)])
    email = StringField('email', filters=[strip], validators=[
        DataRequired(), Length(max=255),
        Regexp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$',
               message='Please enter a valid email address.'),
        email_free])
    password = StringField('password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long.')])
