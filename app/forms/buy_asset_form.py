from flask_wtf import FlaskForm
from wtforms import IntegerField, SelectField, StringField
from wtforms.validators import DataRequired, Length, NumberRange


class TradeForm(FlaskForm):
    symbol = StringField('symbol', validators=[DataRequired(), Length(max=5)])
    side = SelectField('side', choices=['buy', 'sell'])
    count = IntegerField('count', validators=[
        DataRequired(message='Please enter a number of shares.'),
        NumberRange(min=1, max=1_000_000,
                    message='Please enter between 1 and 1,000,000 shares.')])
