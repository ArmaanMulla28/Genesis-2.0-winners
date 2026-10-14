"""
run.py - Convenience entry point to start the Self-Healing Registry Mock API server.

Usage:
    python run.py
"""

import sys
import os

# Add self-healing-registry to sys.path so app can be imported
base_dir = os.path.dirname(os.path.abspath(__file__))
registry_dir = os.path.join(base_dir, "self-healing-registry")
if registry_dir not in sys.path:
    sys.path.insert(0, registry_dir)

import uvicorn

if __name__ == "__main__":
    print("\nStarting Self-Healing Registry Mock API Server...")
    print("Swagger UI docs: http://127.0.0.1:8000/docs")
    print("Health check:    http://127.0.0.1:8000/health")
    print("Schema endpoint: http://127.0.0.1:8000/schema\n")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, app_dir=registry_dir)
