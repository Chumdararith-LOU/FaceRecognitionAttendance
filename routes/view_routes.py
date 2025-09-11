from flask import Blueprint, render_template

view_bp = Blueprint('views', __name__)

@view_bp.route('/')
def registration_page():
    """Serves the main registration page."""
    return render_template('index.html')