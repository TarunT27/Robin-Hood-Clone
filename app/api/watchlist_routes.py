from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import func

from app.api.stock_routes import is_known_symbol
from app.api.utils import (bound_form, get_owned_or_404,
                           validation_errors_to_error_messages)
from app.forms import CreateWatchlistForm
from app.models import Watchlist, WatchlistStock, db

watchlist_routes = Blueprint('watchlists', __name__)


def name_taken(name, exclude_id=None):
    query = Watchlist.query.filter(
        Watchlist.user_id == current_user.id,
        func.lower(Watchlist.name) == name.strip().lower())
    if exclude_id is not None:
        query = query.filter(Watchlist.id != exclude_id)
    return db.session.query(query.exists()).scalar()


def serialize(watchlist):
    return {
        'id': watchlist.id,
        'name': watchlist.name,
        'stocks': [{'id': s.id, 'symbol': s.symbol}
                   for s in sorted(watchlist.stocks, key=lambda s: s.id)],
    }


@watchlist_routes.route('/', methods=['GET'])
@login_required
def load_watchlists():
    watchlists = Watchlist.query.filter_by(
        user_id=current_user.id).order_by(Watchlist.id).all()
    return jsonify([serialize(w) for w in watchlists])


@watchlist_routes.route('/', methods=['POST'])
@login_required
def create_watchlist():
    form = bound_form(CreateWatchlistForm)
    if not form.validate_on_submit():
        return {'errors': validation_errors_to_error_messages(form.errors)}, 400
    name = form.data['name'].strip()
    if name_taken(name):
        return {'error': 'Watchlist already exists'}, 409
    watchlist = Watchlist(user_id=current_user.id, name=name)
    db.session.add(watchlist)
    db.session.commit()
    return watchlist.to_dict()


@watchlist_routes.route('/<int:id>', methods=['DELETE'])
@login_required
def delete_watchlist(id):
    watchlist = get_owned_or_404(Watchlist, id)
    data = watchlist.to_dict()
    db.session.delete(watchlist)
    db.session.commit()
    return data


@watchlist_routes.route('/<int:id>', methods=['PATCH'])
@login_required
def rename_watchlist(id):
    watchlist = get_owned_or_404(Watchlist, id)
    form = bound_form(CreateWatchlistForm)
    if not form.validate_on_submit():
        return {'errors': validation_errors_to_error_messages(form.errors)}, 400
    name = form.data['name'].strip()
    if name_taken(name, exclude_id=id):
        return {'error': 'Watchlist already exists'}, 409
    watchlist.name = name
    db.session.commit()
    return watchlist.to_dict()


@watchlist_routes.route('/<int:id>/stocks', methods=['POST'])
@login_required
def add_stock(id):
    watchlist = get_owned_or_404(Watchlist, id)
    body = request.get_json(silent=True) or {}
    symbol = str(body.get('symbol') or body.get('name') or '').strip().upper()
    if not symbol or len(symbol) > 5 or not is_known_symbol(symbol):
        return {'error': 'Please choose a listed stock.'}, 400
    if any(s.symbol == symbol for s in watchlist.stocks):
        return {'error': 'Stock already exists within watchlist'}, 409
    stock = WatchlistStock(watchlist_id=watchlist.id, symbol=symbol)
    db.session.add(stock)
    db.session.commit()
    return stock.to_dict()


@watchlist_routes.route('/<int:watchlist_id>/stocks/<int:stock_id>', methods=['DELETE'])
@login_required
def delete_stock(watchlist_id, stock_id):
    watchlist = get_owned_or_404(Watchlist, watchlist_id)
    stock = db.session.get(WatchlistStock, stock_id)
    if stock is None or stock.watchlist_id != watchlist.id:
        return {'error': 'Stock not found in this watchlist'}, 404
    data = stock.to_dict()
    db.session.delete(stock)
    db.session.commit()
    return data
