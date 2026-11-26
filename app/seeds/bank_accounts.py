from app.models import db, BankAccount
from .utils import clear_table


def seed_bank_accounts():
    acc_1 = BankAccount(
        user_id=1, bank_id=1, name='Chase bank', account_number='1234567890')
    acc_2 = BankAccount(user_id=1, bank_id=2, name='BoA',
                        account_number='9876543210')

    db.session.add(acc_1)
    db.session.add(acc_2)

    db.session.commit()



def undo_bank_accounts():
    clear_table('bank_accounts')
