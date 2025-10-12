#!/bin/bash
# Video Player Launcher Script

# Set strict error handling
set -euo pipefail

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🎬 Video Player Launcher"
echo "========================="

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run the installation commands first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if required modules are installed
echo "🔍 Checking dependencies..."
python3 -c "import PyQt5" 2>/dev/null || {
    echo "❌ PyQt5 not found. Installing..."
    pip install PyQt5
}

python3 -c "import cv2" 2>/dev/null || {
    echo "❌ OpenCV not found. Installing..."
    pip install opencv-python
}

python3 -c "import numpy" 2>/dev/null || {
    echo "❌ NumPy not found. Installing..."
    pip install numpy
}

# Check if main application exists
if [ ! -f "run.py" ]; then
    echo "❌ Main application file 'run.py' not found!"
    exit 1
fi

# Run the application
echo "🚀 Starting Video Player..."
echo ""
python3 run.py

# Deactivate virtual environment
deactivate
echo ""
echo "✅ Video Player closed."
