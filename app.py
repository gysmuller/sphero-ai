#!/usr/bin/env python3
"""
Sphero Web Control Interface

This script provides a web interface for controlling a Sphero robot
using Flask and Flask-SocketIO.
"""

import sys
from sphero_controller import create_app, config

def main():
    """Main entry point for the application."""
    print("Starting Sphero Web Control Interface...")
    print(f"Using async_mode='{config.SOCKETIO_ASYNC_MODE}'")
    print(f"Open your browser and navigate to http://localhost:{config.PORT}")
    
    app, socketio = create_app()
    
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