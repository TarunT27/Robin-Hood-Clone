import os
import secrets


def _database_url():
    """
    Returns the database URL to use.

    Heroku-style Postgres URLs start with 'postgres://', which SQLAlchemy 1.4+
    no longer accepts, so they are rewritten to 'postgresql://'. With no
    DATABASE_URL set, a local SQLite file is used so the app runs out of the box.
    """
    url = os.environ.get('DATABASE_URL')
    if not url:
        return 'sqlite:///' + os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'dev.db')
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
    return url


class Config:
    # A random key is generated for local development so sessions work
    # without any setup. Set SECRET_KEY in production so sessions survive
    # restarts and are shared between workers.
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_ECHO = os.environ.get('SQLALCHEMY_ECHO', '').lower() in (
        '1', 'true', 'yes')
    JSON_SORT_KEYS = False

    # Market data: Finnhub is used when FINNHUB_API_KEY (or the older
    # API_KEY) is set. Otherwise, or when Finnhub refuses a request (its
    # candle endpoint is no longer on the free plan), the app falls back to
    # simulated prices so every page still works.
    FINNHUB_API_KEY = os.environ.get('FINNHUB_API_KEY') or os.environ.get(
        'API_KEY')
    MARKET_DATA_FALLBACK = os.environ.get(
        'MARKET_DATA_FALLBACK', 'simulated').lower()
