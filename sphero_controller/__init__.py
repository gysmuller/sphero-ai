"""
Sphero Controller Package

This package provides a web interface for controlling a Sphero robot.
"""

import logging
from typing import Tuple, Any
from flask import Flask
from flask_socketio import SocketIO
import signal
import sys

from . import config
from . import sphero_connection
from . import random_movement
from . import routes
from . import socket_handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sphero_controller")

# Global instances accessed from other modules
sphero = sphero_connection.sphero
random_movement_mgr = random_movement.random_movement_manager
socket_handler = socket_handlers.socket_handlers

def create_app() -> Tuple[Flask, SocketIO]:
    """
    Create and configure the Flask application.
    
    Returns:
        Tuple of (app, socketio)
    """
    # Initialize Flask application
    app = Flask(__name__, template_folder='../templates', static_folder='../static')
    app.config['SECRET_KEY'] = config.FLASK_SECRET_KEY
    
    # Initialize Socket.IO
    socketio = SocketIO(
        app, 
        cors_allowed_origins=config.SOCKETIO_CORS_ALLOWED_ORIGINS, 
        async_mode=config.SOCKETIO_ASYNC_MODE
    )
    
    # Register routes and socket handlers
    routes.register_routes(app)
    socket_handlers.socket_handlers.register_handlers(socketio)
    
    # Set up signal handlers
    setup_signal_handlers()
    
    logger.info(f"Sphero Controller application initialized with async_mode={config.SOCKETIO_ASYNC_MODE}")
    return app, socketio

def setup_signal_handlers() -> None:
    """Set up signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    logger.info("Signal handlers registered for graceful shutdown")

def cleanup(signum: int, frame: Any) -> None:
    """
    Graceful shutdown: disconnect Sphero.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info(f"Received signal {signum}. Shutting down...")
    
    # Signal random movement to stop
    random_movement_mgr._stop_random_movement = True
    
    # Acquire lock to prevent conflict with connection attempts
    if sphero.connection_lock.acquire(blocking=True, timeout=2): 
        try:
            if sphero.is_connected and sphero._api_instance:
                logger.info("Closing Sphero connection...")
                try:
                    sphero.disconnect_sphero()
                    logger.info("Sphero connection closed.")
                except Exception as e:
                    logger.error(f"Error closing connection during shutdown: {e}")
            else:
                logger.info("No active Sphero connection to close.")
        finally:
            sphero.connection_lock.release()
            logger.info("Connection lock released during shutdown.")
    else:
        logger.warning("Could not acquire lock during shutdown, connection might be held.")

    logger.info("Exiting.")
    sys.exit(0)

# Initialize Flask application and Socket.IO when imported
app, socketio = create_app() 