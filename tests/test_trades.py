from decimal import Decimal

from app.models import Asset, User, db


def trade(client, symbol='AAPL', side='buy', count=1):
    return client.post('/api/portfolio/assets/trade',
                       json={'symbol': symbol, 'side': side, 'count': count})


def buying_power(user_id):
    return Decimal(db.session.get(User, user_id).buying_power)


def test_buy_charges_server_price(logged_in, user, fixed_price):
    res = trade(logged_in, count=3)
    data = res.get_json()
    assert res.status_code == 200, data
    assert data['price'] == 10.0
    assert data['total'] == 30.0
    assert data['asset']['count'] == 3
    assert data['buying_power'] == 970.0
    assert buying_power(user.id) == Decimal('970.00')


def test_buying_more_adds_to_the_holding(logged_in, user, fixed_price):
    trade(logged_in, count=2)
    res = trade(logged_in, symbol='aapl', count=5)
    assert res.get_json()['asset']['count'] == 7
    assert Asset.query.filter_by(user_id=user.id).count() == 1


def test_cannot_overspend(logged_in, user, fixed_price):
    res = trade(logged_in, count=101)  # $1,010 > $1,000
    assert res.status_code == 400
    assert 'buying power' in res.get_json()['errors'][0]
    assert buying_power(user.id) == Decimal('1000.00')
    assert Asset.query.count() == 0


def test_sell_credits_buying_power(logged_in, user, fixed_price):
    trade(logged_in, count=10)
    res = trade(logged_in, side='sell', count=4)
    data = res.get_json()
    assert res.status_code == 200
    assert data['asset']['count'] == 6
    assert data['buying_power'] == 940.0


def test_selling_everything_removes_the_holding(logged_in, user, fixed_price):
    trade(logged_in, count=10)
    res = trade(logged_in, side='sell', count=10)
    assert res.get_json()['asset'] is None
    assert Asset.query.count() == 0
    assert buying_power(user.id) == Decimal('1000.00')


def test_cannot_sell_shares_you_do_not_have(logged_in, user, fixed_price):
    trade(logged_in, count=2)
    res = trade(logged_in, side='sell', count=3)
    assert res.status_code == 400
    assert trade(logged_in, symbol='MSFT', side='sell').status_code == 400


def test_rejects_bad_counts_and_symbols(logged_in, fixed_price):
    assert trade(logged_in, count=0).status_code == 400
    assert trade(logged_in, count=-5).status_code == 400
    assert trade(logged_in, side='short').status_code == 400
    assert trade(logged_in, symbol='ZZZZZ').status_code == 400


def test_trade_uses_simulated_prices_without_api_key(logged_in, user):
    res = trade(logged_in, symbol='MSFT', count=1)
    assert res.status_code == 200
    assert res.get_json()['price'] > 0


def test_holdings_list(logged_in, fixed_price):
    trade(logged_in, symbol='AAPL', count=1)
    trade(logged_in, symbol='MSFT', count=2)
    res = logged_in.get('/api/portfolio/assets/')
    assert res.status_code == 200
    assert {k: v['count'] for k, v in res.get_json().items()} == {'AAPL': 1, 'MSFT': 2}


def test_trading_requires_login(client, fixed_price):
    assert trade(client).status_code == 401
