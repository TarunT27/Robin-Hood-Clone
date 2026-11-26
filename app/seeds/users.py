from app.models import db, User
from .utils import clear_table

DEMO_EMAIL = 'demo@aa.io'


def demo_user_fields():
    return {
        'first_name': 'Demo',
        'last_name': 'User',
        'email': DEMO_EMAIL,
        'password': 'password',
        'buying_power': 100000,
    }


def seed_users():
    db.session.add(User(**demo_user_fields()))
    db.session.commit()


def undo_users():
    clear_table('users')
