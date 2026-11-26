from app import create_app
from app.config import _database_url


def test_database_url_defaults(monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    assert _database_url().startswith('sqlite:///')
    monkeypatch.setenv('DATABASE_URL', 'postgres://u:p@host/db')
    assert _database_url() == 'postgresql://u:p@host/db'


def test_csrf_cookie_and_security_headers(client):
    res = client.get('/api/auth/')
    assert 'csrf_token' in res.headers.get('Set-Cookie', '')
    assert res.headers['X-Content-Type-Options'] == 'nosniff'


def test_missing_csrf_cookie_is_rejected_not_a_crash(tmp_path):
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'csrf.db'}",
        'SECRET_KEY': 'test',
    })
    from app.models import db
    with app.app_context():
        db.create_all()
    res = app.test_client().post('/api/auth/login',
                                 json={'email': 'a@b.co', 'password': 'x'})
    assert res.status_code == 401
    assert any('csrf' in e.lower() for e in res.get_json()['errors'])


def test_react_routes_without_a_build(client, monkeypatch, tmp_path):
    import app as app_module
    monkeypatch.setattr(app_module, 'BUILD_DIR', str(tmp_path))
    res = client.get('/stocks/AAPL')
    assert res.status_code == 404
    assert b'npm run build' in res.data


def test_react_routes_serve_index(client, monkeypatch, tmp_path):
    import app as app_module
    (tmp_path / 'index.html').write_text('<div id="root"></div>')
    (tmp_path / 'manifest.json').write_text('{}')
    monkeypatch.setattr(app_module, 'BUILD_DIR', str(tmp_path))
    assert b'root' in client.get('/stocks/AAPL').data
    assert client.get('/manifest.json').data == b'{}'
    # Paths can't escape the build folder.
    assert client.get('/../app/config.py').status_code in (200, 404)
    assert b'SECRET_KEY' not in client.get('/../app/config.py').data


def test_seed_and_undo(app):
    from app.models import User, Watchlist
    from app.seeds import seed_all, undo_all
    from app.models import Bank, db
    db.session.query(Bank).delete()
    db.session.commit()
    seed_all()
    assert User.query.count() == 1
    assert Watchlist.query.count() == 3
    undo_all()
    assert User.query.count() == 0


def test_migrations_build_the_current_schema(tmp_path):
    import os
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from flask_migrate import upgrade

    from app.models import db

    migrations = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'migrations')
    app = create_app({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f"sqlite:///{tmp_path / 'migrated.db'}",
        'SECRET_KEY': 'test',
    })
    with app.app_context():
        upgrade(directory=migrations)
        with db.engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), db.metadata)
        assert diff == []
