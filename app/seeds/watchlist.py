from app.models import db, Watchlist
from .utils import clear_table


def seed_watchlists():
    tech = Watchlist(user_id=1, name='Tech')
    random = Watchlist(user_id=1, name='Random')
    eft = Watchlist(user_id=1, name='EFT')

    db.session.add(tech)
    db.session.add(random)
    db.session.add(eft)

    db.session.commit()



def undo_watchlists():
    clear_table('watchlists')
