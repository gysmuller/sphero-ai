"""
OpenAI Response Processor

Module for processing OpenAI responses and executing Sphero commands.
"""
import re
import logging
from typing import Tuple, Any, Dict, Optional
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
        transcript: The transcript text from OpenAI
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        Tuple of (success, message)
    """
    logger.info(f"Processing transcript: {transcript}")
    
    if not transcript or not ';' in transcript:
        return True, None
    
    if not sphero.is_connected:
        return False, 'Livvy wants to move, but Sphero is not connected.'
    
    commands = transcript.split(';')
    logger.info(f"Executing {len(commands)} Sphero commands")
    
    for command in commands:
        command = command.strip()
        if not command or command.startswith('#'):
            continue  # Skip empty commands and comments
        
        process_command_line(command)
    
    return True, 'Livvy executed the commands!'

def process_command_line(line: str) -> None:
    """
    Process and execute a single command line.
    
    Args:
        line: The command line to process
    """
    if line.startswith('set_main_led'):
        process_set_color_command(line)
    elif line.startswith('roll'):
        process_roll_command(line)
    elif line.startswith('spin'):
        process_spin_command(line)
    elif line.startswith('set_heading'):
        process_heading_command(line)
    # Add more command processors as needed

def process_set_color_command(line: str) -> None:
    """
    Process and execute a set_main_led command.
    
    Args:
        line: The command line to process
    """
    color_match = re.search(r'Color\(r=(\d+),\s*g=(\d+),\s*b=(\d+)\)', line)
    if color_match:
        r = int(color_match.group(1))
        g = int(color_match.group(2))
        b = int(color_match.group(3))
        logger.info(f"Setting color to RGB({r},{g},{b})")
        sphero.set_main_led(r, g, b)

def process_roll_command(line: str) -> None:
    """
    Process and execute a roll command.
    
    Args:
        line: The command line to process
    """
    roll_match = re.search(r'roll\((\d+),\s*(\d+),\s*([\d.]+)\)', line)
    if roll_match:
        heading = int(roll_match.group(1))
        speed = int(roll_match.group(2))
        duration = float(roll_match.group(3))
        logger.info(f"Rolling with heading {heading}, speed {speed}, duration {duration}")
        sphero.roll(heading, speed, duration)

def process_spin_command(line: str) -> None:
    """
    Process and execute a spin command.
    
    Args:
        line: The command line to process
    """
    spin_match = re.search(r'spin\(([-\d]+),\s*([\d.]+)\)', line)
    if spin_match:
        degrees = int(spin_match.group(1))
        duration = float(spin_match.group(2))
        logger.info(f"Spinning {degrees} degrees over {duration} seconds")
        sphero.spin(degrees, duration)

def process_heading_command(line: str) -> None:
    """
    Process and execute a set_heading command.
    
    Args:
        line: The command line to process
    """
    heading_match = re.search(r'set_heading\((\d+)\)', line)
    if heading_match:
        heading = int(heading_match.group(1))
        logger.info(f"Setting heading to {heading} degrees")
        sphero.set_heading(heading) 