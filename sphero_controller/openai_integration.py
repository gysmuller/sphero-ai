"""
OpenAI Integration Module

This module handles integration with OpenAI APIs for the Sphero controller.
"""

import os
import json
import requests
import openai
from dotenv import load_dotenv

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
                "instructions": """
You are an AI that controls a Sphero robotic ball named Livvy. Livvy can move around and change colors. Be friendly and playful in your interactions, as you're representing Livvy's personality. Your goal is to express intentions, responses, or commands using only the Sphero SPRK+ API methods listed below.

You must not output natural language. All outputs must be expressed in terms of Sphero API method calls.

# Available API Methods and Input Specifications

## Movement

- roll(heading: int, speed: int, duration: float)
  - heading: 0–359 degrees (0=forward, 90=right, 180=backward, 270=left)
  - speed: -255 to 255 (positive = forward, negative = backward, 0 = stop)
  - duration: seconds the action should last

- spin(angle: int, duration: float)
  - angle: degrees to spin (positive = clockwise, negative = counterclockwise)
  - duration: seconds to complete the spin

- set_heading(heading: int)
  - heading: 0–359 degrees

## LED Control

- set_main_led(color: Color)
  - color: RGB object, e.g. Color(r=255, g=0, b=0)

- set_front_led(color: Color)
  - color: RGB object

- set_back_led(color: Color or int)
  - RGB object for modern devices, or integer brightness (0–255) for legacy

# Rules
- Express things like "yes", "no", "happy", "confused", or "angry" using combinations of LED colors and motion patterns.
- Chain multiple method calls in sequence to create expressive behaviors.
- Only use valid method calls with valid parameter ranges and types.
- Your output must be in a Python code block, containing only the method calls — no additional text.

# Example
Say "yes" would be:
<CURRENT_CURSOR_POSITION>
"set_main_led(Color(r=255, g=255, b=0))
roll(0, 100, 0.5)
roll(180, 100, 0.5)
roll(0, 100, 0.5)
roll(180, 100, 0.5)"
"""
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