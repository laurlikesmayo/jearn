from . import db
from flask_login import UserMixin
from flask_migrate import Migrate
from datetime import datetime
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



class UserPreferences(db.Model, UserMixin):
    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    age = db.Column(db.Integer, default=20)
    language = db.Column(db.String(50), default="English")
    subjects = db.Column(db.JSON, default=default_list)
    strengths = db.Column(db.JSON, default=default_list)  # Correct spelling
    weaknesses = db.Column(db.JSON, default=default_list)


class DDOE(db.Model, UserMixin):
    id = db.Column("id", db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    last_updated =  db.Column(db.DateTime, default=datetime.now)
    topic = db.Column(db.String(50))
    description = db.Column(db.String(1000))
    examples = db.Column(db.String(1000))




    
