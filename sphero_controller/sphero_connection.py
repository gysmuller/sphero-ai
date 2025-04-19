"""
Sphero Connection Module

This module handles the connection to Sphero robots using the spherov2 library.
"""

import threading
import sys
from typing import Optional, Tuple, Any

try:
    from spherov2 import scanner
    from spherov2.sphero_edu import SpheroEduAPI
    from spherov2.types import Color
except ImportError:
    print("Error: spherov2 module not found!")
    print("Please install it with: pip install spherov2")
    sys.exit(1)

# Global variables for connection state
sphero_toy = None
sphero_api = None
is_connected = False
api_instance = None  # Will hold the context manager instance
connection_lock = threading.Lock()

# Configurable settings
MAX_SPEED = 30  # Maximum allowed speed (0-255)
MAX_BRIGHTNESS = 50  # Maximum brightness limit (0-255)

def scan_for_spheros(timeout: int = 10) -> list:
    """
    Scan for available Sphero toys.
    
    Args:
        timeout: Time in seconds to scan for devices
        
    Returns:
        List of found Sphero toys
    """
    return scanner.find_toys(toy_names=None, timeout=timeout)

def connect_to_sphero(toy) -> Tuple[bool, str]:
    """
    Connect to a specific Sphero toy.
    
    Args:
        toy: The Sphero toy object to connect to
        
    Returns:
        Tuple of (success, message)
    """
    global sphero_toy, sphero_api, is_connected, api_instance
    
    try:
        print(f"Attempting to connect to: {toy}")
        api_context = SpheroEduAPI(toy)
        api_instance = api_context.__enter__()
        sphero_api = api_instance
        sphero_toy = toy
        is_connected = True
        return True, f"Connected to {toy}!"
    except Exception as e:
        print(f"Connection Exception: {str(e)}")
        # Clean up partial connection
        sphero_toy = None
        api_instance = None
        sphero_api = None
        is_connected = False
        return False, f"Connection error: {str(e)}"

def disconnect_sphero() -> Tuple[bool, str]:
    """
    Disconnect from the currently connected Sphero.
    
    Returns:
        Tuple of (success, message)
    """
    global sphero_api, is_connected, api_instance, sphero_toy
    
    if not is_connected or not api_instance:
        return False, "Not connected to any Sphero"
    
    try:
        print(f"Disconnecting from {sphero_toy}...")
        api_instance.__exit__(None, None, None)
        api_instance = None
        sphero_api = None
        is_connected = False
        sphero_toy = None
        return True, "Disconnected from Sphero"
    except Exception as e:
        return False, f"Error disconnecting: {str(e)}"

def get_connection_status() -> dict:
    """
    Get the current connection status.
    
    Returns:
        Dictionary with connection status information
    """
    return {
        'connected': is_connected,
        'toy': str(sphero_toy) if sphero_toy else None
    }

def set_brightness_limit(limit: int) -> Tuple[bool, str]:
    """
    Set the brightness limit for the Sphero LED.
    
    Args:
        limit: Brightness limit (0-255)
        
    Returns:
        Tuple of (success, message)
    """
    global MAX_BRIGHTNESS
    
    try:
        # Ensure value is in range 0-255
        limit = max(0, min(255, limit))
        MAX_BRIGHTNESS = limit
        return True, f'Brightness limit set to {limit}'
    except Exception as e:
        return False, f'Error setting brightness limit: {str(e)}'

def get_brightness_limit() -> int:
    """
    Get the current brightness limit.
    
    Returns:
        Current brightness limit value
    """
    return MAX_BRIGHTNESS

def set_main_led(r: int, g: int, b: int) -> Tuple[bool, str]:
    """
    Set the main LED color of the Sphero with brightness limit applied.
    
    Args:
        r: Red color component (0-255)
        g: Green color component (0-255)
        b: Blue color component (0-255)
        
    Returns:
        Tuple of (success, message)
    """
    if not is_connected or not sphero_api:
        return False, "Not connected to any Sphero"
    
    try:
        # Ensure values are in range 0-255
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        
        # Apply brightness limit
        brightness_factor = MAX_BRIGHTNESS / 255.0
        r_adj = int(r * brightness_factor)
        g_adj = int(g * brightness_factor)
        b_adj = int(b * brightness_factor)
        
        sphero_api.set_main_led(Color(r=r_adj, g=g_adj, b=b_adj))
        return True, f'Color set to RGB({r},{g},{b}) with brightness {MAX_BRIGHTNESS}'
    except Exception as e:
        return False, f'Error setting color: {str(e)}'

def roll(heading: int, speed: int, duration: float) -> Tuple[bool, str]:
    """
    Make the Sphero roll in a specific direction.
    
    Args:
        heading: Direction in degrees (0-359)
        speed: Speed (0-255)
        duration: Duration in seconds
        
    Returns:
        Tuple of (success, message)
    """
    if not is_connected or not sphero_api:
        return False, "Not connected to any Sphero"
    
    try:
        # Ensure values are in valid ranges
        heading = max(0, min(359, heading))
        speed = max(0, min(MAX_SPEED, speed))
        
        sphero_api.roll(heading, speed, duration)
        return True, f'Rolling with heading {heading}, speed {speed}'
    except Exception as e:
        return False, f'Error rolling: {str(e)}'

def spin(degrees: int, duration: float) -> Tuple[bool, str]:
    """
    Make the Sphero spin in place.
    
    Args:
        degrees: Degrees to spin
        duration: Duration in seconds
        
    Returns:
        Tuple of (success, message)
    """
    if not is_connected or not sphero_api:
        return False, "Not connected to any Sphero"
    
    try:
        sphero_api.spin(degrees, duration)
        return True, f'Spinning {degrees} degrees'
    except Exception as e:
        return False, f'Error spinning: {str(e)}' 