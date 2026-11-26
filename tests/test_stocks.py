import os


def test_symbols_load(client):
    data = client.get('/api/stocks/').get_json()
    assert data['AAPL']['name']
    assert 'META' in data


def test_search_ranks_exact_symbol_first(client):
    results = client.get('/api/stocks/search/aapl').get_json()
    assert results[0]['symbol'] == 'AAPL'
    assert len(client.get('/api/stocks/search/a').get_json()) <= 50


def test_symbols_load_from_any_working_directory(client, tmp_path, monkeypatch):
    from app.api import stock_routes
    stock_routes.load_symbols.cache_clear()
    monkeypatch.chdir(tmp_path)
    assert client.get('/api/stocks/search/msft').status_code == 200


def test_quote_candles_financials(client):
    quote = client.get('/api/stocks/AAPL/quote').get_json()
    assert set(quote) == {'current', 'change', 'change_percent', 'open',
                          'previous_close', 'high', 'low'}
    for frame in ('1D', '1W', '1M', '3M', '1Y'):
        candles = client.get(f'/api/stocks/AAPL/candles?time-frame={frame}').get_json()
        assert candles, frame
    financials = client.get('/api/stocks/AAPL/financials').get_json()
    assert financials['52_week_high'] >= financials['52_week_low']


def test_bad_time_frame(client):
    res = client.get('/api/stocks/AAPL/candles?time-frame=5Y')
    assert res.status_code == 400


def test_unknown_api_route_is_json_404(client):
    res = client.get('/api/nope')
    assert res.status_code == 404
    assert 'errors' in res.get_json()
