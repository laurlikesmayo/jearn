from flask import Flask
from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from os import path
from flask_caching import Cache
from sqlalchemy import MetaData
convention={
    "ix": 'ix_%(column_0_label)s',
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}
app = Flask(__name__)

# Configurations
app.secret_key = 'hello'
app.permanent_session_lifetime = timedelta(days=5)
app.config['SECRET_KEY'] = 'hello'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=1)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['CACHE_TYPE'] = 'RedisCache'
app.config['CACHE_REDIS_HOST'] = 'localhost'
app.config['CACHE_REDIS_PORT'] = 6379
app.config['CACHE_DEFAULT_TIMEOUT'] = 0  # Cache timeout (in seconds)

# Initialize the cache
cache = Cache(app)

# Initialize extensions
metadata = MetaData(naming_convention =convention)
db = SQLAlchemy(app)
migrate = Migrate(app, db, render_as_batch=True)

# Setup login manager
login_manager = LoginManager()
login_manager.login_view = 'login'  # The view to redirect to when the user needs to log in
login_manager.init_app(app)

# Import and register blueprints
from .views import views
app.register_blueprint(views, url_prefix='/')

# Import models
from .models import Users, UserPreferences

# Setup user loader function
@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id))

# Create database if it doesn't exist
with app.app_context():
    if not path.exists("website/database.db"):
        db.create_all()
        print("Database created")
