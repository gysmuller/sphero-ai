"""
Application Configuration Module

This module contains the configuration settings for the Sphero Web Control Interface.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Flask configuration
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'sphero-control-secret')
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 't')
HOST = os.getenv('HOST', '0.0.0.0')
PORT = int(os.getenv('PORT', '4000'))

# Socket.IO configuration
SOCKETIO_ASYNC_MODE = 'threading'
SOCKETIO_CORS_ALLOWED_ORIGINS = "*"

# Sphero configuration
SPHERO_SCAN_TIMEOUT = int(os.getenv('SPHERO_SCAN_TIMEOUT', '10')) 