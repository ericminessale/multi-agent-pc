#!/bin/bash

echo "PC Builder Pro Demo Launcher"
echo "==========================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Please run: python setup.py"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the service
echo "Starting PC Builder Pro service..."
python pc_builder_service.py

# Note: deactivate is handled by the subshell exit