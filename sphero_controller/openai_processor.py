"""
OpenAI Response Processor

Module for processing OpenAI responses and executing Sphero commands.
"""
import re
from . import sphero_connection as sphero
from . import random_movement
from .openai_integration import call_openai_response_api

def process_openai_response(server_event, socketio):
    """
    Process OpenAI response data and execute corresponding Sphero commands.
    
    Args:
        server_event (dict): The OpenAI server event data
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        bool: Success status
        str: Status message
    """
    try:
        if not server_event:
            return False, 'Invalid OpenAI response data'
        
        if server_event.get('type') == "conversation.item.input_audio_transcription.completed":
            print("Input audio transcription completed")
            print(server_event)
            transcript = server_event.get('transcript', '')
            process_response_output(transcript, socketio)
            return True, 'OpenAI response processed'

        # Handle errors
        elif server_event.get('type') == "error":
            error_msg = server_event.get('message', 'Unknown error')
            print(f"OpenAI Error Event: {error_msg}")
            return False, f'OpenAI Error: {error_msg}'
        
        return True, 'OpenAI response processed'
            
    except Exception as e:
        print(f"Error processing OpenAI response: {str(e)}")
        return False, f'Error processing response: {str(e)}'

def process_response_output(transcript, socketio):
    """
    Process the output items from OpenAI response.
    
    Args:
        transcript (str): The transcript to send to the Response API
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        bool: Success status
        str: Status message
    """

    # Call the OpenAI Response API
    response_message = call_openai_response_api(transcript)
    process_transcript(response_message.get("data"), socketio)
    
    return True, 'Response processed'

def handle_random_movement(socketio):
    """
    Handle random movement function call.
    
    Args:
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        bool: Success status
        str: Status message
    """
    print("Function call detected: start_sphero_random_movement")
    
    # Check if Sphero is connected before starting movement
    if sphero.is_connected:
        return random_movement.start_random_movement(socketio)
    else:
        return False, 'Livvy wants to move, but Sphero is not connected.'

def process_transcript(transcript, socketio):
    """
    Process transcript from OpenAI response and execute commands.
    
    Args:
        transcript (str): The transcript text from OpenAI
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        bool: Success status
        str: Status message
    """
    print(f"Processing transcript: {transcript}")
    
    if not transcript or not ';' in transcript:
        return True, None
    
    if not sphero.is_connected:
        return False, 'Livvy wants to move, but Sphero is not connected.'
    
    commands = transcript.split(';')
    print(f"Executing {len(commands)} Sphero commands")
    
    for command in commands:
        command = command.strip()
        if not command or command.startswith('#'):
            continue  # Skip empty commands and comments
        
        process_command_line(command)
    
    return True, 'Livvy executed the commands!'

def process_command_line(line):
    """
    Process and execute a single command line.
    
    Args:
        line (str): The command line to process
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

def process_set_color_command(line):
    """
    Process and execute a set_main_led command.
    
    Args:
        line (str): The command line to process
    """
    color_match = re.search(r'Color\(r=(\d+),\s*g=(\d+),\s*b=(\d+)\)', line)
    if color_match:
        r = int(color_match.group(1))
        g = int(color_match.group(2))
        b = int(color_match.group(3))
        print(f"Setting color to RGB({r},{g},{b})")
        sphero.set_main_led(r, g, b)

def process_roll_command(line):
    """
    Process and execute a roll command.
    
    Args:
        line (str): The command line to process
    """
    roll_match = re.search(r'roll\((\d+),\s*(\d+),\s*([\d.]+)\)', line)
    if roll_match:
        heading = int(roll_match.group(1))
        speed = int(roll_match.group(2))
        duration = float(roll_match.group(3))
        print(f"Rolling with heading {heading}, speed {speed}, duration {duration}")
        sphero.roll(heading, speed, duration)

def process_spin_command(line):
    """
    Process and execute a spin command.
    
    Args:
        line (str): The command line to process
    """
    spin_match = re.search(r'spin\(([-\d]+),\s*([\d.]+)\)', line)
    if spin_match:
        degrees = int(spin_match.group(1))
        duration = float(spin_match.group(2))
        print(f"Spinning {degrees} degrees over {duration} seconds")
        sphero.spin(degrees, duration)

def process_heading_command(line):
    """
    Process and execute a set_heading command.
    
    Args:
        line (str): The command line to process
    """
    heading_match = re.search(r'set_heading\((\d+)\)', line)
    if heading_match:
        heading = int(heading_match.group(1))
        print(f"Setting heading to {heading} degrees")
        # May need to implement set_heading in sphero_connection.py
        if hasattr(sphero, 'set_heading'):
            sphero.set_heading(heading)
        else:
            # Fallback implementation using roll with speed 0
            sphero.roll(heading, 0, 0.1) 