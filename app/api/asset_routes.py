from decimal import Decimal, ROUND_HALF_UP

from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app import market
from app.api.stock_routes import is_known_symbol
from app.api.utils import bound_form, validation_errors_to_error_messages
from app.forms import TradeForm
from app.models import Asset, User, db

asset_routes = Blueprint('assets', __name__)

CENT = Decimal('0.01')


@asset_routes.route('/', methods=['GET'])
@login_required
def load_assets():
    assets = Asset.query.filter(Asset.user_id == current_user.id).all()
    return jsonify({asset.symbol: asset.to_dict() for asset in assets})


@asset_routes.route('/trade', methods=['POST'])
@login_required
def trade():
    """
    Buys or sells shares at the current market price.

    The price comes from the server, and the buying power and the holding are
    updated in one transaction, so a trade can't overspend, sell shares the
    user doesn't have, or leave the account half updated.

    Body: {"symbol": "AAPL", "side": "buy" | "sell", "count": 3}
    """
    form = bound_form(TradeForm)
    if not form.validate_on_submit():
        return {'errors': validation_errors_to_error_messages(form.errors)}, 400

    symbol = form.data['symbol'].strip().upper()
    side = form.data['side']
    count = form.data['count']

    if not is_known_symbol(symbol):
        return {'errors': [f'symbol : {symbol} is not a listed stock.']}, 400

    try:
        quote = market.get_quote(symbol)
    except market.MarketDataError as err:
        return {'errors': [f'Market data unavailable: {err}']}, 502

    price = Decimal(str(quote['current'])).quantize(CENT)
    total = (price * count).quantize(CENT, rounding=ROUND_HALF_UP)

    # Lock the user's row while the trade runs (no-op on SQLite).
    user = db.session.execute(
        db.select(User).filter_by(id=current_user.id).with_for_update()
    ).scalar_one()
    asset = Asset.query.filter_by(user_id=user.id, symbol=symbol).first()
    buying_power = Decimal(user.buying_power or 0)

    if side == 'buy':
        if total > buying_power:
            return {'errors': ["You don't have enough buying power."]}, 400
        user.buying_power = buying_power - total
        if asset:
            asset.count += count
        else:
            asset = Asset(user_id=user.id, symbol=symbol, count=count)
            db.session.add(asset)
    else:
        if not asset or asset.count < count:
            return {'errors': ["You don't have that many shares to sell."]}, 400
        user.buying_power = buying_power + total
        asset.count -= count
        if asset.count == 0:
            db.session.delete(asset)

    db.session.commit()

    holding = asset.to_dict() if asset.count > 0 else None
    return {
        'symbol': symbol,
        'side': side,
        'count': count,
        'price': float(price),
        'total': float(total),
        'asset': holding,
        'buying_power': float(user.buying_power),
    }
