# In utils/logger.py

import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Configures the application logger."""
    
    # Ensure the log directory exists
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # Create a rotating file handler to limit log file size
    file_handler = RotatingFileHandler(
        'logs/app.log', 
        maxBytes=10240,  # 10 KB per file
        backupCount=10   # Keep 10 old log files
    )
    
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