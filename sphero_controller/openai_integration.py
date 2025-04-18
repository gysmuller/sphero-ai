"""
OpenAI Integration Module

This module handles integration with OpenAI APIs for the Sphero controller.
"""

import os
import json
import requests
import openai
from dotenv import load_dotenv
from .sphero_prompts import SPHERO_CONTROL_PROMPT

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
try:
    openai_client = openai.OpenAI()
    if not openai_client.api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
except Exception as e:
    print(f"Error initializing OpenAI client: {e}")
    print("Please ensure your OPENAI_API_KEY is set correctly in the .env file.")

# Define the OpenAI function tool for starting random movement
start_random_movement_tool = {
    "type": "function",
    "name": "start_sphero_random_movement",
    "description": "Starts the Sphero robot moving randomly with dim lights.",
    "parameters": {
        "type": "object",
        "properties": {}, # No parameters needed for this function
        "required": []
    }
}

def create_realtime_session():
    """
    Create an OpenAI Realtime session and return the session details.
    
    Returns:
        Tuple of (success, response_data)
    """
    try:
        # Make a request to the OpenAI REST API to create a session
        response = requests.post(
            "https://api.openai.com/v1/realtime/sessions",
            headers={
                "Authorization": f"Bearer {openai_client.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-realtime-preview-2024-12-17",
                "voice": "verse",
                "tools": [start_random_movement_tool], # Provide the function tool
                "tool_choice": "auto", # Let the model decide when to call the function
                "instructions": SPHERO_CONTROL_PROMPT
            }
        )
        response.raise_for_status() # Raise exception for bad status codes
        return True, response.json()
        
    except requests.exceptions.RequestException as e:
        error_message = str(e)
        if e.response is not None:
            print(f"Response status: {e.response.status_code}")
            print(f"Response body: {e.response.text}")
            error_message = f"{error_message} - Status: {e.response.status_code}"
        return False, {"error": f"Failed to create OpenAI session: {error_message}"}
    except Exception as e:
        return False, {"error": f"Unexpected error creating OpenAI session: {str(e)}"}

def get_openai_api_key():
    """
    Get the OpenAI API key from the environment.
    
    Returns:
        The API key or None if not set
    """
    return openai_client.api_key if openai_client else None 