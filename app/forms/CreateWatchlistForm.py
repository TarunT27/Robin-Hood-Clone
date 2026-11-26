from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired, Length


class CreateWatchlistForm(FlaskForm):
    name = StringField('name', validators=[
        DataRequired(message='Please enter a name.'),
        Length(max=100, message='Name must be 100 characters or fewer.')])
