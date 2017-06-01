from datetime import datetime
from dateutil import parser

from . import db


class Post(db.Model):
    """
    The post model
    """
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), index=True)
    trip_id = db.Column(db.Integer, index=True)
    public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow())
    lon = db.Column(db.Float)
    lat = db.Column(db.Float)
    location = db.Column(db.String(128))
    title = db.Column(db.String(256))
    content = db.Column(db.Text())

    def __init__(self, **kwargs):
        if 'created_at' in kwargs and type(kwargs['created_at']) is str:
            kwargs['created_at'] = parser.parse(kwargs['created_at'])
        if 'created_at' not in kwargs:
            kwargs['created_at'] = datetime.utcnow()
        super(Post, self).__init__(**kwargs)

    def to_json(self):
        return {"id": self.id,
                "username": self.username,
                "trip_id": self.trip_id,
                "created_at": self.created_at.isoformat(),
                "location": self.location,
                "lon": self.lon,
                "lat": self.lat,
                "title": self.title,
                "content": self.content}
