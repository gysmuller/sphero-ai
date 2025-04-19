"""
Sphero Connection Module

This module handles the connection to Sphero robots using the spherov2 library.
"""

import logging
import sys
import threading
from typing import Optional, Tuple, Any, List, Dict, Union

try:
    from spherov2 import scanner
    from spherov2.sphero_edu import SpheroEduAPI
    from spherov2.types import Color
except ImportError:
    logging.error("Error: spherov2 module not found!")
    logging.error("Please install it with: pip install spherov2")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("sphero_connection")

class SpheroConnection:
    """Class for managing Sphero robot connections."""
    
    def __init__(self) -> None:
        """Initialize a new SpheroConnection instance."""
        self._sphero_toy: Any = None
        self._sphero_api: Optional[SpheroEduAPI] = None
        self._is_connected: bool = False
        self._api_instance: Any = None  # Will hold the context manager instance
        self._connection_lock: threading.Lock = threading.Lock()
        
        # Configurable settings
        self._max_speed: int = 30  # Maximum allowed speed (0-255)
        self._max_brightness: int = 50  # Maximum brightness limit (0-255)
    
    @property
    def is_connected(self) -> bool:
        """Get the current connection status."""
        return self._is_connected
    
    @property
    def sphero_toy(self) -> Any:
        """Get the current Sphero toy object."""
        return self._sphero_toy
    
    @property
    def sphero_api(self) -> Optional[SpheroEduAPI]:
        """Get the current Sphero API instance."""
        return self._sphero_api
    
    @property
    def connection_lock(self) -> threading.Lock:
        """Get the connection lock."""
        return self._connection_lock
    
    @property
    def max_speed(self) -> int:
        """Get the maximum allowed speed."""
        return self._max_speed
    
    @max_speed.setter
    def max_speed(self, value: int) -> None:
        """Set the maximum allowed speed."""
        self._max_speed = max(0, min(255, value))
    
    @property
    def max_brightness(self) -> int:
        """Get the maximum brightness limit."""
        return self._max_brightness
    
    @max_brightness.setter
    def max_brightness(self, value: int) -> None:
        """Set the maximum brightness limit."""
        self._max_brightness = max(0, min(255, value))
    
    def scan_for_spheros(self, timeout: int = 10) -> List[Any]:
        """
        Scan for available Sphero toys.
        
        Args:
            timeout: Time in seconds to scan for devices
            
        Returns:
            List of found Sphero toys
        """
        logger.info(f"Scanning for Sphero toys with timeout={timeout}s")
        return scanner.find_toys(toy_names=None, timeout=timeout)
    
    def connect_to_sphero(self, toy: Any) -> Tuple[bool, str]:
        """
        Connect to a specific Sphero toy.
        
        Args:
            toy: The Sphero toy object to connect to
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Attempting to connect to: {toy}")
        
        try:
            api_context = SpheroEduAPI(toy)
            api_instance = api_context.__enter__()
            self._api_instance = api_instance
            self._sphero_api = api_instance
            self._sphero_toy = toy
            self._is_connected = True
            logger.info(f"Connected to {toy}")
            return True, f"Connected to {toy}!"
        except Exception as e:
            logger.error(f"Connection Exception: {str(e)}")
            # Clean up partial connection
            self._sphero_toy = None
            self._api_instance = None
            self._sphero_api = None
            self._is_connected = False
            return False, f"Connection error: {str(e)}"
    
    def disconnect_sphero(self) -> Tuple[bool, str]:
        """
        Disconnect from the currently connected Sphero.
        
        Returns:
            Tuple of (success, message)
        """
        if not self._is_connected or not self._api_instance:
            logger.warning("Disconnect attempted when not connected")
            return False, "Not connected to any Sphero"
        
        try:
            logger.info(f"Disconnecting from {self._sphero_toy}...")
            self._api_instance.__exit__(None, None, None)
            self._api_instance = None
            self._sphero_api = None
            self._is_connected = False
            self._sphero_toy = None
            logger.info("Successfully disconnected")
            return True, "Disconnected from Sphero"
        except Exception as e:
            logger.error(f"Error disconnecting: {str(e)}")
            return False, f"Error disconnecting: {str(e)}"
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the current connection status.
        
        Returns:
            Dictionary with connection status information
        """
        return {
            'connected': self._is_connected,
            'toy': str(self._sphero_toy) if self._sphero_toy else None
        }
    
    def set_brightness_limit(self, limit: int) -> Tuple[bool, str]:
        """
        Set the brightness limit for the Sphero LED.
        
        Args:
            limit: Brightness limit (0-255)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Ensure value is in range 0-255
            limit = max(0, min(255, limit))
            self._max_brightness = limit
            logger.info(f"Brightness limit set to {limit}")
            return True, f'Brightness limit set to {limit}'
        except Exception as e:
            logger.error(f"Error setting brightness limit: {str(e)}")
            return False, f'Error setting brightness limit: {str(e)}'
    
    def set_main_led(self, r: int, g: int, b: int) -> Tuple[bool, str]:
        """
        Set the main LED color of the Sphero with brightness limit applied.
        
        Args:
            r: Red color component (0-255)
            g: Green color component (0-255)
            b: Blue color component (0-255)
            
        Returns:
            Tuple of (success, message)
        """
        if not self._is_connected or not self._sphero_api:
            logger.warning("Set color attempted when not connected")
            return False, "Not connected to any Sphero"
        
        try:
            # Ensure values are in range 0-255
            r = max(0, min(255, r))
            g = max(0, min(255, g))
            b = max(0, min(255, b))
            
            # Apply brightness limit
            brightness_factor = self._max_brightness / 255.0
            r_adj = int(r * brightness_factor)
            g_adj = int(g * brightness_factor)
            b_adj = int(b * brightness_factor)
            
            self._sphero_api.set_main_led(Color(r=r_adj, g=g_adj, b=b_adj))
            logger.info(f"Color set to RGB({r},{g},{b}) with brightness {self._max_brightness}")
            return True, f'Color set to RGB({r},{g},{b}) with brightness {self._max_brightness}'
        except Exception as e:
            logger.error(f"Error setting color: {str(e)}")
            return False, f'Error setting color: {str(e)}'
    
    def roll(self, heading: int, speed: int, duration: float) -> Tuple[bool, str]:
        """
        Make the Sphero roll in a specific direction.
        
        Args:
            heading: Direction in degrees (0-359)
            speed: Speed (0-255)
            duration: Duration in seconds
            
        Returns:
            Tuple of (success, message)
        """
        if not self._is_connected or not self._sphero_api:
            logger.warning("Roll attempted when not connected")
            return False, "Not connected to any Sphero"
        
        try:
            # Ensure values are in valid ranges
            heading = max(0, min(359, heading))
            speed = max(0, min(self._max_speed, speed))
            
            self._sphero_api.roll(heading, speed, duration)
            logger.info(f"Rolling with heading {heading}, speed {speed}")
            return True, f'Rolling with heading {heading}, speed {speed}'
        except Exception as e:
            logger.error(f"Error rolling: {str(e)}")
            return False, f'Error rolling: {str(e)}'
    
    def spin(self, degrees: int, duration: float) -> Tuple[bool, str]:
        """
        Make the Sphero spin in place.
        
        Args:
            degrees: Degrees to spin
            duration: Duration in seconds
            
        Returns:
            Tuple of (success, message)
        """
        if not self._is_connected or not self._sphero_api:
            logger.warning("Spin attempted when not connected")
            return False, "Not connected to any Sphero"
        
        try:
            self._sphero_api.spin(degrees, duration)
            logger.info(f"Spinning {degrees} degrees over {duration} seconds")
            return True, f'Spinning {degrees} degrees'
        except Exception as e:
            logger.error(f"Error spinning: {str(e)}")
            return False, f'Error spinning: {str(e)}'

    def set_heading(self, heading: int) -> Tuple[bool, str]:
        """
        Set the Sphero's heading without moving it.
        
        Args:
            heading: Direction in degrees (0-359)
            
        Returns:
            Tuple of (success, message)
        """
        if not self._is_connected or not self._sphero_api:
            logger.warning("Set heading attempted when not connected")
            return False, "Not connected to any Sphero"
        
        try:
            heading = max(0, min(359, heading))
            # Use roll with zero speed to set heading
            self._sphero_api.roll(heading, 0, 0.1)
            logger.info(f"Set heading to {heading}°")
            return True, f'Set heading to {heading}°'
        except Exception as e:
            logger.error(f"Error setting heading: {str(e)}")
            return False, f'Error setting heading: {str(e)}'

# Create a singleton instance
sphero = SpheroConnection() 