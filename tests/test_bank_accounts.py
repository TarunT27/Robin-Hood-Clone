from decimal import Decimal

from app.models import BankAccount, User, db
from conftest import login


def add_account(client, number='1234567890', **extra):
    return client.post('/api/portfolio/bank-accounts/add', json={
        'bank_id': 1, 'account_number': number, 'name': 'Checking', **extra})


def deposit(client, amount):
    return client.put('/api/portfolio/buying-power/add', json={'buying_power': amount})


def test_link_account_uses_logged_in_user(logged_in, user, other_user):
    res = add_account(logged_in, user_id=other_user.id)
    assert res.status_code == 200
    assert res.get_json()['user_id'] == user.id
    assert res.get_json()['bank_name'] == 'Chase'


def test_account_validation(logged_in):
    assert add_account(logged_in, number='123').status_code == 400
    assert add_account(logged_in, number='abcdefghij').status_code == 400
    assert logged_in.post('/api/portfolio/bank-accounts/add', json={
        'bank_id': 99, 'account_number': '1234567890', 'name': 'Checking'}).status_code == 400
    add_account(logged_in)
    assert add_account(logged_in).status_code == 400  # number already used


def test_edit_keeps_own_number(logged_in):
    acct = add_account(logged_in).get_json()
    res = logged_in.put(f"/api/portfolio/bank-accounts/edit/{acct['id']}", json={
        'bank_id': 1, 'account_number': '1234567890', 'name': 'Savings'})
    assert res.status_code == 200
    assert res.get_json()['name'] == 'Savings'


def test_cannot_change_someone_elses_account(client, user, other_user):
    theirs = BankAccount(user_id=other_user.id, bank_id=1, name='Theirs',
                         account_number='5555555555')
    db.session.add(theirs)
    db.session.commit()
    login(client)
    assert client.delete(f'/api/portfolio/bank-accounts/delete/{theirs.id}').status_code == 404
    res = client.put(f'/api/portfolio/bank-accounts/edit/{theirs.id}', json={
        'bank_id': 1, 'account_number': '5555555555', 'name': 'Mine now'})
    assert res.status_code == 404
    assert db.session.get(BankAccount, theirs.id).user_id == other_user.id


def test_listing_only_shows_own_accounts(logged_in, other_user):
    db.session.add(BankAccount(user_id=other_user.id, bank_id=1, name='Theirs',
                               account_number='5555555555'))
    db.session.commit()
    add_account(logged_in)
    accounts = logged_in.get('/api/portfolio/bank-accounts/').get_json()
    assert [a['name'] for a in accounts.values()] == ['Checking']


def test_deposit_needs_a_linked_account(logged_in, user):
    res = deposit(logged_in, 100)
    assert res.status_code == 400
    assert 'Link a bank account' in res.get_json()['errors'][0]


def test_deposit(logged_in, user):
    add_account(logged_in)
    res = deposit(logged_in, 250)
    assert res.status_code == 200
    assert Decimal(res.get_data(as_text=True)) == Decimal('1250.00')
    assert Decimal(db.session.get(User, user.id).buying_power) == Decimal('1250.00')


def test_deposit_limits(logged_in, user):
    add_account(logged_in)
    assert deposit(logged_in, 0).status_code == 400
    assert deposit(logged_in, -50).status_code == 400
    assert deposit(logged_in, 1_000_001).status_code == 400


def test_old_withdraw_endpoint_is_gone(logged_in):
    # Buying power used to be spendable by anyone calling this directly.
    res = logged_in.put('/api/portfolio/buying-power/subtract', json={'buying_power': 5})
    assert res.status_code in (404, 405)
