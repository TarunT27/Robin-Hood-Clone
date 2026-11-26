import os

import click
from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_login import LoginManager
from flask_migrate import Migrate, stamp
from flask_wtf.csrf import generate_csrf
from werkzeug.exceptions import HTTPException

from .config import Config
from .models import db, User


# The React production build (`npm run build` in react-app/).
BUILD_DIR = os.environ.get('REACT_BUILD_DIR') or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'react-app', 'build')


def create_app(config=None):
    """
    Builds the Flask app. `config` is an optional dict of overrides, used by
    the tests to point at a throwaway database.
    """
    # The build's js/css live under build/static and are served at /static.
    app = Flask(__name__, static_folder=os.path.join(BUILD_DIR, 'static'),
                static_url_path='/static')
    app.config.from_object(Config)
    if config:
        app.config.update(config)

    db.init_app(app)
    Migrate(app, db)

    login = LoginManager(app)
    login.login_view = 'auth.unauthorized'

    @login.user_loader
    def load_user(id):
        return db.session.get(User, int(id))

    @login.unauthorized_handler
    def unauthorized():
        return {'errors': ['Unauthorized']}, 401

    from .api.auth_routes import auth_routes
    from .api.bank_routes import bank_routes
    from .api.portfolio_routes import portfolio_routes
    from .api.stock_routes import stock_routes
    from .seeds import seed_commands, seed_all

    app.register_blueprint(auth_routes, url_prefix='/api/auth')
    app.register_blueprint(portfolio_routes, url_prefix='/api/portfolio')
    app.register_blueprint(bank_routes, url_prefix='/api/banks')
    app.register_blueprint(stock_routes, url_prefix='/api/stocks')

    app.cli.add_command(seed_commands)

    @app.cli.command('init-db')
    @click.option('--no-seed', is_flag=True, help='Create tables only.')
    def init_db(no_seed):
        """Creates every table, adds the demo data and marks migrations as applied."""
        db.create_all()
        if not no_seed:
            seed_all()
        stamp()
        click.echo('Database ready.')

    in_production = os.environ.get('FLASK_ENV') == 'production'

    # Behind Heroku's router every request arrives over http, so production
    # requests that came in over plain http are redirected to https.
    @app.before_request
    def https_redirect():
        if in_production and request.headers.get('X-Forwarded-Proto') == 'http':
            return redirect(request.url.replace('http://', 'https://', 1), code=301)

    @app.after_request
    def inject_csrf_token(response):
        response.set_cookie(
            'csrf_token',
            generate_csrf(),
            secure=in_production,
            samesite='Strict' if in_production else 'Lax',
            httponly=True)
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'same-origin')
        return response

    @app.errorhandler(HTTPException)
    def api_errors(err):
        # API callers get JSON errors instead of HTML pages.
        if request.path.startswith('/api/'):
            return jsonify({'errors': [err.description]}), err.code
        return err

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def react_root(path):
        if path.startswith('api/'):
            return {'errors': ['Not found']}, 404
        # Top-level build files (favicon, manifest, ...), else the React app,
        # whose router handles the path.
        if path and os.path.isfile(os.path.join(BUILD_DIR, path)):
            return send_from_directory(BUILD_DIR, path)
        if not os.path.isfile(os.path.join(BUILD_DIR, 'index.html')):
            return ('The React app has not been built yet. Run '
                    '`npm run build` in react-app/, or use `npm start` '
                    'for development.'), 404
        return send_from_directory(BUILD_DIR, 'index.html')

    return app


app = create_app()
