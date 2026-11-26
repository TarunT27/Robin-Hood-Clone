from flask_wtf import FlaskForm
from wtforms import IntegerField
from wtforms.validators import DataRequired, NumberRange

MAX_TRANSFER = 1_000_000


class AddBuyingPowerForm(FlaskForm):
    buying_power = IntegerField('buying_power', validators=[
        DataRequired(message='Please enter an amount.'),
        NumberRange(min=1, max=MAX_TRANSFER,
                    message='Please enter an amount between $1 and $1,000,000.')])
