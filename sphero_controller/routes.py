"""
Flask Routes Module

This module contains the Flask routes for the Sphero Web Control Interface.
"""

from flask import render_template, jsonify, request
from . import openai_integration

def register_routes(app):
    """
    Register all Flask routes with the application.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/')
    def index():
        """Render the main control page."""
        return render_template('index.html')

    @app.route('/session', methods=['POST'])
    def create_openai_session():
        """Create an OpenAI Realtime session and return the ephemeral token."""
        print("Received request to create OpenAI Realtime session...")
        
        success, response_data = openai_integration.create_realtime_session()
        
        if success:
            print("OpenAI Realtime session created successfully.")
            return jsonify(response_data)
        else:
            print(f"Error creating OpenAI session: {response_data.get('error')}")
            return jsonify(response_data), 500 