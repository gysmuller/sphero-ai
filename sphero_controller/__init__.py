"""
Sphero Controller Package

This package provides a web interface for controlling a Sphero robot.
"""

from flask import Flask
from flask_socketio import SocketIO
import signal
import sys

from . import config
from . import sphero_connection as sphero
from . import routes
from . import socket_handlers

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
socket_handlers.register_handlers(socketio)

# Signal handlers for graceful shutdown
def cleanup(signum, frame):
    """Graceful shutdown: disconnect Sphero."""
    print(f"\nReceived signal {signum}. Shutting down...")
    
    # Signal random movement to stop
    from . import random_movement
    random_movement.stop_random_movement = True
    
    # Acquire lock to prevent conflict with connection attempts
    if sphero.connection_lock.acquire(blocking=True, timeout=2): 
        try:
            if sphero.is_connected and sphero.api_instance:
                print("Closing Sphero connection...")
                try:
                    sphero.disconnect_sphero()
                    print("Sphero connection closed.")
                except Exception as e:
                    print(f"Error closing connection during shutdown: {e}")
            else:
                print("No active Sphero connection to close.")
        finally:
            sphero.connection_lock.release()
            print("Connection lock released during shutdown.")
    else:
        print("Could not acquire lock during shutdown, connection might be held.")

    print("Exiting.")
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

def create_app():
    """
    Create and configure the Flask application.
    
    Returns:
        Tuple of (app, socketio)
    """
    return app, socketio 