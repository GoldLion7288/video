# 🎬 Video Player Application

A custom video player with playlist support, built with PyQt5 and OpenCV.

## 🚀 Quick Start (Fresh Linux System)

### 1. Install System Dependencies
```bash
./setup_system.sh
```

### 2. Run the Application
```bash
./run.sh
```

That's it! The `run.sh` script will automatically:
- Create a virtual environment if needed
- Install Python dependencies
- Launch the video player

## 📁 Project Structure
```
player/
├── run.py                 # Main application
├── run.sh                 # Launch script
├── setup_system.sh        # System dependencies installer
├── requirements.txt       # Python dependencies
├── playlist.csv          # Media playlist configuration
├── INSTALLATION_GUIDE.md  # Detailed setup guide
├── icons/                # UI icons and background
└── file/                 # Sample media files
```

## 🎮 Features
- ✅ Play videos (MP4, AVI, MKV) and images (JPG, PNG)
- ✅ Playlist-based media management
- ✅ Fullscreen mode with animated controls
- ✅ Variable playback speed (0.25x to 4x)
- ✅ Draggable window interface
- ✅ Custom title bar and controls

## 🎯 Controls
- **▶️ Play/Pause**: Start/pause playback
- **⏮️⏭️ Previous/Next**: Navigate playlist
- **⏹️ Stop**: Return to background
- **🔄 Speed**: Adjust playback speed
- **F11**: Toggle fullscreen

## 📖 Full Documentation
See [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for detailed setup instructions.

## 🔧 Manual Setup
If you prefer manual installation:

```bash
# 1. Install system dependencies (requires sudo)
sudo apt install python3 python3-pip python3-venv python3-pyqt5 python3-opencv

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate

# 4. Install Python dependencies
pip install -r requirements.txt

# 5. Run application
python3 run.py
```

## 🎵 Media Configuration
Edit `playlist.csv` to customize your media:
```csv
1,file/video.mp4,60
2,file/image.jpg,5
3,repeat,0
```

Format: `index,file_path,duration_seconds`

# in cmd
./run.sh start playlist.csv
./run.sh play test/2.jpg 3

./run.sh stop
./run.sh exit