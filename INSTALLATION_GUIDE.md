# 🎬 Video Player Setup Guide - Fresh Linux Installation

## 📋 Complete Installation Guide for Fresh Linux System

This guide will help you set up the video player application from scratch on a completely fresh Linux system.

---

## 🔧 Step 1: Install System Dependencies

### Update System Packages
```bash
sudo apt update && sudo apt upgrade -y
```

### Install Python and Essential Tools
```bash
# Install Python 3 and development tools
sudo apt install -y python3 python3-pip python3-venv python3-dev

# Install multimedia and graphics libraries
sudo apt install -y \
    libgl1-mesa-glx \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxkbcommon-x11-0 \
    libxss1 \
    libgconf-2-4 \
    libxtst6 \
    libxrandr2 \
    libasound2-dev \
    libpulse-dev \
    libjack-dev \
    portaudio19-dev

# Install Qt5 system packages
sudo apt install -y \
    python3-pyqt5 \
    python3-pyqt5.qtmultimedia \
    pyqt5-dev-tools \
    qttools5-dev-tools

# Install OpenCV system dependencies
sudo apt install -y \
    libopencv-dev \
    python3-opencv

# Install GStreamer for video support
sudo apt install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    python3-gi \
    python3-gi-cairo \
    gir1.2-gstreamer-1.0

# Install media codecs
sudo apt install -y \
    ubuntu-restricted-extras \
    ffmpeg
```

---

## 📁 Step 2: Set Up Project Directory

### Navigate to Project Directory
```bash
cd /home/username/Downloads/player
```

### Verify Project Files
Make sure you have these files:
```
player/
├── run.py              # Main application
├── playlist.csv        # Media playlist
├── requirements.txt    # Python dependencies
├── icons/              # UI icons and background
└── file/              # Sample media files
```

---

## 🐍 Step 3: Create Python Virtual Environment

### Create Virtual Environment
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate
```

### Install Python Dependencies
```bash
# Update pip first
pip install --upgrade pip

# Install core dependencies
pip install PyQt5 opencv-python numpy

# Install additional dependencies from requirements.txt
pip install -r requirements.txt
```

---

## 🎮 Step 4: Create Launch Scripts

### Create Easy Launch Script
```bash
cat > run.sh << 'EOF'
#!/bin/bash
# Video Player Launcher Script

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment
echo "🎬 Starting Video Player..."
source venv/bin/activate

# Run the application
python3 run.py

# Deactivate when done
deactivate
EOF

# Make script executable
chmod +x run.sh
```

### Create Desktop Entry (Optional)
```bash
cat > video-player.desktop << EOF
[Desktop Entry]
Name=Video Player
Comment=Custom Video Player Application
Exec=/home/username/Downloads/player/run.sh
Icon=/home/username/Downloads/player/icons/ico.ico
Terminal=false
Type=Application
Categories=AudioVideo;Player;
StartupNotify=true
EOF

# Make desktop entry executable
chmod +x video-player.desktop
```

---

## 🚀 Step 5: Run the Application

### Method 1: Using Launch Script (Recommended)
```bash
./run.sh
```

### Method 2: Manual Launch
```bash
# Activate virtual environment
source venv/bin/activate

# Run application
python3 run.py

# Deactivate when done
deactivate
```

### Method 3: Double-Click Desktop Entry
- Copy `video-player.desktop` to your Desktop
- Double-click to launch

---

## 🎯 Verification Steps

### Test Dependencies
```bash
# Activate virtual environment
source venv/bin/activate

# Test Python imports
python3 -c "import PyQt5; print('✅ PyQt5 OK')"
python3 -c "import cv2; print('✅ OpenCV OK')" 
python3 -c "import numpy; print('✅ NumPy OK')"

# Test application startup
python3 -c "from run import VideoPlayer; print('✅ Application imports OK')"
```

---

## 📋 Complete Dependency List

### System Packages
- `python3`, `python3-pip`, `python3-venv`, `python3-dev`
- `python3-pyqt5`, `python3-pyqt5.qtmultimedia`
- `python3-opencv`, `libopencv-dev`
- `gstreamer1.0-*` (plugins and tools)
- `python3-gi`, `gir1.2-gstreamer-1.0`
- `ffmpeg`, `ubuntu-restricted-extras`

### Python Packages
- `PyQt5>=5.15.0` - GUI framework
- `opencv-python>=4.0.0` - Video/image processing
- `numpy>=1.19.0` - Numerical computations
- `bcc`, `traitlets`, `traittypes` - Additional utilities

---

## 🎛️ Application Features

### Controls
- **▶️ Play/Pause**: Start or pause media playback
- **⏮️ Previous**: Go to previous item in playlist
- **⏭️ Next**: Go to next item in playlist
- **⏹️ Stop**: Stop playback and return to background
- **🔄 Speed**: Adjust playback speed (0.25x to 4x)

### Keyboard Shortcuts
- **F11**: Toggle fullscreen mode
- **Space**: Play/Pause
- **Left Arrow**: Previous item
- **Right Arrow**: Next item
- **Escape**: Exit fullscreen

### Window Controls
- **Drag title bar**: Move window
- **Minimize/Maximize**: Window size controls
- **Close**: Exit application

---

## 🔧 Troubleshooting

### Common Issues

#### "No module named 'PyQt5'"
```bash
# Install PyQt5 system package
sudo apt install python3-pyqt5

# Or install via pip in virtual environment
source venv/bin/activate
pip install PyQt5
```

#### "No module named 'cv2'"
```bash
# Install OpenCV system package
sudo apt install python3-opencv

# Or install via pip
pip install opencv-python
```

#### "GStreamer not available"
```bash
# Install GStreamer packages
sudo apt install gstreamer1.0-plugins-base gstreamer1.0-plugins-good python3-gi
```

#### Video playback issues
```bash
# Install additional codecs
sudo apt install ubuntu-restricted-extras ffmpeg
```

#### Permission denied on run.sh
```bash
chmod +x run.sh
```

---

## 📝 Configuration

### Playlist Setup
Edit `playlist.csv` to customize your media files:
```csv
1,file/1.mp4,60
2,file/2.jpg,5
3,file/3.jpg,5
4,file/4.jpg,5
5,repeat,0
```

Format: `index,file_path,duration_in_seconds`

### Media Files
- Place video files (`.mp4`, `.avi`, `.mkv`) in the `file/` directory
- Place image files (`.jpg`, `.png`, `.bmp`) in the `file/` directory
- Update `playlist.csv` to reference your files

---

## 🎉 Success!

If everything is installed correctly, you should see:
1. Video player window opens
2. Background image displays
3. Control buttons are visible
4. Media playback works
5. Fullscreen mode functions

Your video player is now ready to use! 🚀
