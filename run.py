"""
MarineAI - Quick Launcher
Starts the FastAPI server and opens the MarineAI Command Dashboard in your browser.
"""

import os
import sys
import time
import webbrowser
import threading
import uvicorn

def open_browser():
    """Wait for server initialization then open browser."""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print(f"\n=======================================================")
    print(f"🌊 MarineAI Detection Suite is live at: {url}")
    print(f"=======================================================\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Note: Could not automatically open browser: {e}")

if __name__ == "__main__":
    # Start browser opener thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run uvicorn server with hot reload
    print("Initializing MarineAI Core Engine...")
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
