from flask import Blueprint
from flask_login import current_user, login_user, logout_user
from sqlalchemy import func

from app.api.utils import bound_form, validation_errors_to_error_messages
from app.forms import LoginForm, SignUpForm
from app.models import User, db
from app.seeds.users import DEMO_EMAIL, demo_user_fields

auth_routes = Blueprint('auth', __name__)


@auth_routes.route('/')
def authenticate():
    """
    Authenticates a user.
    """
    if current_user.is_authenticated:
        return current_user.to_safe_dict()
    return {'errors': ['Unauthorized']}, 401


@auth_routes.route('/login', methods=['POST'])
def login():
    """
    Logs a user in
    """
    form = bound_form(LoginForm)
    if form.validate_on_submit():
        email = form.data['email'].strip().lower()
        user = User.query.filter(func.lower(User.email) == email).first()
        login_user(user)
        return user.to_safe_dict()
    return {'errors': validation_errors_to_error_messages(form.errors)}, 401


@auth_routes.route('/demo', methods=['POST'])
def demo():
    """
    Logs in as demo user
    """
    user = User.query.filter(User.email == DEMO_EMAIL).first()
    if not user:
        # Recreate the demo account if the database wasn't seeded.
        user = User(**demo_user_fields())
        db.session.add(user)
        db.session.commit()
    login_user(user)
    return user.to_safe_dict()


@auth_routes.route('/logout', methods=['POST'])
def logout():
    """
    Logs a user out
    """
    logout_user()
    return {'message': 'User logged out'}


@auth_routes.route('/signup', methods=['POST'])
def sign_up():
    """
    Creates a new user and logs them in
    """
    form = bound_form(SignUpForm)
    if form.validate_on_submit():
        user = User(
            first_name=form.data['first_name'].strip(),
            last_name=form.data['last_name'].strip(),
            email=form.data['email'].strip().lower(),
            password=form.data['password']
        )
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return user.to_safe_dict()
    return {'errors': validation_errors_to_error_messages(form.errors)}, 401


@auth_routes.route('/unauthorized')
def unauthorized():
    """
    Returns unauthorized JSON when flask-login authentication fails
    """
    return {'errors': ['Unauthorized']}, 401
