"""
Runner script for The Lineup project.
Ensures proper Python path setup for importing app modules.
"""

import os
import sys
import importlib.util
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

def run_script(script_path: str):
    """Run a Python script with proper path setup."""
    try:
        # Convert script path to module name
        module_name = script_path.replace('/', '.').replace('.py', '')
        if module_name.startswith('app.'):
            module_name = module_name  # Keep as is
        else:
            module_name = module_name.replace('app.', '', 1)  # Remove first app. if present
            
        # Import and run the module
        module = importlib.import_module(module_name)
        
        # If module has a main() function, call it
        if hasattr(module, 'main'):
            module.main()
            
    except Exception as e:
        print(f"Error running {script_path}: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <script_path>")
        print("Example: python run.py app/modeling/test_2023_draft.py")
        sys.exit(1)
        
    script_path = sys.argv[1]
    if not os.path.exists(script_path):
        print(f"Error: Script {script_path} not found")
        sys.exit(1)
        
    run_script(script_path) 