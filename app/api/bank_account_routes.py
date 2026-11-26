from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from app.api.utils import (bound_form, get_owned_or_404,
                           validation_errors_to_error_messages)
from app.forms import AddBankForm, EditBankForm
from app.models import BankAccount, db

bank_account_routes = Blueprint('bank_accounts', __name__)


@bank_account_routes.route('/')
@login_required
def linked():
    """
    Gets all bank accounts linked to the logged-in user
    """
    accounts = BankAccount.query.filter_by(user_id=current_user.id).all()
    return jsonify({account.id: account.to_dict() for account in accounts})


@bank_account_routes.route('/add', methods=['POST'])
@login_required
def add_bank():
    """
    Links a new bank account to the logged-in user
    """
    form = bound_form(AddBankForm)
    if form.validate_on_submit():
        account = BankAccount(
            user_id=current_user.id,
            bank_id=form.data['bank_id'],
            name=form.data['name'].strip(),
            account_number=form.data['account_number'])
        db.session.add(account)
        db.session.commit()
        return account.to_dict()
    return {'errors': validation_errors_to_error_messages(form.errors)}, 400


@bank_account_routes.route('/delete/<int:id>', methods=['DELETE'])
@login_required
def remove_account(id):
    account = get_owned_or_404(BankAccount, id)
    db.session.delete(account)
    db.session.commit()
    return {'message': 'Bank account unlinked', 'id': id}


@bank_account_routes.route('/edit/<int:id>', methods=['PUT'])
@login_required
def update_bank(id):
    account = get_owned_or_404(BankAccount, id)
    form = bound_form(EditBankForm)
    form.account_id = account.id
    if form.validate_on_submit():
        account.bank_id = form.data['bank_id']
        account.name = form.data['name'].strip()
        account.account_number = form.data['account_number']
        db.session.commit()
        return account.to_dict()
    return {'errors': validation_errors_to_error_messages(form.errors)}, 400
