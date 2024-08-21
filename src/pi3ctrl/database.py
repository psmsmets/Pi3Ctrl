# absolute imports
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


__all__ = []


db = SQLAlchemy()


# Define the Trigger class
class Trigger(db.Model):
    """Database table containing all trigger events, recording both the timestamp and pin."""
    __tablename__ = 'triggers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=func.current_timestamp())
    pin = db.Column(db.Integer, nullable=False)
