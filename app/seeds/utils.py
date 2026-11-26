from sqlalchemy import text

from app.models import db


def clear_table(name):
    """
    Empties a table and resets its ids. Postgres uses TRUNCATE ... CASCADE;
    other databases (SQLite in development and tests) use a plain DELETE.
    """
    if db.engine.dialect.name == 'postgresql':
        db.session.execute(text(f'TRUNCATE {name} RESTART IDENTITY CASCADE;'))
    else:
        db.session.execute(text(f'DELETE FROM {name};'))
    db.session.commit()
