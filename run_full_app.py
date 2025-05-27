#!/usr/bin/env python3
"""
The Lineup - Full Application Runner
Starts both FastAPI backend and Streamlit frontend together
"""

import subprocess
import sys
import os
import time
import signal
import threading
import requests
from pathlib import Path

class AppRunner:
    def __init__(self):
        self.backend_process = None
        self.frontend_process = None
        self.running = True
        
    def check_backend_health(self, max_retries=30, delay=1):
        """Check if backend is healthy and responding."""
        for i in range(max_retries):
            try:
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    return True
            except requests.exceptions.RequestException:
                pass
            
            if i < max_retries - 1:  # Don't sleep on last iteration
                time.sleep(delay)
                
        return False
    
    def start_backend(self):
        """Start the FastAPI backend server."""
        print("🚀 Starting FastAPI backend server...")
        
        try:
            self.backend_process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", 
                "app.main:app", 
                "--reload", 
                "--host", "0.0.0.0", 
                "--port", "8000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            # Wait for backend to be ready
            print("⏳ Waiting for backend to start...")
            if self.check_backend_health():
                print("✅ Backend server is ready!")
                return True
            else:
                print("❌ Backend failed to start properly")
                return False
                
        except Exception as e:
            print(f"❌ Error starting backend: {e}")
            return False
    
    def start_frontend(self):
        """Start the Streamlit frontend."""
        print("🎨 Starting Streamlit frontend...")
        
        script_path = "app/frontend/streamlit/pages/draft_assistant_v2.py"
        
        if not os.path.exists(script_path):
            print(f"❌ Error: {script_path} not found")
            return False
        
        try:
            self.frontend_process = subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", 
                script_path,
                "--server.port", "8502",
                "--server.headless", "true",
                "--browser.gatherUsageStats", "false"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            
            print("✅ Streamlit frontend started!")
            print("🌐 Frontend URL: http://localhost:8502")
            print("🔧 Backend API: http://localhost:8000")
            return True
            
        except Exception as e:
            print(f"❌ Error starting frontend: {e}")
            return False
    
    def monitor_processes(self):
        """Monitor both processes and restart if needed."""
        while self.running:
            try:
                # Check backend
                if self.backend_process and self.backend_process.poll() is not None:
                    print("⚠️ Backend process died, restarting...")
                    self.start_backend()
                
                # Check frontend
                if self.frontend_process and self.frontend_process.poll() is not None:
                    print("⚠️ Frontend process died, restarting...")
                    self.start_frontend()
                
                time.sleep(5)  # Check every 5 seconds
                
            except KeyboardInterrupt:
                break
    
    def cleanup(self):
        """Clean up processes."""
        print("\n🛑 Shutting down The Lineup...")
        self.running = False
        
        if self.frontend_process:
            print("🔄 Stopping Streamlit frontend...")
            self.frontend_process.terminate()
            try:
                self.frontend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.frontend_process.kill()
        
        if self.backend_process:
            print("🔄 Stopping FastAPI backend...")
            self.backend_process.terminate()
            try:
                self.backend_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.backend_process.kill()
        
        print("✅ Cleanup complete!")
    
    def run(self):
        """Run the full application."""
        print("🏀 Starting The Lineup - Fantasy Basketball Draft Assistant")
        print("=" * 60)
        
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            self.cleanup()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            # Start backend first
            if not self.start_backend():
                print("❌ Failed to start backend. Exiting.")
                return False
            
            # Start frontend
            if not self.start_frontend():
                print("❌ Failed to start frontend. Exiting.")
                self.cleanup()
                return False
            
            print("\n" + "=" * 60)
            print("🎉 The Lineup is ready!")
            print("📱 Open your browser and go to: http://localhost:8502")
            print("🔧 API documentation available at: http://localhost:8000/docs")
            print("⌨️  Press Ctrl+C to stop both servers")
            print("=" * 60)
            
            # Start monitoring in a separate thread
            monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
            monitor_thread.start()
            
            # Keep main thread alive
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            self.cleanup()
        
        return True

def main():
    """Main entry point."""
    # Check if we're in the right directory
    if not os.path.exists("app/main.py"):
        print("❌ Error: Please run this script from the project root directory")
        print("   (the directory containing the 'app' folder)")
        sys.exit(1)
    
    # Check if virtual environment is activated
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment not detected")
        print("   Consider activating your virtual environment first:")
        print("   source venv/bin/activate  # On macOS/Linux")
        print("   venv\\Scripts\\activate     # On Windows")
        print()
    
    runner = AppRunner()
    success = runner.run()
    
    if success:
        print("👋 Thanks for using The Lineup!")
    else:
        print("❌ The Lineup failed to start properly")
        sys.exit(1)

if __name__ == "__main__":
    main() 