from flask import Flask
from flask_migrate import Migrate
from config import config_by_name
from models import Student, User, AttendanceRecord
from routes.registration import registration_bp
from routes.view_routes import view_bp
from routes.dashboard import dashboard_bp
from services.attendance_service import load_known_faces
from flask_login import LoginManager
from routes.auth import auth_bp
from services.attendance_service import load_known_faces, initialize_models
from extensions import db, migrate, limiter 
from utils.logger import setup_logging

def create_app(config_name='development'):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth_api.login' # type: ignore

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Register the view blueprint
    app.register_blueprint(view_bp)
    app.register_blueprint(dashboard_bp)

    # --- INITIALIZE LOGGER ---
    setup_logging(app)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    # Register the blueprint
    app.register_blueprint(registration_bp)
    app.register_blueprint(auth_bp)
    
    #  A simple test route
    @app.route('/')
    def hello():
        return "Smart Attendance System is running!"
    
    with app.app_context():
        print("Application context created. Loading known faces from the database...")
        initialize_models()
        load_known_faces()

    return app

# Create the app instance for running
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
