"""
Market data for Robinsock.

Quotes, price history ("candles") and key financials come from Finnhub when an
API key is configured. Finnhub's free plan no longer serves price history and
any request can fail or be rate limited, so every call can fall back to a
simulated market: a deterministic random walk per symbol, so the same symbol
shows the same prices across page loads and the quote always agrees with the
chart.
"""
import hashlib
import math
import random
from datetime import date, datetime, time, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

import requests
from flask import current_app

MARKET_TZ = ZoneInfo('America/New_York')
MARKET_OPEN = time(9, 30)
MARKET_CLOSE = time(16, 0)
FINNHUB_URL = 'https://finnhub.io/api/v1'
REQUEST_TIMEOUT = 5

TIME_FRAMES = ('1D', '1W', '1M', '3M', '1Y')

class MarketDataError(Exception):
    """Raised when no market data source could answer."""


# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------

def now():
    return datetime.now(MARKET_TZ)


def is_trading_day(day):
    return day.weekday() < 5


def last_trading_day(moment):
    """The most recent trading day whose session has started by `moment`."""
    day = moment.date()
    if moment.time() < MARKET_OPEN:
        day -= timedelta(days=1)
    while not is_trading_day(day):
        day -= timedelta(days=1)
    return day


def previous_trading_day(day):
    day -= timedelta(days=1)
    while not is_trading_day(day):
        day -= timedelta(days=1)
    return day


def at(day, clock):
    return datetime.combine(day, clock, tzinfo=MARKET_TZ)


# ---------------------------------------------------------------------------
# Simulated market
# ---------------------------------------------------------------------------

def _seed(*parts):
    digest = hashlib.sha256('|'.join(str(p) for p in parts).encode()).hexdigest()
    return int(digest[:16], 16)


# The simulated history starts here; every symbol's walk begins on this day,
# so a given day's price never changes no matter which chart asks for it.
HISTORY_START = date(2021, 1, 4)
MEAN_REVERSION = 0.01


@lru_cache(maxsize=256)
def _series(symbol, until):
    rng = random.Random(_seed(symbol, 'daily'))
    base = math.log(rng.uniform(15, 450))
    volatility = rng.uniform(0.008, 0.025)
    drift = rng.uniform(-0.0002, 0.0004)

    # The log price wanders around the symbol's base price and is pulled
    # back towards it, so years of history stay in a believable range.
    log_price = base
    closes = []
    day = HISTORY_START
    while day <= until:
        if is_trading_day(day):
            # Each day's move depends only on the symbol and the date.
            day_rng = random.Random(_seed(symbol, day.isoformat()))
            log_price += (drift + MEAN_REVERSION * (base - log_price)
                          + volatility * day_rng.gauss(0, 1))
            closes.append((day, round(max(math.exp(log_price), 1.0), 2)))
        day += timedelta(days=1)
    return tuple(closes)


def _daily_closes(symbol, end_day):
    """
    Closing prices for each trading day up to and including `end_day`,
    oldest first, as a list of (date, close).
    """
    # Build the series once per symbol (up to today) and slice it.
    until = max(end_day, now().date())
    return [c for c in _series(symbol, until) if c[0] <= end_day]


def _intraday(symbol, day, step_minutes=5):
    """
    Simulated prices through one session, every `step_minutes`, as a list of
    (datetime, price). It starts near the previous close and ends on the
    day's close.
    """
    closes = dict(_daily_closes(symbol, day))
    prev_close = closes[previous_trading_day(day)]
    close = closes[day]

    rng = random.Random(_seed(symbol, day.isoformat(), 'intraday'))
    opening = prev_close * (1 + rng.gauss(0, 0.004))

    start = at(day, MARKET_OPEN)
    steps = int((at(day, MARKET_CLOSE) - start).total_seconds() // 60 // step_minutes)

    # Brownian bridge from the open to the close.
    walk = [0.0]
    for _ in range(steps):
        walk.append(walk[-1] + rng.gauss(0, 1))
    noise = abs(close - opening) / 4 + close * 0.002
    points = []
    for i, w in enumerate(walk):
        t = i / steps
        bridge = w - t * walk[-1]
        price = opening + (close - opening) * t + bridge * noise / math.sqrt(steps)
        points.append((start + timedelta(minutes=i * step_minutes), round(max(price, 0.5), 2)))
    return points


def _session_so_far(symbol, moment):
    """Today's simulated points up to `moment` (the whole session if closed)."""
    day = last_trading_day(moment)
    points = _intraday(symbol, day)
    if moment.date() == day:
        points = [p for p in points if p[0] <= moment] or points[:1]
    return day, points


def simulated_quote(symbol, moment=None):
    moment = moment or now()
    day, points = _session_so_far(symbol, moment)
    closes = dict(_daily_closes(symbol, day))
    previous_close = closes[previous_trading_day(day)]
    prices = [p for _, p in points]
    current = prices[-1]
    change = round(current - previous_close, 2)
    return {
        'current': current,
        'change': change,
        'change_percent': round(change / previous_close * 100, 4),
        'open': prices[0],
        'previous_close': previous_close,
        'high': max(prices),
        'low': min(prices),
    }


def simulated_candles(symbol, time_frame, moment=None):
    moment = moment or now()
    day, today = _session_so_far(symbol, moment)

    if time_frame == '1D':
        points = today
    elif time_frame in ('1W', '1M'):
        days = 5 if time_frame == '1W' else 21
        step = 10 if time_frame == '1W' else 60
        sessions = []
        d = day
        for _ in range(days - 1):
            d = previous_trading_day(d)
            sessions.append(d)
        points = []
        for d in reversed(sessions):
            points.extend(p for i, p in enumerate(_intraday(symbol, d)) if (i * 5) % step == 0)
        points.extend(p for i, p in enumerate(today) if (i * 5) % step == 0)
    else:
        span = 63 if time_frame == '3M' else 252
        history = _daily_closes(symbol, day)[-span:]
        points = [(at(d, MARKET_CLOSE), c) for d, c in history[:-1]]
        points.append(today[-1])

    return [{'time': int(t.timestamp()), 'price': p} for t, p in points]


def simulated_financials(symbol):
    rng = random.Random(_seed(symbol, 'financials'))
    closes = [c for _, c in _daily_closes(symbol, last_trading_day(now()))[-252:]]
    return {
        'market_cap': round(rng.uniform(300, 2_500_000), 2),
        '52_week_high': max(closes),
        '52_week_low': min(closes),
        'pe_ratio': round(rng.uniform(6, 80), 2),
        'dividend_yield': round(rng.choice([0, 0, rng.uniform(0.2, 4.5)]), 2),
    }


# ---------------------------------------------------------------------------
# Finnhub
# ---------------------------------------------------------------------------

def _finnhub(path, **params):
    token = current_app.config.get('FINNHUB_API_KEY')
    if not token:
        raise MarketDataError('No Finnhub API key configured.')
    try:
        res = requests.get(f'{FINNHUB_URL}{path}',
                           params={**params, 'token': token},
                           timeout=REQUEST_TIMEOUT)
        res.raise_for_status()
        data = res.json()
    except (requests.RequestException, ValueError) as err:
        raise MarketDataError(f'Finnhub request failed: {err}') from err
    if isinstance(data, dict) and data.get('error'):
        raise MarketDataError(f"Finnhub refused the request: {data['error']}")
    return data


def finnhub_quote(symbol):
    res = _finnhub('/quote', symbol=symbol)
    # Finnhub answers unknown symbols with all zeros.
    if not res.get('c'):
        raise MarketDataError(f'No quote for {symbol}.')
    return {
        'current': res['c'],
        'change': res['d'],
        'change_percent': res['dp'],
        'open': res['o'],
        'previous_close': res['pc'],
        'high': res['h'],
        'low': res['l'],
    }


def finnhub_candles(symbol, time_frame):
    moment = now()
    day = last_trading_day(moment)
    starts = {
        '1D': at(day, MARKET_OPEN),
        '1W': at(day - timedelta(days=6), MARKET_OPEN),
        '1M': at(day - timedelta(days=30), MARKET_OPEN),
        '3M': at(day - timedelta(days=91), MARKET_OPEN),
        '1Y': at(day - timedelta(days=365), MARKET_OPEN),
    }
    resolutions = {'1D': '5', '1W': '5', '1M': '60', '3M': 'D', '1Y': 'D'}
    res = _finnhub('/stock/candle', symbol=symbol,
                   resolution=resolutions[time_frame],
                   **{'from': int(starts[time_frame].timestamp()),
                      'to': int(moment.timestamp())})
    if res.get('s') != 'ok' or not res.get('t'):
        raise MarketDataError(f'No candles for {symbol}.')

    data = [{'time': t, 'price': c} for t, c in zip(res['t'], res['c'])]
    if time_frame in ('1W', '1M'):
        # Keep regular-hours points only, every 10 minutes.
        def keep(point):
            local = datetime.fromtimestamp(point['time'], MARKET_TZ)
            return (MARKET_OPEN <= local.time() < MARKET_CLOSE
                    and local.minute % 10 == 0)
        data = [d for d in data if keep(d)]
    return data


def finnhub_financials(symbol):
    res = _finnhub('/stock/metric', symbol=symbol, metric='all').get('metric') or {}
    if not res:
        raise MarketDataError(f'No financials for {symbol}.')
    return {
        'market_cap': res.get('marketCapitalization'),
        '52_week_high': res.get('52WeekHigh'),
        '52_week_low': res.get('52WeekLow'),
        'pe_ratio': res.get('peNormalizedAnnual'),
        'dividend_yield': res.get('dividendYieldIndicatedAnnual'),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def _with_fallback(live, simulated, *args):
    try:
        return live(*args)
    except MarketDataError:
        if current_app.config.get('MARKET_DATA_FALLBACK') == 'off':
            raise
        return simulated(*args)


def get_quote(symbol):
    return _with_fallback(finnhub_quote, simulated_quote, symbol.upper())


def get_candles(symbol, time_frame):
    if time_frame not in TIME_FRAMES:
        raise ValueError(f'Unknown time frame {time_frame!r}.')
    symbol = symbol.upper()
    try:
        return finnhub_candles(symbol, time_frame)
    except MarketDataError:
        if current_app.config.get('MARKET_DATA_FALLBACK') == 'off':
            raise
    points = simulated_candles(symbol, time_frame)
    # Finnhub's free plan has live quotes but no history. When a live quote
    # is available, scale the simulated chart so it ends on the real price
    # and the chart agrees with the quote shown beside it.
    try:
        live = finnhub_quote(symbol)['current']
    except MarketDataError:
        return points
    scale = live / points[-1]['price']
    return [{'time': p['time'], 'price': round(p['price'] * scale, 2)}
            for p in points]


def get_financials(symbol):
    return _with_fallback(finnhub_financials, simulated_financials, symbol.upper())
