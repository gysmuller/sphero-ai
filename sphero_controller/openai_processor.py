"""
OpenAI Response Processor

Module for processing OpenAI responses and executing Sphero commands.
"""
import re
import json
import logging
from typing import Tuple, Any, Dict, Optional, List
from . import sphero_connection
from . import random_movement
from .openai_integration import call_openai_response_api

# Configure logging
logger = logging.getLogger("openai_processor")

# Get the singleton instances
sphero = sphero_connection.sphero
random_movement_mgr = random_movement.random_movement_manager

def process_openai_response(server_event: Dict[str, Any], socketio: Any) -> Tuple[bool, Optional[str]]:
    """
    Process OpenAI response data and execute corresponding Sphero commands.
    
    Args:
        server_event: The OpenAI server event data
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        Tuple of (success, message)
    """
    try:
        if not server_event:
            return False, 'Invalid OpenAI response data'
        
        if server_event.get('type') == "conversation.item.input_audio_transcription.completed":
            logger.info("Input audio transcription completed")
            logger.debug(f"Server event: {server_event}")
            transcript = server_event.get('transcript', '')
            process_response_output(transcript, socketio)
            return True, 'OpenAI response processed'

        # Handle errors
        elif server_event.get('type') == "error":
            error_msg = server_event.get('message', 'Unknown error')
            logger.error(f"OpenAI Error Event: {error_msg}")
            return False, f'OpenAI Error: {error_msg}'
        
        return True, 'OpenAI response processed'
            
    except Exception as e:
        logger.error(f"Error processing OpenAI response: {str(e)}")
        return False, f'Error processing response: {str(e)}'

def process_response_output(transcript: str, socketio: Any) -> Tuple[bool, Optional[str]]:
    """
    Process the output items from OpenAI response.
    
    Args:
        transcript: The transcript to send to the Response API
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        Tuple of (success, message)
    """
    # Call the OpenAI Response API
    response_message = call_openai_response_api(transcript)
    process_transcript(response_message.get("data"), socketio)
    
    return True, 'Response processed'

def handle_random_movement(socketio: Any) -> Tuple[bool, str]:
    """
    Handle random movement function call.
    
    Args:
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        Tuple of (success, message)
    """
    logger.info("Function call detected: start_sphero_random_movement")
    
    # Check if Sphero is connected before starting movement
    if sphero.is_connected:
        return random_movement_mgr.start_random_movement(socketio)
    else:
        return False, 'Livvy wants to move, but Sphero is not connected.'

def process_transcript(transcript: str, socketio: Any) -> Tuple[bool, Optional[str]]:
    """
    Process transcript from OpenAI response and execute commands.
    
    Args:
        transcript: The JSON-formatted commands from OpenAI
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        Tuple of (success, message)
    """
    logger.info(f"Processing transcript: {transcript}")
    
    if not transcript:
        return True, None
    
    if not sphero.is_connected:
        return False, 'Livvy wants to move, but Sphero is not connected.'
    
    try:
        # Split multiple JSON objects if needed
        command_sets = split_json_objects(transcript)
        total_commands = 0
        
        for command_set in command_sets:
            command_data = json.loads(command_set)
            commands = command_data.get('commands', [])
            total_commands += len(commands)
            
            for cmd in commands:
                command_name = cmd.get('command')
                parameters = cmd.get('parameters', {})
                process_command(command_name, parameters)
        
        logger.info(f"Executed {total_commands} Sphero commands")
        return True, 'Livvy executed the commands!'
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error: {str(e)}")
        return False, f'Error parsing command data: {str(e)}'
    except Exception as e:
        logger.error(f"Error processing commands: {str(e)}")
        return False, f'Error processing commands: {str(e)}'

def split_json_objects(text: str) -> List[str]:
    """
    Split multiple JSON objects in a string.
    
    Args:
        text: String containing potentially multiple JSON objects
        
    Returns:
        List of individual JSON object strings
    """
    result = []
    depth = 0
    start = 0
    
    for i, char in enumerate(text):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0:
                result.append(text[start:i+1])
    
    return result

def process_command(command_name: str, parameters: Dict[str, str]) -> None:
    """
    Process and execute a single command.
    
    Args:
        command_name: The name of the command to execute
        parameters: The parameters for the command
    """
    if command_name == 'set_main_led':
        process_set_color_command(parameters.get('param1', ''))
    elif command_name == 'roll':
        heading = parameters.get('param1', '0')
        speed = parameters.get('param2', '0')
        duration = parameters.get('param3', '1.0')
        logger.info(f"Rolling with heading {heading}, speed {speed}, duration {duration}")
        sphero.roll(int(heading), int(speed), float(duration) if duration else 1.0)
    elif command_name == 'spin':
        degrees = parameters.get('param1', '0')
        duration = parameters.get('param2', '1.0')
        logger.info(f"Spinning {degrees} degrees over {duration} seconds")
        sphero.spin(int(degrees), float(duration) if duration else 1.0)
    elif command_name == 'set_heading':
        heading = parameters.get('param1', '0')
        logger.info(f"Setting heading to {heading} degrees")
        sphero.set_heading(int(heading))
    # Add more command processors as needed

def process_set_color_command(color_param: str) -> None:
    """
    Process and execute a set_main_led command.
    
    Args:
        color_param: The color parameter string
    """
    color_match = re.search(r'Color\(r=(\d+),\s*g=(\d+),\s*b=(\d+)\)', color_param)
    if color_match:
        r = int(color_match.group(1))
        g = int(color_match.group(2))
        b = int(color_match.group(3))
        logger.info(f"Setting color to RGB({r},{g},{b})")
        sphero.set_main_led(r, g, b) 