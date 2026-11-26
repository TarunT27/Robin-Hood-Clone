from app.models import db, Asset
from .utils import clear_table


def seed_assets():
    aapl = Asset(user_id=1, symbol='AAPL', count=35)
    tsla = Asset(user_id=1, symbol='TSLA', count=90)
    meta = Asset(user_id=1, symbol='META', count=9)
    nvda = Asset(user_id=1, symbol='NVDA', count=10)
    nflx = Asset(user_id=1, symbol='NFLX', count=50)
    amd = Asset(user_id=1, symbol='AMD', count=3)
    gme = Asset(user_id=1, symbol='GME', count=420)

    db.session.add(aapl)
    db.session.add(tsla)
    db.session.add(meta)
    db.session.add(nvda)
    db.session.add(nflx)
    db.session.add(amd)
    db.session.add(gme)

    db.session.commit()



def undo_assets():
    clear_table('assets')
