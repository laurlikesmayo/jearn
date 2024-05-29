from flask import Flask
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os import path
from flask_login import LoginManager
from sqlalchemy import MetaData
convention={
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata= MetaData(naming_convention=convention)
app = Flask(__name__)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)



def createapp():

    #configurations of the app, setting up database and initialising
    app.secret_key = 'hello'
    app.permanent_session_lifetime = timedelta(days = 5)

    app.config['SECRET_KEY']='hello'
    app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS']= False

    login_manager = LoginManager()

    login_manager.login_view = '/'  # The view to redirect to when the user needs to log in

    
    db.init_app(app)
    #gets all the website routes from views.py
    from .views import views
    app.register_blueprint(views, url_prefix='/')


    #gets the user information from the database 
    from .models import Users
    createdatabase(app)

    #returning the app 
    return app

#creating a database for the website if its not created
def createdatabase(app):
    if not path.exists("website/database.db"):
        db.create_all(app = app)
        print("created")
