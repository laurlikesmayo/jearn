from . import db
from flask_login import UserMixin
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.dialects.postgresql import JSON
from flask_migrate import Migrate
from datetime import datetime, date
import json

def default_list():
    return []

#puts all the users information into the database
class Users(db.Model, UserMixin):
    id = db.Column("id", db.Integer, primary_key = True)
    date_added = db.Column(db.DateTime, default=datetime.now)
    username = db.Column(db.String(50), unique=True, nullable = False)
    email = db.Column(db.String(50), unique=True, nullable = False)
    password = db.Column(db.String(50), nullable = False)
    preferences = db.relationship('UserPreferences', backref = 'preferences')
    dailytopic = db.relationship('DDOE', backref = 'preferences')
    notes = db.relationship('SavedContent', backref = 'savedcontent')




class UserPreferences(db.Model, UserMixin):
    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    age = db.Column(db.Integer, default=20)
    language = db.Column(db.String(50), default="English")
    subjects = db.Column(MutableList.as_mutable(JSON), default=[])
    strengths = db.Column(MutableList.as_mutable(JSON), default=[])  # Correct spelling
    weaknesses = db.Column(MutableList.as_mutable(JSON), default=[])


class DDOE(db.Model, UserMixin):
    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_updated = db.Column(db.Date, default=date.today)
    previous_topics = db.Column(MutableList.as_mutable(JSON), default=[])
    previous_words = db.Column(MutableList.as_mutable(JSON), default=[])
    word = db.Column(db.String(50))
    definition = db.Column(db.String(5000))
    current_streak = db.Column(db.Integer, default=1)
    topic = db.Column(db.String(500))
    description = db.Column(db.String(1000))
    examples = db.Column(db.String(1000))

class SavedContent(db.Model, UserMixin):
    id = db.Column('id', db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(500))
    content = db.Column(db.String(10000)) #video URL
    note = db.Column(db.String(10000))





    
