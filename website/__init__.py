from flask import Flask
from datetime import timedelta
app = Flask(__name__)


def createapp():

    #configurations of the app, setting up database and initialising
    app.secret_key = 'hello'
    app.permanent_session_lifetime = timedelta(days = 5)

    app.config['SECRET_KEY']='hello'

    #gets all the website routes from views.py
    from .views import views
    app.register_blueprint(views, url_prefix='/')


    #returning the app 
    return app

