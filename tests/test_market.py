from datetime import datetime

import pytest
import requests

from app import market

ET = market.MARKET_TZ
TUESDAY_NOON = datetime(2026, 11, 24, 12, 0, tzinfo=ET)
SATURDAY = datetime(2026, 11, 28, 15, 0, tzinfo=ET)
MONDAY_EARLY = datetime(2026, 11, 23, 8, 0, tzinfo=ET)


def test_last_trading_day():
    assert market.last_trading_day(TUESDAY_NOON).isoformat() == '2026-11-24'
    assert market.last_trading_day(SATURDAY).isoformat() == '2026-11-27'
    # Before the open on Monday, Friday's session is the latest one.
    assert market.last_trading_day(MONDAY_EARLY).isoformat() == '2026-11-20'


def test_simulated_prices_are_stable():
    assert market.simulated_quote('AAPL', TUESDAY_NOON) == \
        market.simulated_quote('AAPL', TUESDAY_NOON)
    assert market.simulated_quote('AAPL', TUESDAY_NOON) != \
        market.simulated_quote('MSFT', TUESDAY_NOON)


def test_quote_matches_the_chart():
    quote = market.simulated_quote('NVDA', TUESDAY_NOON)
    day = market.simulated_candles('NVDA', '1D', TUESDAY_NOON)
    prices = [p['price'] for p in day]
    assert quote['current'] == prices[-1]
    assert quote['open'] == prices[0]
    assert quote['high'] == max(prices) and quote['low'] == min(prices)
    # Midday: no points after "now".
    assert day[-1]['time'] <= TUESDAY_NOON.timestamp()


def test_previous_close_is_yesterdays_close():
    monday_close = market.simulated_quote(
        'TSLA', datetime(2026, 11, 23, 17, 0, tzinfo=ET))['current']
    assert market.simulated_quote('TSLA', TUESDAY_NOON)['previous_close'] == monday_close


@pytest.mark.parametrize('frame,minimum', [
    ('1D', 20), ('1W', 100), ('1M', 100), ('3M', 60), ('1Y', 250)])
def test_simulated_candles(frame, minimum):
    candles = market.simulated_candles('AMD', frame, SATURDAY)
    times = [c['time'] for c in candles]
    assert len(candles) >= minimum
    assert times == sorted(times)
    assert all(c['price'] > 0 for c in candles)
    # Every point falls on a weekday.
    assert all(datetime.fromtimestamp(t, ET).weekday() < 5 for t in times)


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status_code = payload, status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))

    def json(self):
        return self.payload


def test_uses_finnhub_when_configured(app, monkeypatch):
    app.config['FINNHUB_API_KEY'] = 'key'
    seen = {}

    def fake_get(url, params, timeout):
        seen.update(url=url, params=params, timeout=timeout)
        return FakeResponse({'c': 101.5, 'd': 1.5, 'dp': 1.5, 'o': 100,
                             'pc': 100, 'h': 102, 'l': 99})
    monkeypatch.setattr(market.requests, 'get', fake_get)
    quote = market.get_quote('aapl')
    assert quote['current'] == 101.5
    assert seen['params']['symbol'] == 'AAPL'
    assert seen['timeout'] == market.REQUEST_TIMEOUT


def test_falls_back_when_finnhub_refuses(app, monkeypatch):
    app.config['FINNHUB_API_KEY'] = 'key'
    monkeypatch.setattr(market.requests, 'get', lambda *a, **k: FakeResponse(
        {'error': "You don't have access to this resource."}))
    candles = market.get_candles('AAPL', '1Y')
    assert len(candles) > 200


def test_falls_back_on_network_errors(app, monkeypatch):
    app.config['FINNHUB_API_KEY'] = 'key'

    def boom(*a, **k):
        raise requests.ConnectionError('down')
    monkeypatch.setattr(market.requests, 'get', boom)
    assert market.get_quote('AAPL')['current'] > 0


def test_fallback_can_be_turned_off(app, client):
    app.config['MARKET_DATA_FALLBACK'] = 'off'
    res = client.get('/api/stocks/AAPL/quote')
    assert res.status_code == 502
    assert 'Market data unavailable' in res.get_json()['errors'][0]


def test_unknown_time_frame():
    with pytest.raises(ValueError):
        market.get_candles('AAPL', '10Y')


def test_simulated_history_stays_believable():
    closes = [c for _, c in market._daily_closes('AAPL', SATURDAY.date())]
    first = closes[0]
    assert all(first / 4 < c < first * 4 for c in closes)


def test_simulated_chart_ends_on_the_live_quote(app, monkeypatch):
    app.config['FINNHUB_API_KEY'] = 'key'

    def fake_get(url, params, timeout):
        if url.endswith('/quote'):
            return FakeResponse({'c': 123.45, 'd': 1, 'dp': 1, 'o': 122,
                                 'pc': 122.45, 'h': 124, 'l': 121})
        return FakeResponse({'error': "You don't have access to this resource."})
    monkeypatch.setattr(market.requests, 'get', fake_get)
    candles = market.get_candles('AAPL', '1M')
    assert candles[-1]['price'] == 123.45
    assert len(candles) > 50
