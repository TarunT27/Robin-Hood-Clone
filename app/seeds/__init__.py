from flask.cli import AppGroup

from .users import seed_users, undo_users
from .banks import seed_banks, undo_banks
from .assets import seed_assets, undo_assets
from .bank_accounts import seed_bank_accounts, undo_bank_accounts
from .watchlist import seed_watchlists, undo_watchlists
from .watchlist_stocks import seed_watchlist_stocks, undo_watchlist_stocks

# `flask seed --help`
seed_commands = AppGroup('seed')


def seed_all():
    seed_users()
    seed_banks()
    seed_assets()
    seed_bank_accounts()
    seed_watchlists()
    seed_watchlist_stocks()


def undo_all():
    # Children first, so foreign keys never point at deleted rows.
    undo_watchlist_stocks()
    undo_watchlists()
    undo_bank_accounts()
    undo_assets()
    undo_banks()
    undo_users()


@seed_commands.command('all')
def seed():
    """Adds the demo user, banks, holdings and watchlists."""
    seed_all()


@seed_commands.command('undo')
def undo():
    """Removes all seeded data."""
    undo_all()
