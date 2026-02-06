import logging
import logging.handlers
import os
from datetime import datetime

# Create logs directory if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'app.log')

# Create logger
logger = logging.getLogger('salesforce_app')
logger.setLevel(logging.DEBUG)

# Create rotating file handler (100MB max, keep 5 backups)
handler = logging.handlers.RotatingFileHandler(
    LOG_FILE,
    maxBytes=100 * 1024 * 1024,  # 100MB
    backupCount=5
)

# Create formatter
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

def log_action(action_type, user=None, details=None, status='success', error=None):
    """
    Log user actions and API calls
    
    Args:
        action_type: Type of action (e.g., 'API_REQUEST', 'LOGIN', 'CREATE_LEAD', 'CLICK')
        user: Username or user ID
        details: Additional details about the action
        status: 'success' or 'error'
        error: Error message if status is 'error'
    """
    message = f"ACTION: {action_type}"
    
    if user:
        message += f" | USER: {user}"
    
    if details:
        message += f" | DETAILS: {details}"
    
    message += f" | STATUS: {status}"
    
    if error:
        message += f" | ERROR: {error}"
    
    if status == 'error':
        logger.error(message)
    else:
        logger.info(message)
