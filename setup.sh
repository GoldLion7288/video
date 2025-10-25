#!/bin/bash
# ===========================================
# 🎬 Raspberry Pi Video Player Setup Script
# ===========================================

set -euo pipefail

echo "🔧 Step 1: Create & activate virtual environment (with system packages)..."
python3 -m venv --system-site-packages venv
source venv/bin/activate

echo "📦 Step 2: Install Python packages from requirements.txt..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🔑 Step 3: Make run.sh executable..."
chmod +x run.sh

echo "🖥 Step 4: Install system packages (PyQt5, GStreamer, X11)..."
sudo apt update

# PyQt5
sudo apt install -y python3-pyqt5 pyqt5-dev-tools

# Python GObject bindings
sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0

# GStreamer core + plugins
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base \
                    gstreamer1.0-plugins-good gstreamer1.0-plugins-bad \
                    gstreamer1.0-plugins-ugly gstreamer1.0-libav

# GStreamer introspection bindings for Python
sudo apt install -y gir1.2-gstreamer-1.0

# X11 libraries needed for Qt GUI
sudo apt install -y libxcb-xinerama0 libx11-xcb1 libxkbcommon-x11-0 libxcb-icccm4 \
                    libxcb-image0 libxcb-keysyms1 libxcb-randr0 libxcb-render-util0 \
                    libxcb-shape0 libxcb-sync1 libxcb-xfixes0 libxrender1

# Qt5 core libraries
sudo apt install -y libqt5gui5 libqt5core5a libqt5widgets5 libqt5opengl5 \
                    libqt5x11extras5 libqt5dbus5 libqt5network5

echo "✅ Setup complete!"

echo ""
echo "🎬 How to run your video player:"
echo "Start from playlist (full screen): ./run.sh start playlist.csv"
echo "Play single file: ./run.sh play \"test/2.jpg\""
echo "Stop player: ./run.sh stop"
echo "Exit PyQt5 environment: ./run.sh exit"

echo ""
echo "💡 Tip: If running headless (no monitor), use:"
echo "export QT_QPA_PLATFORM=offscreen"
echo "before running ./run.sh"