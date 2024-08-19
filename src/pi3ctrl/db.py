# absolute imports
import sqlite3
from flask import current_app as app
from flask import g


__all__ = ['get_db', 'query_db', 'init_db']


# https://flask.palletsprojects.com/en/latest/patterns/sqlite3/


def get_db(DATABASE: str = None):
    """Returns the database object."""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE or app.config['DATABASE'])
    return db


def query_db(query, args=(), one=False):
    """Returns the database object."""
    with app.app_context():
        cur = get_db().execute(query, args)
        rv = cur.fetchall()
        cur.close()
    return (rv[0] if rv else None) if one else rv


def init_db():
    """Initialize the sqlite3 database."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()
