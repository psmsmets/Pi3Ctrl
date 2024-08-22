# absolute imports
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func


__all__ = ['db', 'Trigger']


db = SQLAlchemy()


def dump_datetime(value):
    """Deserialize datetime object into string form for JSON processing."""
    if value is None:
        return None
    return value.strftime("%Y-%m-%d") + " " + value.strftime("%H:%M:%S")


# Define the Trigger class
class Trigger(db.Model):
    """Database table containing all GPIO trigger events, recording both the timestamp and pin."""
    __tablename__ = 'triggers'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    pin = db.Column(db.Integer, nullable=False)
    created = db.Column(db.TIMESTAMP, nullable=False, server_default=func.current_timestamp())

    @property
    def serialize(self):
       """Return object data in easily serializable format"""
       return {
           "id" : self.id,
           "pin": self.pin,
           "created" : dump_datetime(self.created)
       }
