#!/bin/bash

# The Lineup - Quick Start Script
# This script activates the virtual environment and starts both servers

echo "🏀 Starting The Lineup - Fantasy Basketball Draft Assistant"
echo "============================================================"

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the project root directory"
    echo "   (the directory containing the 'app' folder)"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Error: Virtual environment 'venv' not found"
    echo "   Please create it first with: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if activation was successful
if [ "$VIRTUAL_ENV" = "" ]; then
    echo "❌ Error: Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"

# Install/update dependencies
echo "📦 Checking dependencies..."
pip install -r requirements.txt --quiet

# Run the full application
echo "🚀 Starting The Lineup..."
python run_full_app.py 