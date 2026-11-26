from app.models import db, WatchlistStock
from .utils import clear_table


def seed_watchlist_stocks():
    aapl_1 = WatchlistStock(watchlist_id=1, symbol='AAPL')
    tsla_1 = WatchlistStock(watchlist_id=1, symbol='TSLA')
    meta_1 = WatchlistStock(watchlist_id=1, symbol='META')
    nvda_1 = WatchlistStock(watchlist_id=1, symbol='NVDA')
    nflx_1 = WatchlistStock(watchlist_id=1, symbol='NFLX')
    twlo_1 = WatchlistStock(watchlist_id=1, symbol='TWLO')
    amzn_1 = WatchlistStock(watchlist_id=1, symbol='AMZN')
    googl_1 = WatchlistStock(watchlist_id=1, symbol='GOOGL')

    amd_2 = WatchlistStock(watchlist_id=2, symbol='AMD')
    gme_2 = WatchlistStock(watchlist_id=2, symbol='GME')
    bb_2 = WatchlistStock(watchlist_id=2, symbol='BB')
    mrna_2 = WatchlistStock(watchlist_id=2, symbol='MRNA')
    ko_2 = WatchlistStock(watchlist_id=2, symbol='KO')
    qqq_2 = WatchlistStock(watchlist_id=2, symbol='QQQ')
    googl_2 = WatchlistStock(watchlist_id=2, symbol='GOOGL')

    voo_3 = WatchlistStock(watchlist_id=3, symbol='VOO')
    vym_3 = WatchlistStock(watchlist_id=3, symbol='VYM')
    vti_3 = WatchlistStock(watchlist_id=3, symbol='VTI')
    qqq_3 = WatchlistStock(watchlist_id=3, symbol='QQQ')

    db.session.add(aapl_1)
    db.session.add(tsla_1)
    db.session.add(meta_1)
    db.session.add(nvda_1)
    db.session.add(nflx_1)
    db.session.add(twlo_1)
    db.session.add(amzn_1)
    db.session.add(googl_1)

    db.session.add(amd_2)
    db.session.add(gme_2)
    db.session.add(bb_2)
    db.session.add(mrna_2)
    db.session.add(ko_2)
    db.session.add(qqq_2)
    db.session.add(googl_2)

    db.session.add(voo_3)
    db.session.add(vym_3)
    db.session.add(vti_3)
    db.session.add(qqq_3)

    db.session.commit()



def undo_watchlist_stocks():
    clear_table('watchlist_stocks')
