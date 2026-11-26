from decimal import Decimal

from flask import Blueprint
from flask_login import current_user, login_required

from app.api.utils import bound_form, validation_errors_to_error_messages
from app.forms import AddBuyingPowerForm
from app.models import BankAccount, db

buying_power_routes = Blueprint('buying_power', __name__)


@buying_power_routes.route('/add', methods=['PUT'])
@login_required
def add_bp():
    """
    Moves pretend money from one of the user's linked bank accounts into
    their buying power. Spending buying power only happens through a trade.
    """
    form = bound_form(AddBuyingPowerForm)
    if not form.validate_on_submit():
        return {'errors': validation_errors_to_error_messages(form.errors)}, 400

    if not BankAccount.query.filter_by(user_id=current_user.id).first():
        return {'errors': ['buying_power : Link a bank account before depositing funds.']}, 400

    current_user.buying_power = (Decimal(current_user.buying_power or 0)
                                 + Decimal(form.data['buying_power']))
    db.session.commit()
    return str(current_user.buying_power)
