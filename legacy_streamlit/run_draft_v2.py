#!/usr/bin/env python3
"""
The Lineup - Draft Assistant V2 Runner
Run the modular version of the draft assistant
"""

import subprocess
import sys
import os

def main():
    """Run the modular draft assistant."""
    
    # Get the path to the modular draft assistant
    script_path = "app/frontend/streamlit/pages/draft_assistant_v2.py"
    
    # Check if file exists
    if not os.path.exists(script_path):
        print(f"Error: {script_path} not found")
        sys.exit(1)
    
    # Run streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            script_path, 
            "--server.port", "8502"  # Use different port to avoid conflicts
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        sys.exit(0)

if __name__ == "__main__":
    main() 