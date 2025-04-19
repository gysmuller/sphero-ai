"""
Socket Event Handlers Module

This module contains the socket event handlers for controlling the Sphero robot.
"""

import logging
from typing import Any, Dict, Optional, Callable
from . import sphero_connection
from . import random_movement
from . import openai_processor

# Configure logging
logger = logging.getLogger("socket_handlers")

class SocketHandlers:
    """Class for handling socket.io events for the Sphero controller."""
    
    def __init__(self, 
                 sphero_conn: sphero_connection.SpheroConnection = None,
                 rand_movement: random_movement.RandomMovement = None,
                 openai_proc: Any = None) -> None:
        """
        Initialize the socket handlers with dependencies.
        
        Args:
            sphero_conn: The SpheroConnection instance
            rand_movement: The RandomMovement instance
            openai_proc: The OpenAIProcessor instance
        """
        # Default to module singletons if not provided
        self.sphero = sphero_conn or sphero_connection.sphero
        self.random_movement = rand_movement or random_movement.random_movement_manager
        self.openai_processor = openai_proc or openai_processor
    
    def register_handlers(self, socketio: Any) -> None:
        """
        Register all socket event handlers with the SocketIO instance.
        
        Args:
            socketio: Flask-SocketIO instance
        """
        
        @socketio.on('connect')
        def handle_connect() -> None:
            """Handle client connection."""
            logger.info("Client connected")
            # Attempt auto-connect when a client connects if not already connected
            if not self.sphero.is_connected:
                logger.info("Client connected, starting auto-connect task...")
                socketio.start_background_task(self.attempt_auto_connect, socketio)
            else:
                # Inform the new client about the current status
                logger.info("Client connected, already connected to Sphero.")
                socketio.emit('connection_status', {'connected': True})
                socketio.emit('status', {'message': f'Already connected to {self.sphero.sphero_toy}'})

        @socketio.on('check_connection_status')
        def handle_check_connection() -> None:
            """Handle checking connection status."""
            logger.info("Checking connection status...")
            socketio.emit('connection_status', {'connected': self.sphero.is_connected})
            if not self.sphero.is_connected:
                # If not connected, trigger an auto-connect attempt
                logger.info("Not connected, starting auto-connect task...")
                socketio.start_background_task(self.attempt_auto_connect, socketio)
            else:
                logger.info(f"Already connected to {self.sphero.sphero_toy}.")

        @socketio.on('disconnect_from_sphero')
        def handle_disconnect() -> None:
            """Disconnect from the currently connected Sphero toy."""
            logger.info("Disconnect request received.")
            
            # Stop random movement if it's running
            self.random_movement._stop_random_movement = True
            if self.random_movement._random_movement_thread and self.random_movement._random_movement_thread.is_alive():
                logger.info("Waiting for random movement thread to stop...")
                # Wait up to 2 seconds
                # Note: This might not be reliable with socketio async modes
            
            # Try to acquire the lock briefly to avoid disconnecting during connection
            if self.sphero.connection_lock.acquire(blocking=True, timeout=1): 
                try:
                    success, message = self.sphero.disconnect_sphero()
                    socketio.emit('connection_status', {'connected': self.sphero.is_connected})
                    socketio.sleep(0)
                    socketio.emit('status', {'message': message})
                    socketio.sleep(0)
                    logger.info(f"Disconnect result: {message}")
                finally:
                    self.sphero.connection_lock.release()
                    logger.info("Connection lock released after disconnect.")
            else:
                logger.warning("Could not acquire lock, connection/disconnection likely in progress.")
                socketio.emit('status', {'message': 'Cannot disconnect, operation in progress.'})

        @socketio.on('set_color')
        def handle_set_color(data: Dict[str, Any]) -> None:
            """
            Set the main LED color of the Sphero.
            
            Args:
                data: Dictionary containing 'r', 'g', 'b' values
            """
            try:
                r = int(data['r'])
                g = int(data['g'])
                b = int(data['b'])
                
                success, message = self.sphero.set_main_led(r, g, b)
                socketio.emit('status', {'message': message})
            except Exception as e:
                logger.error(f"Error setting color: {e}")
                socketio.emit('status', {'message': f'Error setting color: {str(e)}'})

        @socketio.on('roll')
        def handle_roll(data: Dict[str, Any]) -> None:
            """
            Make the Sphero roll in a specific direction.
            
            Args:
                data: Dictionary containing 'heading', 'speed', and optionally 'duration'
            """
            try:
                heading = int(data['heading'])
                speed = int(data['speed'])
                duration = float(data.get('duration', 1.0))
                
                success, message = self.sphero.roll(heading, speed, duration)
                socketio.emit('status', {'message': message})
            except Exception as e:
                logger.error(f"Error rolling: {e}")
                socketio.emit('status', {'message': f'Error rolling: {str(e)}'})

        @socketio.on('spin')
        def handle_spin(data: Dict[str, Any]) -> None:
            """
            Make the Sphero spin in place.
            
            Args:
                data: Dictionary containing 'degrees' and optionally 'duration'
            """
            try:
                degrees = int(data['degrees'])
                duration = float(data.get('duration', 1.0))
                
                success, message = self.sphero.spin(degrees, duration)
                socketio.emit('status', {'message': message})
            except Exception as e:
                logger.error(f"Error spinning: {e}")
                socketio.emit('status', {'message': f'Error spinning: {str(e)}'})

        @socketio.on('set_heading')
        def handle_set_heading(data: Dict[str, Any]) -> None:
            """
            Set the Sphero's heading (orientation).
            
            Args:
                data: Dictionary containing 'heading' value in degrees (0-359)
            """
            try:
                heading = int(data['heading'])
                
                success, message = self.sphero.set_heading(heading)                
                socketio.emit('status', {'message': message})
            except Exception as e:
                logger.error(f"Error setting heading: {e}")
                socketio.emit('status', {'message': f'Error setting heading: {str(e)}'})

        @socketio.on('start_random_movement')
        def handle_start_random_movement() -> None:
            """Start the random movement mode."""
            success, message = self.random_movement.start_random_movement(socketio)
            if not success:
                socketio.emit('status', {'message': message})

        @socketio.on('stop_random_movement')
        def handle_stop_random_movement() -> None:
            """Stop the random movement mode."""
            success, message = self.random_movement.stop_random_movement_command(socketio)
            socketio.emit('status', {'message': message})
            socketio.sleep(0)

        @socketio.on('process_openai_response')
        def handle_openai_response(data: Dict[str, Any]) -> None:
            """
            Process the OpenAI response data from the client.
            
            Args:
                data: Dictionary containing the response data from OpenAI
            """
            logger.info("Received OpenAI response for processing")
            server_event = data.get('event')
            
            # Use the openai_processor module to process the response
            success, message = self.openai_processor.process_openai_response(server_event, socketio)
            
            # Send status message back to the client
            if message:
                socketio.emit('openai_status', {'message': message})

        @socketio.on('disconnect')
        def handle_client_disconnect() -> None:
            """Handle client disconnect."""
            logger.info("Client disconnected.")

    def attempt_auto_connect(self, socketio: Any) -> None:
        """
        Attempt to scan and connect to the first available Sphero toy.
        
        Args:
            socketio: Flask-SocketIO instance for emitting events
        """
        logger.info("Attempting to acquire connection lock...")
        # Prevent multiple concurrent connection attempts
        if not self.sphero.connection_lock.acquire(blocking=False):
            logger.warning("Auto-connection attempt already in progress. Lock not acquired.")
            return
        logger.info("Connection lock acquired.")
        
        try:
            if self.sphero.is_connected:
                logger.info("Already connected.")
                return # Lock will be released in finally

            # Emit status update
            socketio.emit('status', {'message': 'Scanning for Sphero toys...'})
            logger.info("Scanning for Sphero toys...")
            toys = self.sphero.scan_for_spheros(timeout=10)

            if not toys:
                logger.warning("No Sphero toys found.")
                socketio.emit('status', {'message': 'No Sphero toys found.'})
                socketio.emit('connection_status', {'connected': False})
                return # Lock will be released in finally

            toy = toys[0]
            logger.info(f"Found {len(toys)} toy(s). Attempting to connect to: {toy}")
            socketio.emit('status', {'message': f'Found {toy}. Connecting...'})
            socketio.sleep(0) # Yield control before blocking call

            success, message = self.sphero.connect_to_sphero(toy)
            socketio.emit('connection_status', {'connected': self.sphero.is_connected})
            socketio.sleep(0)
            socketio.emit('status', {'message': message})
            socketio.sleep(0)
                
        finally:
            logger.info("Releasing connection lock.")
            self.sphero.connection_lock.release()

# Create a singleton instance with default dependencies
socket_handlers = SocketHandlers() 