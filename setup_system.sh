#!/bin/bash
# System Dependencies Setup Script for Video Player

echo "🔧 Video Player System Setup"
echo "============================"
echo ""
echo "This script will install all required system dependencies."
echo "You will need sudo privileges."
echo ""

# Ask for confirmation
read -p "Continue with installation? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 1
fi

echo "🔄 Updating system packages..."
sudo apt update

echo "🐍 Installing Python and development tools..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    python3-setuptools

echo "🎨 Installing Qt5 and GUI dependencies..."
sudo apt install -y \
    python3-pyqt5 \
    python3-pyqt5.qtmultimedia \
    pyqt5-dev-tools \
    qttools5-dev-tools \
    libgl1-mesa-glx \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxkbcommon-x11-0

echo "📹 Installing multimedia libraries..."
sudo apt install -y \
    python3-opencv \
    libopencv-dev \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gstreamer-1.0

echo "🎵 Installing audio/video codecs..."
sudo apt install -y \
    ffmpeg \
    libasound2-dev \
    libpulse-dev

echo "✅ System dependencies installed!"
echo ""
echo "Next steps:"
echo "1. Create virtual environment: python3 -m venv venv"
echo "2. Activate it: source venv/bin/activate"
echo "3. Install Python packages: pip install -r requirements.txt"
echo "4. Run the application: ./run.sh"
echo ""
echo "Or simply run: ./run.sh (it will handle steps 1-3 automatically)"
