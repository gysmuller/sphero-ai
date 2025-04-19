#!/usr/bin/env python3
"""
Sphero Web Control Interface

This script provides a web interface for controlling a Sphero robot
using Flask and Flask-SocketIO.
"""

import sys
import logging
from sphero_controller import app, socketio, config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("app")

def main():
    """Main entry point for the application."""
    logger.info("Starting Sphero Web Control Interface...")
    logger.info(f"Using async_mode='{config.SOCKETIO_ASYNC_MODE}'")
    logger.info(f"Open your browser and navigate to http://localhost:{config.PORT}")
    
    # Run with standard threading mode
    # use_reloader=False is recommended when using threads/signal handling directly
    socketio.run(
        app, 
        host=config.HOST, 
        port=config.PORT, 
        debug=config.DEBUG, 
        use_reloader=False
    )

if __name__ == '__main__':
    main() 