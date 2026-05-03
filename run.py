import subprocess
import sys
import os
import threading

def run_backend():
    print("Starting FastAPI backend on http://127.0.0.1:8000 ...")
    subprocess.run([sys.executable, "-m", "uvicorn", "src.app:app", "--reload", "--port", "8000"])

def run_frontend():
    print("Starting Frontend server on http://127.0.0.1:3000 ...")
    os.chdir("frontend")
    subprocess.run([sys.executable, "-m", "http.server", "3000"])

if __name__ == "__main__":
    print("=== Starting Road Accident Prediction System ===")
    
    # Create threads for backend and frontend
    t1 = threading.Thread(target=run_backend, daemon=True)
    t2 = threading.Thread(target=run_frontend, daemon=True)
    
    t1.start()
    t2.start()
    
    try:
        # Keep the main thread alive to catch KeyboardInterrupt
        while True:
            t1.join(1)
            t2.join(1)
    except KeyboardInterrupt:
        print("\nShutting down both servers...")
        sys.exit(0)
