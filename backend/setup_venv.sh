#!/bin/bash
# Setup script for CTLChat backend virtual environment

set -e

echo "Setting up Python virtual environment for CTLChat backend..."

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements from requirements.txt..."
pip install -r requirements.txt

echo ""
echo "✓ Virtual environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source backend/venv/bin/activate"
echo ""
echo "To deactivate when done, run:"
echo "  deactivate"
