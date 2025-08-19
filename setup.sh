#!/bin/bash

# OpenNVR Development Environment Setup Script
# This script sets up the virtual environment and installs all dependencies

set -e

echo "🚀 Setting up OpenNVR development environment..."

# Check if Python 3.11+ is available
if ! python3 --version | grep -E "Python 3\.(1[1-9]|[2-9][0-9])" > /dev/null; then
    echo "❌ Python 3.11+ is required. Please install Python 3.11 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and essential packages
echo "⬆️  Upgrading pip, setuptools, and wheel..."
pip install --upgrade pip setuptools wheel

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p data logs recordings

# Set permissions for scripts
chmod +x scripts/*.sh 2>/dev/null || true

echo "✅ Development environment setup complete!"
echo ""
echo "To activate the environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To start the application:"
echo "  python -m src.main"
