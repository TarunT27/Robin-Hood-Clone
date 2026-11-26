from app.models import Watchlist, db
from conftest import login


def create(client, name='Tech'):
    return client.post('/api/portfolio/watchlists/', json={'name': name})


def test_create_and_list_with_stocks(logged_in):
    wl = create(logged_in).get_json()
    assert logged_in.post(f"/api/portfolio/watchlists/{wl['id']}/stocks",
                          json={'symbol': 'aapl'}).status_code == 200
    # Listing a watchlist that has stocks used to crash (it read a column
    # that no longer exists).
    res = logged_in.get('/api/portfolio/watchlists/')
    assert res.status_code == 200
    assert res.get_json() == [
        {'id': wl['id'], 'name': 'Tech', 'stocks': [{'id': 1, 'symbol': 'AAPL'}]}]


def test_watchlist_belongs_to_logged_in_user(logged_in, user, other_user):
    res = logged_in.post('/api/portfolio/watchlists/',
                         json={'name': 'Mine', 'user_id': other_user.id})
    assert res.get_json()['user_id'] == user.id


def test_duplicate_names_are_rejected(logged_in):
    create(logged_in, 'Tech')
    res = create(logged_in, ' tech ')
    assert res.status_code == 409
    assert res.get_json()['error'] == 'Watchlist already exists'


def test_rename(logged_in):
    a = create(logged_in, 'A').get_json()
    create(logged_in, 'B')
    url = f"/api/portfolio/watchlists/{a['id']}"
    assert logged_in.patch(url, json={'name': 'B'}).status_code == 409
    # Renaming to its own name (different case) is fine.
    assert logged_in.patch(url, json={'name': 'a'}).status_code == 200
    assert logged_in.patch(url, json={'name': 'Growth'}).get_json()['name'] == 'Growth'


def test_add_stock_validation(logged_in):
    wl = create(logged_in).get_json()
    url = f"/api/portfolio/watchlists/{wl['id']}/stocks"
    # The old picker sent "Apple Inc AAPL" as the symbol.
    assert logged_in.post(url, json={'name': 'Apple Inc AAPL'}).status_code == 400
    assert logged_in.post(url, json={'symbol': 'AAPL'}).status_code == 200
    assert logged_in.post(url, json={'symbol': 'AAPL'}).status_code == 409


def test_delete_stock_and_watchlist(logged_in):
    wl = create(logged_in).get_json()
    stock = logged_in.post(f"/api/portfolio/watchlists/{wl['id']}/stocks",
                           json={'symbol': 'MSFT'}).get_json()
    assert logged_in.delete(
        f"/api/portfolio/watchlists/{wl['id']}/stocks/{stock['id']}").status_code == 200
    assert logged_in.delete(f"/api/portfolio/watchlists/{wl['id']}").status_code == 200
    assert Watchlist.query.count() == 0


def test_cannot_touch_someone_elses_watchlist(client, user, other_user):
    theirs = Watchlist(user_id=other_user.id, name='Private')
    db.session.add(theirs)
    db.session.commit()
    login(client)
    url = f'/api/portfolio/watchlists/{theirs.id}'
    assert client.delete(url).status_code == 404
    assert client.patch(url, json={'name': 'Hacked'}).status_code == 404
    assert client.post(f'{url}/stocks', json={'symbol': 'AAPL'}).status_code == 404
    assert db.session.get(Watchlist, theirs.id).name == 'Private'


def test_missing_watchlist_is_404_not_500(logged_in):
    assert logged_in.delete('/api/portfolio/watchlists/999').status_code == 404
    assert logged_in.delete('/api/portfolio/watchlists/999/stocks/1').status_code == 404
