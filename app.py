"""
MarineGuard AI (SIH 2026 PS-1655) - Root App Bridge
Directly exports and runs the unified MarineGuard AI FastAPI application.
"""

from backend.main import app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
