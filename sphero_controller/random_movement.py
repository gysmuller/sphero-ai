"""
Random Movement Module

This module handles the random movement functionality for the Sphero robot.
"""

import random
import threading
from . import sphero_connection as sphero

# Global variables for random movement control
stop_random_movement = False
random_movement_thread = None

def random_movement_function(socketio):
    """
    Generate random slow movements and very dim light changes.
    
    Args:
        socketio: Flask-SocketIO instance for emitting events
    """
    global stop_random_movement
    
    try:
        print("Random movement task started.")
        socketio.emit('status', {'message': 'Random movement started'})
        socketio.sleep(0)
        
        while not stop_random_movement:
            # Check connection status inside the loop
            if not sphero.is_connected or not sphero.sphero_api:
                print("Random movement: No longer connected, exiting loop.")
                break
                
            try:
                # Generate a random very dim color (max brightness 40)
                r = random.randint(0, 40)
                g = random.randint(0, 40)
                b = random.randint(0, 40)
                sphero.sphero_api.set_main_led(sphero.Color(r=r, g=g, b=b))
                
                # Generate random direction and very slow speed (max 40)
                heading = random.randint(0, 359)
                speed = random.randint(10, 40)
                
                # Roll for a short duration to limit distance
                duration = random.uniform(0.5, 1.5)
                sphero.sphero_api.roll(heading, speed, duration)
                
                # Longer pause between movements
                pause_duration = duration + random.uniform(1.0, 2.0)
                print(f"Random movement: Rolling H:{heading} S:{speed} D:{duration:.1f}s, Pausing:{pause_duration:.1f}s")
                # Use socketio.sleep for cooperative yielding in threaded mode
                socketio.sleep(pause_duration) 
                
                # Occasionally make the Sphero spin very slowly
                if random.random() < 0.2:  # 20% chance to spin
                    if sphero.is_connected and sphero.sphero_api and not stop_random_movement:
                        # Slow gentle spin, smaller angles
                        degrees = random.choice([45, 90, 180])
                        spin_duration = random.uniform(2.0, 3.5)
                        print(f"Random movement: Spinning {degrees}deg over {spin_duration:.1f}s")
                        sphero.sphero_api.spin(degrees, spin_duration)
                        # Use socketio.sleep after spin
                        socketio.sleep(spin_duration + 1.0) 
                
            except Exception as e:
                print(f"Error in random movement loop: {e}")
                socketio.sleep(1) # Wait a bit before trying again
            
            # Explicit yield in case loop runs long
            socketio.sleep(0)

        # Stop moving if the loop finishes or is stopped
        if sphero.is_connected and sphero.sphero_api:
            try:
                print("Random movement: Stopping Sphero roll.")
                sphero.sphero_api.roll(0, 0, 0) # Stop moving
            except Exception as e:
                print(f"Random movement: Error stopping roll: {e}")
                
        print("Random movement task finished.")
        socketio.emit('status', {'message': 'Random movement stopped'})
        socketio.sleep(0)
        socketio.emit('random_movement_status', {'active': False})
        socketio.sleep(0)
    
    except Exception as e:
        print(f"Fatal error in random movement task: {e}")
        socketio.emit('status', {'message': f'Random movement error: {str(e)}'})
        socketio.sleep(0)
        socketio.emit('random_movement_status', {'active': False})
        socketio.sleep(0)

def start_random_movement(socketio):
    """
    Start the random movement mode.
    
    Args:
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        Tuple of (success, message)
    """
    global random_movement_thread, stop_random_movement
    
    if not sphero.is_connected or not sphero.sphero_api:
        return False, 'Cannot start random movement: Not connected to Sphero'
    
    print("Start random movement request received.")
    # Signal any existing thread to stop
    stop_random_movement = True
    if random_movement_thread and random_movement_thread.is_alive():
        print("Waiting for existing random movement thread to stop...")
    
    # Start new random movement task using socketio background task
    print("Starting new random movement background task.")
    stop_random_movement = False
    random_movement_thread = socketio.start_background_task(
        random_movement_function, socketio
    )
    
    socketio.emit('random_movement_status', {'active': True})
    socketio.sleep(0)
    
    return True, 'Random movement started'

def stop_random_movement_command(socketio):
    """
    Stop the random movement mode.
    
    Args:
        socketio: Flask-SocketIO instance for emitting events
        
    Returns:
        Tuple of (success, message)
    """
    global stop_random_movement
    
    print("Stop random movement request received.")
    stop_random_movement = True
    
    # Wait a short moment for the background task to potentially stop itself via the flag
    socketio.sleep(0.1) 

    # Ensure the Sphero stops moving regardless of thread state
    if sphero.is_connected and sphero.sphero_api:
        try:
            print("Ensuring Sphero roll is stopped.")
            sphero.sphero_api.roll(0, 0, 0) # Stop moving
        except Exception as e:
            print(f"Error stopping movement: {str(e)}")
            return False, f'Error stopping movement: {str(e)}'
    
    return True, 'Stopping random movement...' 