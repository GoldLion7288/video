#!/bin/bash
# ===========================================
# 🎬 Video Player Launcher Script
# ===========================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

show_usage() {
    echo "🎬 Video Player Launcher"
    echo "========================="
    echo "Usage:"
    echo "  $0 start <file_path>     - Start PyQt5 viewer (background image or window)"
    echo "  $0 play <file_path>      - Play specific video file"
    echo "  $0 stop                  - Force stop current video playback"
    echo "  $0 exit                  - Exit the PyQt5 environment completely"
    echo ""
    echo "Examples:"
    echo "  $0 start /path/to/background.jpg"
    echo "  $0 play /path/to/video.mp4"
    echo "  $0 stop"
    echo "  $0 exit"
    echo ""
}

if [ $# -lt 1 ]; then
    show_usage
    exit 1
fi

COMMAND="$1"

# ------------------------------
# Virtual environment check
# ------------------------------
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run the installation commands first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

echo "🔧 Activating virtual environment..."
source venv/bin/activate

# ------------------------------
# Dependency check
# ------------------------------
echo "🔍 Checking dependencies..."
python3 -c "import PyQt5" 2>/dev/null || { echo "❌ Installing PyQt5..."; pip install PyQt5; }
python3 -c "import cv2" 2>/dev/null || { echo "❌ Installing OpenCV..."; pip install opencv-python; }
python3 -c "import numpy" 2>/dev/null || { echo "❌ Installing NumPy..."; pip install numpy; }

if [ ! -f "run.py" ]; then
    echo "❌ Main application file 'run.py' not found!"
    exit 1
fi

PID_FILE="$SCRIPT_DIR/player.pid"

# ------------------------------
# Command handler
# ------------------------------
case "$COMMAND" in
    "start")
        if [ $# -lt 2 ]; then
            echo "❌ Error: file path required for start command"
            show_usage
            exit 1
        fi
        FILE_PATH="$2"
        if [ ! -f "$FILE_PATH" ]; then
            echo "❌ Error: File '$FILE_PATH' not found!"
            exit 1
        fi
        echo "🚀 Starting PyQt5 viewer with file: $FILE_PATH"
        python3 run.py --start "$FILE_PATH" --single-instance &
        echo $! > "$PID_FILE"
        ;;
        
    "play")
        if [ $# -lt 2 ]; then
            echo "❌ Error: video file required for play command"
            show_usage
            exit 1
        fi
        FILE_PATH="$2"
        if [ ! -f "$FILE_PATH" ]; then
            echo "❌ Error: File '$FILE_PATH' not found!"
            exit 1
        fi
        echo "🎬 Playing video: $FILE_PATH"
        python3 run.py --play "$FILE_PATH" --single-instance &
        echo $! > "$PID_FILE"
        ;;
        
    "stop")
        if [ -f "$PID_FILE" ]; then
            PID=$(cat "$PID_FILE")
            if ps -p $PID > /dev/null 2>&1; then
                echo "🛑 Stopping video playback (PID: $PID)..."
                kill -9 $PID || true
                rm -f "$PID_FILE"
            else
                echo "⚠️ No active player process found."
            fi
        else
            echo "⚠️ No running video process found."
        fi
        ;;
        
    "exit")
        echo "👋 Exiting PyQt5 environment..."
        pkill -f "python3 run.py" || true
        rm -f "$PID_FILE"
        ;;
        
    *)
        echo "❌ Error: Unknown command '$COMMAND'"
        show_usage
        exit 1
        ;;
esac

deactivate || true
echo "✅ Done."
