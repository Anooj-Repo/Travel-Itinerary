#!/bin/bash
echo "Starting Intelligent Task Routing Backend..."

# Activate virtual environment
source venv/bin/activate

# Start Flask application
echo "Starting Flask server on port 5004..."
python app.py

read -p "Press Enter to continue..."
