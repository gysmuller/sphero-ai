"""
Random Movement Module

This module handles the random movement functionality for the Sphero robot.
"""

import random
import threading
import asyncio
import logging
from typing import Optional, Tuple, Any, Dict, Callable, Union

# Configure logging
logger = logging.getLogger("random_movement")

class RandomMovement:
    """Class for managing random movement of the Sphero robot."""
    
    def __init__(self, sphero_connection: Any = None) -> None:
        """
        Initialize the RandomMovement class.
        
        Args:
            sphero_connection: The SpheroConnection instance to use
        """
        # Will be set later if not provided
        self._sphero_connection = sphero_connection
        self._stop_random_movement: bool = False
        self._random_movement_task: Optional[asyncio.Task] = None
        self._random_movement_thread: Optional[threading.Thread] = None
        self._is_active: bool = False
    
    @property
    def is_active(self) -> bool:
        """Check if random movement is currently active."""
        return self._is_active
    
    def set_sphero_connection(self, sphero_connection: Any) -> None:
        """
        Set the Sphero connection to use.
        
        Args:
            sphero_connection: The SpheroConnection instance to use
        """
        self._sphero_connection = sphero_connection
    
    def _random_movement_function(self, socketio: Any) -> None:
        """
        Generate random slow movements and very dim light changes.
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
        """
        try:
            logger.info("Random movement task started.")
            socketio.emit('status', {'message': 'Random movement started'})
            socketio.sleep(0)
            
            while not self._stop_random_movement:
                # Check connection status inside the loop
                if not self._sphero_connection.is_connected or not self._sphero_connection.sphero_api:
                    logger.warning("Random movement: No longer connected, exiting loop.")
                    break
                    
                try:
                    # Generate a random very dim color (max brightness 40)
                    r = random.randint(0, 40)
                    g = random.randint(0, 40)
                    b = random.randint(0, 40)
                    self._sphero_connection.set_main_led(r, g, b)
                    
                    # Generate random direction and very slow speed (max 40)
                    heading = random.randint(0, 359)
                    speed = random.randint(10, 40)
                    
                    # Roll for a short duration to limit distance
                    duration = random.uniform(0.5, 1.5)
                    self._sphero_connection.roll(heading, speed, duration)
                    
                    # Longer pause between movements
                    pause_duration = duration + random.uniform(1.0, 2.0)
                    logger.info(f"Random movement: Rolling H:{heading} S:{speed} D:{duration:.1f}s, Pausing:{pause_duration:.1f}s")
                    # Use socketio.sleep for cooperative yielding in threaded mode
                    socketio.sleep(pause_duration) 
                    
                    # Occasionally make the Sphero spin very slowly
                    if random.random() < 0.2:  # 20% chance to spin
                        if (self._sphero_connection.is_connected and 
                            self._sphero_connection.sphero_api and 
                            not self._stop_random_movement):
                            # Slow gentle spin, smaller angles
                            degrees = random.choice([45, 90, 180])
                            spin_duration = random.uniform(2.0, 3.5)
                            logger.info(f"Random movement: Spinning {degrees}deg over {spin_duration:.1f}s")
                            self._sphero_connection.spin(degrees, spin_duration)
                            # Use socketio.sleep after spin
                            socketio.sleep(spin_duration + 1.0) 
                    
                except Exception as e:
                    logger.error(f"Error in random movement loop: {e}")
                    socketio.sleep(1) # Wait a bit before trying again
                
                # Explicit yield in case loop runs long
                socketio.sleep(0)

            # Stop moving if the loop finishes or is stopped
            if self._sphero_connection.is_connected and self._sphero_connection.sphero_api:
                try:
                    logger.info("Random movement: Stopping Sphero roll.")
                    self._sphero_connection.roll(0, 0, 0) # Stop moving
                except Exception as e:
                    logger.error(f"Random movement: Error stopping roll: {e}")
                    
            logger.info("Random movement task finished.")
            socketio.emit('status', {'message': 'Random movement stopped'})
            socketio.sleep(0)
            socketio.emit('random_movement_status', {'active': False})
            socketio.sleep(0)
            self._is_active = False
        
        except Exception as e:
            logger.error(f"Fatal error in random movement task: {e}")
            socketio.emit('status', {'message': f'Random movement error: {str(e)}'})
            socketio.sleep(0)
            socketio.emit('random_movement_status', {'active': False})
            socketio.sleep(0)
            self._is_active = False
    
    async def _async_random_movement(self, socketio: Any) -> None:
        """
        Async version of random movement function.
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
        """
        try:
            logger.info("Async random movement task started.")
            socketio.emit('status', {'message': 'Random movement started'})
            
            while not self._stop_random_movement:
                # Check connection status inside the loop
                if not self._sphero_connection.is_connected or not self._sphero_connection.sphero_api:
                    logger.warning("Random movement: No longer connected, exiting loop.")
                    break
                    
                try:
                    # Generate a random very dim color (max brightness 40)
                    r = random.randint(0, 40)
                    g = random.randint(0, 40)
                    b = random.randint(0, 40)
                    self._sphero_connection.set_main_led(r, g, b)
                    
                    # Generate random direction and very slow speed (max 40)
                    heading = random.randint(0, 359)
                    speed = random.randint(10, 40)
                    
                    # Roll for a short duration to limit distance
                    duration = random.uniform(0.5, 1.5)
                    self._sphero_connection.roll(heading, speed, duration)
                    
                    # Longer pause between movements
                    pause_duration = duration + random.uniform(1.0, 2.0)
                    logger.info(f"Random movement: Rolling H:{heading} S:{speed} D:{duration:.1f}s, Pausing:{pause_duration:.1f}s")
                    # Use asyncio.sleep for async cooperative yielding
                    await asyncio.sleep(pause_duration) 
                    
                    # Occasionally make the Sphero spin very slowly
                    if random.random() < 0.2:  # 20% chance to spin
                        if (self._sphero_connection.is_connected and 
                            self._sphero_connection.sphero_api and 
                            not self._stop_random_movement):
                            # Slow gentle spin, smaller angles
                            degrees = random.choice([45, 90, 180])
                            spin_duration = random.uniform(2.0, 3.5)
                            logger.info(f"Random movement: Spinning {degrees}deg over {spin_duration:.1f}s")
                            self._sphero_connection.spin(degrees, spin_duration)
                            # Use asyncio.sleep after spin
                            await asyncio.sleep(spin_duration + 1.0) 
                    
                except Exception as e:
                    logger.error(f"Error in async random movement loop: {e}")
                    await asyncio.sleep(1) # Wait a bit before trying again
                
                # Explicit yield in case loop runs long
                await asyncio.sleep(0)

            # Stop moving if the loop finishes or is stopped
            if self._sphero_connection.is_connected and self._sphero_connection.sphero_api:
                try:
                    logger.info("Random movement: Stopping Sphero roll.")
                    self._sphero_connection.roll(0, 0, 0) # Stop moving
                except Exception as e:
                    logger.error(f"Random movement: Error stopping roll: {e}")
                    
            logger.info("Async random movement task finished.")
            socketio.emit('status', {'message': 'Random movement stopped'})
            socketio.emit('random_movement_status', {'active': False})
            self._is_active = False
        
        except Exception as e:
            logger.error(f"Fatal error in async random movement task: {e}")
            socketio.emit('status', {'message': f'Random movement error: {str(e)}'})
            socketio.emit('random_movement_status', {'active': False})
            self._is_active = False
    
    def start_random_movement(self, socketio: Any) -> Tuple[bool, str]:
        """
        Start the random movement mode.
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
            
        Returns:
            Tuple of (success, message)
        """
        if not self._sphero_connection or not self._sphero_connection.is_connected:
            logger.warning("Cannot start random movement: Not connected to Sphero")
            return False, 'Cannot start random movement: Not connected to Sphero'
        
        logger.info("Start random movement request received.")
        # Signal any existing thread to stop
        self._stop_random_movement = True
        if self._random_movement_thread and self._random_movement_thread.is_alive():
            logger.info("Waiting for existing random movement thread to stop...")
        
        # Start new random movement task using socketio background task
        logger.info("Starting new random movement background task.")
        self._stop_random_movement = False
        self._is_active = True
        
        # Determine if we're using async mode or threaded mode based on socketio async_mode
        if hasattr(socketio, 'async_mode') and socketio.async_mode == 'asyncio':
            # Use asyncio for async mode
            try:
                loop = asyncio.get_event_loop()
                self._random_movement_task = loop.create_task(self._async_random_movement(socketio))
            except RuntimeError:
                # Fallback to using the thread-based approach if asyncio isn't available
                self._random_movement_thread = socketio.start_background_task(
                    self._random_movement_function, socketio
                )
        else:
            # Use threaded mode
            self._random_movement_thread = socketio.start_background_task(
                self._random_movement_function, socketio
            )
        
        socketio.emit('random_movement_status', {'active': True})
        socketio.sleep(0)
        
        return True, 'Random movement started'
    
    def stop_random_movement_command(self, socketio: Any) -> Tuple[bool, str]:
        """
        Stop the random movement mode.
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
            
        Returns:
            Tuple of (success, message)
        """
        logger.info("Stop random movement request received.")
        self._stop_random_movement = True
        
        # Wait a short moment for the background task to potentially stop itself via the flag
        socketio.sleep(0.1) 

        # Ensure the Sphero stops moving regardless of thread state
        if self._sphero_connection and self._sphero_connection.is_connected:
            try:
                logger.info("Ensuring Sphero roll is stopped.")
                self._sphero_connection.roll(0, 0, 0) # Stop moving
            except Exception as e:
                logger.error(f"Error stopping movement: {str(e)}")
                return False, f'Error stopping movement: {str(e)}'
        
        self._is_active = False
        return True, 'Stopping random movement...'

# Import the sphero connection singleton - this happens after the class definition
from . import sphero_connection

# Create a singleton instance
random_movement_manager = RandomMovement(sphero_connection.sphero) 