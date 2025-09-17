from flask import Flask
from flask_migrate import Migrate
from config import config_by_name
from models import Student, User, AttendanceRecord
from routes.registration import registration_bp
from routes.view_routes import view_bp
from routes.dashboard import dashboard_bp
from routes.auth import auth_bp
from services.attendance_service import load_known_faces, initialize_models
from extensions import db, migrate, limiter, csrf, login_manager, bcrypt
from utils.logger import setup_logging
from routes.admin import admin_bp

def create_app(config_name='development'):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

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
    csrf.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth_api.login'
    login_manager.login_message_category = 'info'

    # Register the blueprint
    app.register_blueprint(registration_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    

    with app.app_context():
        print("Application context created. Loading known faces from the database...")
        initialize_models()
        load_known_faces()

    return app

# Create the app instance for running
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
