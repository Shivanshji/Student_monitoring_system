#!/bin/bash
# Helper script to start the FastAPI backend bypassing the macOS Homebrew/Conda expat dynamic library path conflict.
export DYLD_LIBRARY_PATH="/opt/homebrew/opt/expat/lib"
source venv/bin/activate
exec uvicorn backend.app:app --host 0.0.0.0 --port 8000
