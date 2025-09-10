from flask import Flask
from flask_migrate import Migrate
from config import config_by_name
from models.database import db
from models import Student

migrate = Migrate()

def create_app(config_name='development'):
    """
    Application factory function.
    """
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # A simple test route
    @app.route('/')
    def hello():
        return "Smart Attendance System is running!"

    return app

# Create the app instance for running
app = create_app()

if __name__ == '__main__':
    app.run(debug=True)