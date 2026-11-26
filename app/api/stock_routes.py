import os
from functools import lru_cache

from flask import Blueprint, jsonify, request

from app import market

stock_routes = Blueprint('stocks', __name__)

UTILS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'utils')
EXCHANGE_FILES = ('AMEX.txt', 'NASDAQ.txt', 'NYSE.txt')
SEARCH_LIMIT = 50


@lru_cache(maxsize=1)
def load_symbols():
    """
    Reads the exchange listings once and returns a sorted tuple of
    {'symbol', 'name'} dicts. Paths are relative to this package, so the app
    works no matter which directory it is started from.
    """
    symbols = {}
    for filename in EXCHANGE_FILES:
        with open(os.path.join(UTILS_DIR, filename), encoding='utf-8') as f:
            next(f, None)  # header row
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) == 2 and parts[0]:
                    symbols.setdefault(parts[0], parts[1])
    return tuple({'symbol': s, 'name': n} for s, n in sorted(symbols.items()))


def is_known_symbol(symbol):
    return any(stock['symbol'] == symbol.upper() for stock in load_symbols())


def market_error(err):
    return {'errors': [f'Market data unavailable: {err}']}, 502


@stock_routes.route('/')
def stock_symbols():
    """
    Returns every listed symbol as {symbol: {symbol, name}}
    """
    return jsonify({stock['symbol']: stock for stock in load_symbols()})


@stock_routes.route('/search/<query>')
def search(query):
    """
    Returns up to 50 stocks whose symbol or name contains the query.
    Exact and prefix symbol matches come first.
    """
    q = query.strip().lower()
    if not q:
        return jsonify([])
    matches = [s for s in load_symbols()
               if q in s['symbol'].lower() or q in s['name'].lower()]

    def rank(stock):
        symbol = stock['symbol'].lower()
        return (symbol != q, not symbol.startswith(q), len(symbol), symbol)

    return jsonify(sorted(matches, key=rank)[:SEARCH_LIMIT])


@stock_routes.route('/<symbol>/quote')
def stock_quote(symbol):
    try:
        return jsonify(market.get_quote(symbol))
    except market.MarketDataError as err:
        return market_error(err)


@stock_routes.route('/<symbol>/candles')
def stock_candles(symbol):
    time_frame = request.args.get('time-frame')
    if time_frame not in market.TIME_FRAMES:
        return {'errors': ['Time frame out of scope.']}, 400
    try:
        return jsonify(market.get_candles(symbol, time_frame))
    except market.MarketDataError as err:
        return market_error(err)


@stock_routes.route('/<symbol>/financials')
def stock_financials(symbol):
    try:
        return jsonify(market.get_financials(symbol))
    except market.MarketDataError as err:
        return market_error(err)
