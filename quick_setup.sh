#!/bin/bash

# Quick setup script that runs the exact command provided
# Usage: ./quick_setup.sh

set -e

echo "🔧 Running: source venv/bin/activate && pip install --upgrade pip setuptools wheel"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment first..."
    python3 -m venv venv
fi

# Run the requested commands
source venv/bin/activate
pip install --upgrade pip setuptools wheel

echo "✅ Quick setup complete!"
echo ""
echo "Virtual environment is now active. To install dependencies:"
echo "  pip install -r requirements.txt"
