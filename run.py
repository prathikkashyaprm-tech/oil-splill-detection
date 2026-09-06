"""
MarineGuard AI - Quick Launcher
Starts the FastAPI server and opens the MarineGuard Command Dashboard in your browser.
"""

import os
import sys
import time
import webbrowser
import threading
import uvicorn

# Ensure utf-8 output encoding where possible
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

def open_browser():
    """Wait for server initialization then open browser."""
    time.sleep(1.5)
    url = "http://127.0.0.1:8000"
    print("\n" + "="*60)
    print(f"[+] MarineGuard AI Command Center is LIVE at: {url}")
    print(f"[+] API Documentation available at: {url}/docs")
    print("="*60 + "\n")
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Note: Could not automatically open browser: {e}")

if __name__ == "__main__":
    # Start browser opener thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run uvicorn server
    print("[*] Initializing MarineGuard AI Core Engine...")
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=False)
