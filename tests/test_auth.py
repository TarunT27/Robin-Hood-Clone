from app.models import User
from app.seeds.users import DEMO_EMAIL
from conftest import login


def test_signup_logs_in_and_normalises_email(client):
    res = client.post('/api/auth/signup', json={
        'first_name': 'Ada', 'last_name': 'Lovelace',
        'email': '  Ada@Example.com ', 'password': 'secret1'})
    assert res.status_code == 200
    assert res.get_json()['email'] == 'ada@example.com'
    assert client.get('/api/auth/').status_code == 200


def test_signup_rejects_duplicate_email_any_case(client, user):
    res = client.post('/api/auth/signup', json={
        'first_name': 'A', 'last_name': 'B',
        'email': 'TRADER@example.com', 'password': 'secret1'})
    assert res.status_code == 401
    assert any('already in use' in e for e in res.get_json()['errors'])


def test_signup_validates_email_and_password(client):
    res = client.post('/api/auth/signup', json={
        'first_name': 'A', 'last_name': 'B', 'email': 'nope', 'password': '123'})
    errors = ' '.join(res.get_json()['errors'])
    assert res.status_code == 401
    assert 'valid email' in errors
    assert 'at least 6' in errors


def test_login_does_not_reveal_which_part_was_wrong(client, user):
    wrong_password = client.post('/api/auth/login', json={
        'email': 'trader@example.com', 'password': 'nope'})
    unknown_email = client.post('/api/auth/login', json={
        'email': 'nobody@example.com', 'password': 'nope'})
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.get_json() == unknown_email.get_json()


def test_login_and_logout(client, user):
    login(client)
    assert client.get('/api/auth/').get_json()['email'] == 'trader@example.com'
    client.post('/api/auth/logout')
    assert client.get('/api/auth/').status_code == 401


def test_demo_login_works_without_seed_data(client, app):
    res = client.post('/api/auth/demo')
    assert res.status_code == 200
    assert res.get_json()['email'] == DEMO_EMAIL
    assert User.query.filter_by(email=DEMO_EMAIL).count() == 1
    # A second demo login reuses the same account.
    client.post('/api/auth/demo')
    assert User.query.filter_by(email=DEMO_EMAIL).count() == 1


def test_protected_routes_return_json_401(client):
    res = client.get('/api/portfolio/')
    assert res.status_code == 401
    assert res.get_json() == {'errors': ['Unauthorized']}
