#!/bin/bash
# Script to run the FastAPI backend

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

