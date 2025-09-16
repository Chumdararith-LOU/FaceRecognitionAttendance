# In extensions.py

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt  # Add this import
from flask_login import LoginManager # Add this import


# Initialize extensions here
csrf = CSRFProtect()
db = SQLAlchemy()
migrate = Migrate()
bcrypt = Bcrypt() # Add bcrypt initialization
login_manager = LoginManager() # Add login_manager initialization

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)