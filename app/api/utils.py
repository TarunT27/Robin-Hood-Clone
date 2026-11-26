from flask import abort
from flask_login import current_user

from app.models import db


def validation_errors_to_error_messages(validation_errors):
    """
    Turns WTForms validation errors into a simple list of 'field : error'.
    """
    return [f'{field} : {error}'
            for field, errors in validation_errors.items()
            for error in errors]


def get_owned_or_404(model, id):
    """
    Loads a row by id and checks it belongs to the logged-in user.
    Rows that don't exist and rows owned by someone else both give a 404,
    so ids belonging to other users can't be probed.
    """
    row = db.session.get(model, id)
    if row is None or row.user_id != current_user.id:
        abort(404)
    return row


def bound_form(form_class):
    """
    Builds a form from the request and copies the CSRF token from the
    csrf_token cookie (set on every response) into it, so
    form.validate_on_submit() checks it. A missing cookie fails validation
    instead of raising a KeyError.
    """
    from flask import request

    form = form_class()
    if 'csrf_token' in form:
        form['csrf_token'].data = request.cookies.get('csrf_token', '')
    return form
