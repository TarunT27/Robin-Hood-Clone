from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError

from app.models import Bank, BankAccount


def bank_exists(form, field):
    from app.models import db
    if db.session.get(Bank, field.data) is None:
        raise ValidationError('Please choose a bank.')


def account_number_free(form, field):
    """Account numbers are unique; an account may keep its own number."""
    acct = BankAccount.query.filter(
        BankAccount.account_number == field.data).first()
    if acct and acct.id != getattr(form, 'account_id', None):
        raise ValidationError(
            'That account number is already linked. Please enter a different one.')


class AddBankForm(FlaskForm):
    bank_id = IntegerField('bank_id', validators=[
        DataRequired(message='Please choose a bank.'), bank_exists])
    account_number = StringField('account_number', validators=[
        DataRequired(),
        Regexp(r'^\d{10}$', message='Please enter a valid account number.'),
        account_number_free])
    name = StringField('name', validators=[
        DataRequired(message='Please enter a valid name.'),
        Length(min=3, max=30, message='Name must be 3 to 30 characters long.')])


class EditBankForm(AddBankForm):
    pass
