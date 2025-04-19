"""
Flask Routes Module

This module contains the Flask routes for the Sphero controller.
"""

from flask import Flask, render_template, request, jsonify
from . import sphero_connection
from . import openai_integration
import logging

# Configure logging
logger = logging.getLogger("routes")

def register_routes(app: Flask) -> None:
    """
    Register the Flask routes with the application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/')
    def index():
        """Render the main web interface."""
        return render_template('index.html')
    
    @app.route('/api/connection-status', methods=['GET'])
    def connection_status():
        """Get the current connection status."""
        return jsonify(sphero_connection.sphero.get_connection_status())
        
    @app.route('/session', methods=['POST'])
    def create_openai_session():
        """Create an OpenAI Realtime session and return the ephemeral token."""
        logger.info("Received request to create OpenAI Realtime session...")
        
        success, response_data = openai_integration.create_realtime_session()
        
        if success:
            logger.info("OpenAI Realtime session created successfully.")
            return jsonify(response_data)
        else:
            logger.error(f"Error creating OpenAI session: {response_data.get('error')}")
            return jsonify(response_data), 500 