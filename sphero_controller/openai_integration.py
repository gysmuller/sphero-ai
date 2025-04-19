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

def call_openai_response_api(transcript):
    """
    Call the OpenAI Response API with the transcript.
    
    Args:
        transcript (str): The transcript text to send to the API
        
    Returns:
        dict: The API response data or error information
    """
    try:
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=transcript,
            instructions=SPHERO_CONTROL_PROMPT
        )
        return {"success": True, "data": response.output_text}
    except Exception as e:
        error_message = str(e)
        print(f"Error calling OpenAI Response API: {error_message}")
        return {"success": False, "error": error_message}

def create_realtime_session():
    """
    Create an OpenAI Realtime session and return the session details.
    
    Returns:
        Tuple of (success, response_data)
    """
    try:
        # Make a request to the OpenAI REST API to create a session
        response = requests.post(
            "https://api.openai.com/v1/realtime/transcription_sessions",
            headers={
                "Authorization": f"Bearer {openai_client.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "input_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "gpt-4o-transcribe",
                    "prompt": "", 
                    "language": "en"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "input_audio_noise_reduction": {
                    "type": "far_field"
                }
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