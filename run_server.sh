#!/bin/bash
echo "Installing/updating dependencies..."
pip install -r requirements.txt
echo ""
echo "Starting server with Daphne (WebSocket support)..."
daphne -b 127.0.0.1 -p 8000 truth_dare.asgi:application
