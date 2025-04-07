"""
Socket Event Handlers Module

This module contains the socket event handlers for controlling the Sphero robot.
"""

from . import sphero_connection as sphero
from . import random_movement

def register_handlers(socketio):
    """
    Register all socket event handlers with the SocketIO instance.
    
    Args:
        socketio: Flask-SocketIO instance
    """
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection."""
        print("Client connected")
        # Attempt auto-connect when a client connects if not already connected
        if not sphero.is_connected:
            print("Client connected, starting auto-connect task...")
            socketio.start_background_task(attempt_auto_connect, socketio)
        else:
            # Inform the new client about the current status
            print("Client connected, already connected to Sphero.")
            socketio.emit('connection_status', {'connected': True})
            socketio.emit('status', {'message': f'Already connected to {sphero.sphero_toy}'})

    @socketio.on('check_connection_status')
    def handle_check_connection():
        """Handle checking connection status."""
        print("Checking connection status...")
        socketio.emit('connection_status', {'connected': sphero.is_connected})
        if not sphero.is_connected:
            # If not connected, trigger an auto-connect attempt
            print("Not connected, starting auto-connect task...")
            socketio.start_background_task(attempt_auto_connect, socketio)
        else:
            print(f"Already connected to {sphero.sphero_toy}.")

    @socketio.on('disconnect_from_sphero')
    def handle_disconnect():
        """Disconnect from the currently connected Sphero toy."""
        print("Disconnect request received.")
        
        # Stop random movement if it's running
        random_movement.stop_random_movement = True
        if random_movement.random_movement_thread and random_movement.random_movement_thread.is_alive():
            print("Waiting for random movement thread to stop...")
            # Wait up to 2 seconds
            # Note: This might not be reliable with socketio async modes
        
        # Try to acquire the lock briefly to avoid disconnecting during connection
        if sphero.connection_lock.acquire(blocking=True, timeout=1): 
            try:
                success, message = sphero.disconnect_sphero()
                socketio.emit('connection_status', {'connected': sphero.is_connected})
                socketio.sleep(0)
                socketio.emit('status', {'message': message})
                socketio.sleep(0)
                print(f"Disconnect result: {message}")
            finally:
                sphero.connection_lock.release()
                print("Connection lock released after disconnect.")
        else:
            print("Could not acquire lock, connection/disconnection likely in progress.")
            socketio.emit('status', {'message': 'Cannot disconnect, operation in progress.'})

    @socketio.on('set_color')
    def handle_set_color(data):
        """
        Set the main LED color of the Sphero.
        
        Args:
            data: Dictionary containing 'r', 'g', 'b' values
        """
        try:
            r = int(data['r'])
            g = int(data['g'])
            b = int(data['b'])
            
            success, message = sphero.set_main_led(r, g, b)
            socketio.emit('status', {'message': message})
        except Exception as e:
            socketio.emit('status', {'message': f'Error setting color: {str(e)}'})

    @socketio.on('roll')
    def handle_roll(data):
        """
        Make the Sphero roll in a specific direction.
        
        Args:
            data: Dictionary containing 'heading', 'speed', and optionally 'duration'
        """
        try:
            heading = int(data['heading'])
            speed = int(data['speed'])
            duration = float(data.get('duration', 1.0))
            
            success, message = sphero.roll(heading, speed, duration)
            socketio.emit('status', {'message': message})
        except Exception as e:
            socketio.emit('status', {'message': f'Error rolling: {str(e)}'})

    @socketio.on('spin')
    def handle_spin(data):
        """
        Make the Sphero spin in place.
        
        Args:
            data: Dictionary containing 'degrees' and optionally 'duration'
        """
        try:
            degrees = int(data['degrees'])
            duration = float(data.get('duration', 1.0))
            
            success, message = sphero.spin(degrees, duration)
            socketio.emit('status', {'message': message})
        except Exception as e:
            socketio.emit('status', {'message': f'Error spinning: {str(e)}'})

    @socketio.on('start_random_movement')
    def handle_start_random_movement():
        """Start the random movement mode."""
        success, message = random_movement.start_random_movement(socketio)
        if not success:
            socketio.emit('status', {'message': message})

    @socketio.on('stop_random_movement')
    def handle_stop_random_movement():
        """Stop the random movement mode."""
        success, message = random_movement.stop_random_movement_command(socketio)
        socketio.emit('status', {'message': message})
        socketio.sleep(0)

    @socketio.on('disconnect')
    def handle_client_disconnect():
        """Handle client disconnect."""
        print("Client disconnected.")

def attempt_auto_connect(socketio):
    """
    Attempt to scan and connect to the first available Sphero toy.
    
    Args:
        socketio: Flask-SocketIO instance for emitting events
    """
    print("Attempting to acquire connection lock...")
    # Prevent multiple concurrent connection attempts
    if not sphero.connection_lock.acquire(blocking=False):
        print("Auto-connection attempt already in progress. Lock not acquired.")
        return
    print("Connection lock acquired.")
    
    try:
        if sphero.is_connected:
            print("Already connected.")
            return # Lock will be released in finally

        # Emit status update
        socketio.emit('status', {'message': 'Scanning for Sphero toys...'})
        print("Scanning for Sphero toys...")
        toys = sphero.scan_for_spheros(timeout=10)

        if not toys:
            print("No Sphero toys found.")
            socketio.emit('status', {'message': 'No Sphero toys found.'})
            socketio.emit('connection_status', {'connected': False})
            return # Lock will be released in finally

        toy = toys[0]
        print(f"Found {len(toys)} toy(s). Attempting to connect to: {toy}")
        socketio.emit('status', {'message': f'Found {toy}. Connecting...'})
        socketio.sleep(0) # Yield control before blocking call

        success, message = sphero.connect_to_sphero(toy)
        socketio.emit('connection_status', {'connected': sphero.is_connected})
        socketio.sleep(0)
        socketio.emit('status', {'message': message})
        socketio.sleep(0)
            
    finally:
        print("Releasing connection lock.")
        sphero.connection_lock.release() 