import pytest

from app import create_app, market
from app.models import Bank, User, db


@pytest.fixture
def app(tmp_path):
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'test.db'}",
        'WTF_CSRF_ENABLED': False,
        'FINNHUB_API_KEY': None,
        'MARKET_DATA_FALLBACK': 'simulated',
        'SECRET_KEY': 'test',
    })
    with app.app_context():
        db.create_all()
        db.session.add(Bank(name='Chase', url='https://www.chase.com'))
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def make_user(email='trader@example.com', password='hunter22', buying_power=0):
    user = User(first_name='Test', last_name='Trader', email=email,
                password=password, buying_power=buying_power)
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def user(app):
    return make_user(buying_power=1000)


@pytest.fixture
def other_user(app):
    return make_user(email='other@example.com', buying_power=500)


def login(client, email='trader@example.com', password='hunter22'):
    res = client.post('/api/auth/login', json={'email': email, 'password': password})
    assert res.status_code == 200, res.get_json()
    return res


@pytest.fixture
def logged_in(client, user):
    login(client)
    return client


@pytest.fixture
def fixed_price(monkeypatch):
    """Makes every quote come back at $10.00 so trade math is exact."""
    def quote(symbol):
        return {'current': 10.0, 'change': 0, 'change_percent': 0, 'open': 10.0,
                'previous_close': 10.0, 'high': 10.0, 'low': 10.0}
    monkeypatch.setattr(market, 'get_quote', quote)
