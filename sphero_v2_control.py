#!/usr/bin/env python3
"""
Sphero Control Script using spherov2 library

This script uses the official spherov2 library to control Sphero robots.
It should work with various Sphero models including SPRK+ and variants.
"""

import sys
import time
import asyncio
from typing import Optional, List

try:
    from spherov2 import scanner
    from spherov2.sphero_edu import SpheroEduAPI
    from spherov2.types import Color
except ImportError:
    print("Error: spherov2 module not found!")
    print("Please install it with: pip install spherov2")
    sys.exit(1)

def list_available_toys():
    """Scan and list all available Sphero toys."""
    print("Scanning for Sphero toys (10 seconds)...")
    available_toys = scanner.find_toys(toy_names=None)
    
    if not available_toys:
        print("No Sphero toys found! Make sure your device is:")
        print("1. Charged and powered on")
        print("2. Not connected to another device")
        return []
    
    print(f"\nFound {len(available_toys)} Sphero toys:")
    for i, toy in enumerate(available_toys):
        print(f"{i+1}. {toy}")
    
    return available_toys

def demo_sequences(api):
    """Run a demonstration sequence of commands."""
    print("\nRunning demo sequence...")

    # Light demo
    print("Changing colors...")
    api.set_main_led(Color(r=255, g=0, b=0))  # Red
    time.sleep(1)
    api.set_main_led(Color(r=0, g=255, b=0))  # Green
    time.sleep(1)
    api.set_main_led(Color(r=0, g=0, b=255))  # Blue
    time.sleep(1)
    
    # Movement demo
    try:
        print("Testing movement...")
        # Spin 360 degrees over 2 seconds
        api.spin(360, 2)
        time.sleep(0.5)
        
        # Roll forward at speed 100 for 2 seconds
        print("Rolling forward...")
        api.roll(0, 100, 2)
        time.sleep(0.5)
        
        # Roll right at speed 100 for 1 second
        print("Rolling right...")
        api.roll(90, 100, 1)
        time.sleep(0.5)
        
        # Roll backward at speed 100 for 1 second
        print("Rolling backward...")
        api.roll(180, 100, 1)
        time.sleep(0.5)
        
        # Roll left at speed 100 for 1 second
        print("Rolling left...")
        api.roll(270, 100, 1)
        
    except Exception as e:
        print(f"Movement error: {e}")
        print("Movement may not be supported on this model.")
    
    # Final color
    api.set_main_led(Color(r=128, g=0, b=128))  # Purple
    print("Demo completed!")

def interactive_mode(toy):
    """Run an interactive mode for controlling the Sphero toy."""
    print(f"\nConnecting to {toy}...")
    
    try:
        # Create a context manager for the SpheroEduAPI
        with SpheroEduAPI(toy) as api:
            print(f"Connected to {toy}!")
            print("\nInteractive Mode:")
            print("Available commands:")
            print("- color <r> <g> <b>  : Set main LED color (values 0-255)")
            print("- roll <heading> <speed> <duration>  : Roll in a direction (heading 0-359, speed 0-255, duration in seconds)")
            print("- spin <degrees> <duration>  : Spin in place (degrees 0-360, duration in seconds)")
            print("- demo  : Run a demonstration sequence")
            print("- exit  : Exit the program")
            
            while True:
                user_input = input("\nCommand> ").strip()
                
                if not user_input:
                    continue
                
                cmd_parts = user_input.split()
                cmd = cmd_parts[0].lower()
                
                if cmd == "exit":
                    break
                elif cmd == "color" and len(cmd_parts) >= 4:
                    try:
                        r = int(cmd_parts[1])
                        g = int(cmd_parts[2])
                        b = int(cmd_parts[3])
                        
                        # Ensure values are in range 0-255
                        r = max(0, min(255, r))
                        g = max(0, min(255, g))
                        b = max(0, min(255, b))
                        
                        print(f"Setting color to RGB({r},{g},{b})...")
                        api.set_main_led(Color(r=r, g=g, b=b))
                    except ValueError:
                        print("Error: Color values must be numbers between 0-255")
                
                elif cmd == "roll" and len(cmd_parts) >= 4:
                    try:
                        heading = int(cmd_parts[1])
                        speed = int(cmd_parts[2])
                        duration = float(cmd_parts[3])
                        
                        # Ensure values are in valid ranges
                        heading = max(0, min(359, heading))
                        speed = max(0, min(255, speed))
                        
                        print(f"Rolling with heading {heading}, speed {speed} for {duration} seconds...")
                        api.roll(heading, speed, duration)
                    except ValueError:
                        print("Error: Invalid values. Format: roll <heading 0-359> <speed 0-255> <duration>")
                    except Exception as e:
                        print(f"Movement error: {e}")
                
                elif cmd == "spin" and len(cmd_parts) >= 3:
                    try:
                        degrees = int(cmd_parts[1])
                        duration = float(cmd_parts[2])
                        
                        print(f"Spinning {degrees} degrees over {duration} seconds...")
                        api.spin(degrees, duration)
                    except ValueError:
                        print("Error: Invalid values. Format: spin <degrees> <duration>")
                    except Exception as e:
                        print(f"Spin error: {e}")
                
                elif cmd == "demo":
                    demo_sequences(api)
                
                else:
                    print("Unknown command or invalid parameters.")
                    print("Available commands: color, roll, spin, demo, exit")
            
    except Exception as e:
        print(f"Error: {e}")
        print("An error occurred while interacting with the Sphero device.")

def main():
    """Main function."""
    print("Sphero Control using spherov2 library")
    print("====================================")
    
    try:
        print("Scanning for Sphero toys...")
        toys = scanner.find_toys(toy_names=None, timeout=10)
        
        if not toys:
            print("No Sphero toys found! Make sure your device is:")
            print("1. Charged and powered on")
            print("2. Not connected to another device")
            return 1
        
        # Automatically select the first toy found
        selected_toy = toys[0]
        print(f"Found {len(toys)} toy(s). Automatically connecting to: {selected_toy}")
        
        # Start interactive mode with the selected toy
        interactive_mode(selected_toy)
        
    except KeyboardInterrupt:
        print("\nOperation interrupted. Exiting...")
    except Exception as e:
        print(f"An error occurred: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main()) 