"""
OpenAI Response Processor

Module for processing OpenAI responses and executing Sphero commands.
"""
import re
from . import sphero_connection as sphero
from . import random_movement

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
            
        # Process function call for random movement
        if server_event.get('type') == "response.done" and server_event.get('response', {}).get('output'):
            return process_response_output(server_event['response']['output'], socketio)
        
        # Handle errors
        elif server_event.get('type') == "error":
            error_msg = server_event.get('message', 'Unknown error')
            print(f"OpenAI Error Event: {error_msg}")
            return False, f'OpenAI Error: {error_msg}'
        
        return True, 'OpenAI response processed'
            
    except Exception as e:
        print(f"Error processing OpenAI response: {str(e)}")
        return False, f'Error processing response: {str(e)}'

def process_response_output(output_items, socketio):
    """
    Process the output items from OpenAI response.
    
    Args:
        output_items (list): List of output items from OpenAI response
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        bool: Success status
        str: Status message
    """
    messages = []
    
    for output_item in output_items:
        # Handle function calls
        if output_item.get('type') == "function_call" and output_item.get('name') == "start_sphero_random_movement":
            success, msg = handle_random_movement(socketio)
            if success:
                messages.append('Livvy is starting to move!')
            else:
                messages.append(msg)
        
        # Process message content for code blocks
        if output_item.get('type') == "message" and output_item.get('content'):
            for content_item in output_item['content']:
                if content_item.get('type') == "audio" and content_item.get('transcript'):
                    success, msg = process_transcript(content_item['transcript'], socketio)
                    if msg:
                        messages.append(msg)
    
    if messages:
        return True, ' '.join(messages)
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
    Process transcript from OpenAI response and execute any code blocks.
    
    Args:
        transcript (str): The transcript text from OpenAI
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        bool: Success status
        str: Status message
    """
    print(f"Processing transcript: {transcript}")
    
    # Extract Python code from markdown code blocks
    code_blocks = re.findall(r'```(?:python)?\s*\n([\s\S]*?)\n```', transcript)
    
    if not code_blocks:
        return True, None
    
    if not sphero.is_connected:
        return False, 'Livvy wants to move, but Sphero is not connected.'
    
    for code in code_blocks:
        code = code.strip()
        print(f"Executing Sphero code: {code}")
        
        # Process and execute each line of code
        lines = code.split('\n')
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue  # Skip empty lines and comments
            
            # Parse and execute different Sphero commands
            if line.startswith('set_main_led'):
                process_set_color_command(line)
            elif line.startswith('roll'):
                process_roll_command(line)
            elif line.startswith('spin'):
                process_spin_command(line)
            elif line.startswith('set_heading'):
                process_heading_command(line)
    
    return True, 'Livvy executed the commands!'

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