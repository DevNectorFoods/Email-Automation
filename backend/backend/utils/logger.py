import logging
import sys
from ..config import Config

def setup_logging():
    """Setup application logging configuration."""
    
    # Convert string log level to logging constant
    log_level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    log_level = log_level_map.get(Config.LOG_LEVEL.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('email_automation.log', mode='a')
        ]
    )
    
    # Set specific logger levels
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Reduce Flask request logs
    logging.getLogger('urllib3').setLevel(logging.WARNING)   # Reduce HTTP request logs
    
    # Create application logger
    app_logger = logging.getLogger('email_automation')
    app_logger.info("Logging configured successfully")
    
    return app_logger

def get_logger(name: str):
    """Get a logger instance with the specified name."""
    return logging.getLogger(name)
