import logging
import os
from flask import has_request_context, request

def setup_logging(app):
    """Configures the application logger."""
    
    # Ensure the log directory exists
    log_dir = app.config.get('LOG_DIR', 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Create a standard file handler (not rotating) to avoid permission issues
    log_file = os.path.join(log_dir, 'app.log')
    file_handler = logging.FileHandler(log_file)
    
    # Set the format for the log messages
    formatter = logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    )
    file_handler.setFormatter(formatter)
    
    # Set the logging level from the app's config (or default to INFO)
    log_level = logging.INFO
    if app.debug:
        log_level = logging.DEBUG
        
    file_handler.setLevel(log_level)

    # Add the handler to the default Flask logger
    app.logger.addHandler(file_handler)
    app.logger.setLevel(log_level)
    app.logger.info('Smart Attendance System startup')
