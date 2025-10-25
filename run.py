#!/usr/bin/env python3
import sys
import os
import time
from PyQt5 import QtWidgets, QtGui, QtCore, QtMultimedia, QtMultimediaWidgets
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap, QImage, QIcon
os.environ["QT_QUICK_BACKEND"] = "software"
os.environ["QT_XCB_GL_INTEGRATION"] = "none"
# ... rest of your code

# Try to import OpenCV as fallback
try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("OpenCV not available, using GStreamer only")

# Try to import GStreamer for direct pipeline control
try:
    import gi
    gi.require_version('Gst', '1.0')
    from gi.repository import Gst, GLib
    GSTREAMER_AVAILABLE = True
    Gst.init(None)
    print("GStreamer 1.0 available for direct pipeline control")
except ImportError:
    GSTREAMER_AVAILABLE = False
    print("GStreamer Python bindings not available, using Qt Multimedia")

class GStreamerVideoPlayer(QtWidgets.QWidget):
    """Custom GStreamer video player widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.pipeline = None
        self.video_sink = None
        self.is_playing = False
        self.duration = 0
        
    def setup_pipeline(self, file_path):
        """Setup GStreamer pipeline for video playback"""
        if not GSTREAMER_AVAILABLE:
            return False
            
        try:
            # Try different pipeline approaches for better compatibility
            pipeline_attempts = [
                # Simple playbin with autovideosink
                f"playbin uri=file://{os.path.abspath(file_path)} video-sink=autovideosink",
                # Playbin with specific video sink
                f"playbin uri=file://{os.path.abspath(file_path)} video-sink=xvimagesink",
                # Basic pipeline with decodebin
                f"filesrc location={os.path.abspath(file_path)} ! decodebin ! videoconvert ! autovideosink",
                # Simple playbin
                f"playbin uri=file://{os.path.abspath(file_path)}"
            ]
            
            for i, pipeline_str in enumerate(pipeline_attempts):
                try:
                    print(f"Trying GStreamer pipeline {i+1}: {pipeline_str}")
                    self.pipeline = Gst.parse_launch(pipeline_str)
                    
                    # Connect to bus for messages
                    bus = self.pipeline.get_bus()
                    bus.add_signal_watch()
                    bus.connect("message", self.on_bus_message)
                    
                    print(f"GStreamer pipeline {i+1} created successfully")
                    return True
                    
                except Exception as e:
                    print(f"GStreamer pipeline {i+1} failed: {e}")
                    continue
            
            print("All GStreamer pipeline attempts failed")
            return False
            
        except Exception as e:
            print(f"GStreamer pipeline setup error: {e}")
            return False
    
    def on_bus_message(self, bus, message):
        """Handle GStreamer bus messages"""
        if message.type == Gst.MessageType.EOS:
            print("GStreamer: End of stream")
            self.stop()
        elif message.type == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            print(f"GStreamer error: {err}, {debug}")
            self.stop()
        elif message.type == Gst.MessageType.STATE_CHANGED:
            if message.src == self.pipeline:
                old_state, new_state, pending_state = message.parse_state_changed()
                print(f"GStreamer state changed: {old_state.value_nick} -> {new_state.value_nick}")
    
    def play(self):
        """Start video playback"""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.PLAYING)
            self.is_playing = True
    
    def stop(self):
        """Stop video playback"""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.NULL)
            self.is_playing = False
    
    def pause(self):
        """Pause video playback"""
        if self.pipeline:
            self.pipeline.set_state(Gst.State.PAUSED)
    
    def set_position(self, position):
        """Seek to position (in nanoseconds)"""
        if self.pipeline:
            self.pipeline.seek_simple(Gst.Format.TIME, Gst.SeekFlags.FLUSH, position)
    
    def get_position(self):
        """Get current position (in nanoseconds)"""
        if self.pipeline:
            success, position = self.pipeline.query_position(Gst.Format.TIME)
            if success:
                return position
        return 0
    
    def get_duration(self):
        """Get video duration (in nanoseconds)"""
        if self.pipeline:
            success, duration = self.pipeline.query_duration(Gst.Format.TIME)
            if success:
                return duration
        return 0

class VideoPlayer(QtWidgets.QWidget):
    def __init__(self, playlist_file, auto_fullscreen=False):
        super().__init__()
        def resource_path(relative_path):
            if hasattr(sys, '_MEIPASS'):
                return os.path.join(sys._MEIPASS, relative_path)
            return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
        icon_path = resource_path(os.path.join("icons", "ico.ico"))
        self.setWindowIcon(QtGui.QIcon(icon_path))
        # Get screen information for optimal sizing
        self.screen = QtWidgets.QApplication.primaryScreen()
        self.screen_geometry = self.screen.geometry()
        self.screen_width = self.screen_geometry.width()
        self.screen_height = self.screen_geometry.height()
        
        # Set window size to full screen
        self.FIXED_WIDTH = self.screen_width
        self.FIXED_HEIGHT = self.screen_height

        # Position window to cover full screen
        x = 0
        y = 0
        
        self.resize(self.FIXED_WIDTH, self.FIXED_HEIGHT)
        self.setGeometry(x, y, self.FIXED_WIDTH, self.FIXED_HEIGHT)
        
        print(f"Screen resolution: {self.screen_width}x{self.screen_height}")
        print(f"Window size: {self.FIXED_WIDTH}x{self.FIXED_HEIGHT}")
        
        # Remove default title bar and window frame
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.WindowStaysOnTopHint)
        
        # Enable high-DPI support for better resolution
        self.setAttribute(QtCore.Qt.WA_AcceptTouchEvents, True)
        self.setAttribute(QtCore.Qt.WA_StaticContents, True)
        
        # Enable window dragging and mouse tracking
        self.setMouseTracking(True)
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        
        # Enable transparency for the window
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground, True)
        
        # Fullscreen state
        self.is_fullscreen = False
        self.is_maximized = False
        self.old_geometry = None
        
        # Create main layout first with no margins or spacing
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)
        
        # Create title bar first (at the top)
        self.create_title_bar()
        
        # Create content widget for media display
        self.content_widget = QtWidgets.QWidget()
        self.content_widget.setStyleSheet("background-color: black;")
        self.content_widget.setMouseTracking(True)
        self.content_widget.installEventFilter(self)
        
        # Create main content layout for media display
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        self.content_widget.setLayout(self.content_layout)
        
        # Add content widget to main layout
        self.main_layout.addWidget(self.content_widget)
        
        # Create overlay controls that will float on top of the content
        bottom_controls_layout = QtWidgets.QHBoxLayout()
        bottom_controls_layout.setContentsMargins(20, 5, 20, 5)
        bottom_controls_layout.addStretch()
        bottom_controls_layout.addWidget(self.media_controls)
        bottom_controls_layout.addStretch()

        self.bottom_controls_widget = QtWidgets.QWidget()
        self.bottom_controls_widget.setStyleSheet("background-color: transparent;")
        self.bottom_controls_widget.setLayout(bottom_controls_layout)
        
        # Make controls widget taller for easier interaction when invisible
        self.bottom_controls_widget.setFixedHeight(80)  # Taller for easier clicking when invisible
        
        # Position the controls widget as an overlay on top of the content widgetsuccess copy
        self.bottom_controls_widget.setParent(self.content_widget)
        self.bottom_controls_widget.raise_()  # Bring to front
        
        # Show window normally first, not fullscreen
        self.show()
        self.setCursor(QtCore.Qt.ArrowCursor)  # Show cursor for navigation
        
        # Set title bar as overlay on content widget now that it exists
        self.title_bar_widget.setParent(self.content_widget)
        
        # Position the controls and title bar overlays after the window is shown and has proper dimensions
        QTimer.singleShot(100, self.position_overlay_controls)
        QTimer.singleShot(100, self.position_overlay_title_bar)

        # Initialize single file mode flag
        self.is_single_file_mode = False
        
        # Load playlist if provided, otherwise create empty playlist
        if playlist_file:
            self.playlist = self.load_playlist(playlist_file)
        else:
            self.playlist = []
        self.current_index = 0
        
        # Set up command monitoring for single-instance mode
        self.command_timer = QTimer()
        self.command_timer.timeout.connect(self.check_for_commands)
        self.command_timer.start(1000)  # Check every second

        # Create media player for videos
        self.media_player = QMediaPlayer()
        self.media_player.stateChanged.connect(self.on_state_changed)
        self.media_player.mediaStatusChanged.connect(self.on_media_status_changed)
        self.media_player.error.connect(self.on_media_error)
        self.media_player.setNotifyInterval(100)

        self.timer = QTimer()
        self.timer.timeout.connect(self.play_next)

        self.current_label = None
        self.shuffle = False
        self.repeat = False

        self.is_playing = False  # <-- Add this flag

        # Do NOT call self.play_next() here!
        # self.play_next()  # <-- REMOVE or COMMENT OUT this line

        self.clear_layout()  # <-- ADD THIS LINE HERE
        
        # Auto-fullscreen for playlist mode
        if auto_fullscreen:
            QTimer.singleShot(500, self.toggle_fullscreen)  # Delay to ensure window is ready
        self.center_on_screen()  # <-- ADD THIS LINE HERE

        # Timer for detecting long press
        self.press_timer = QTimer()
        self.press_timer.setInterval(300)  # 0.3 seconds
        self.press_timer.setSingleShot(True)
        self.press_timer.timeout.connect(self.handle_long_press)

        self.is_long_press = False  # Flag to track long press
        
        # Initialize dragging state
        self.dragging = False
        self.drag_position = None
        
        # Initialize media state tracking
        self.currently_playing_video = False
        self.currently_showing_image = False
        self.active_timers = []
        self.is_stopped_at_frame = False  # Track if stopped at current frame
        
        # Initialize fullscreen controls behavior
        self.controls_visible_in_fullscreen = False
        self.mouse_inactivity_timer = QTimer()
        self.mouse_inactivity_timer.setSingleShot(True)
        self.mouse_inactivity_timer.timeout.connect(self.hide_fullscreen_controls)
        self.controls_animation = None
        self.title_bar_animation = None
        # Cursor visibility timer for fullscreen
        self.cursor_inactivity_timer = QTimer()
        self.cursor_inactivity_timer.setSingleShot(True)
        self.cursor_inactivity_timer.timeout.connect(self.hide_mouse_cursor)
        
        # Install event filter for more reliable mouse event detection
        self.installEventFilter(self)
    
    def safe_timer_singleShot(self, delay, callback):
        """Safely create a single shot timer that won't conflict with video playback"""
        # Don't create new timers if we're currently playing video
        if self.currently_playing_video:
            print(f"Blocked timer creation during video playback: {callback.__name__}")
            return
        
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(callback)
        timer.start(delay)
        self.active_timers.append(timer)
        return timer
    
    def clear_all_timers(self):
        """Clear all active timers to prevent conflicts"""
        for timer in self.active_timers:
            if timer.isActive():
                timer.stop()
        self.active_timers.clear()
    
    def safe_stop_all_media(self):
        """Safely stop all media without crashing if resources are already released"""
        try:
            if hasattr(self, 'media_player') and self.media_player:
                self.media_player.stop()
                print("Stopped media player safely")
        except Exception as e:
            print(f"Error stopping media player: {e}")
        
        try:
            if hasattr(self, 'gst_player') and self.gst_player:
                self.gst_player.stop()
                print("Stopped GStreamer player safely")
        except Exception as e:
            print(f"Error stopping GStreamer player: {e}")
        
        try:
            if hasattr(self, 'video_timer') and self.video_timer:
                self.video_timer.stop()
                print("Stopped video timer safely")
        except Exception as e:
            print(f"Error stopping video timer: {e}")
        
        try:
            if hasattr(self, 'video_cap') and self.video_cap is not None:
                self.video_cap.release()
                self.video_cap = None  # Set to None after release
                print("Released video capture safely")
        except Exception as e:
            print(f"Error releasing video capture: {e}")
            self.video_cap = None  # Set to None even if release failed
    
    def show_fullscreen_controls(self):
        """Show controls in fullscreen mode with animation"""
        if not self.is_fullscreen:
            print("Not in fullscreen mode - skipping control show")
            return
            
        # Stop any existing hide timer
        self.mouse_inactivity_timer.stop()
        
        # If controls are already visible, just reset the timer
        if self.controls_visible_in_fullscreen:
            print("Controls already visible - resetting timer")
            self.mouse_inactivity_timer.start(3000)
            return
            
        # Show controls with animation
        self.controls_visible_in_fullscreen = True
        print(f"Showing fullscreen controls - screen size: {self.width()}x{self.height()}")
        
        # In fullscreen mode, set controls as child of main window for proper positioning
        if self.bottom_controls_widget.parent() != self:
            self.bottom_controls_widget.setParent(self)
            print("Changed controls parent to main window")
        
        # Get screen dimensions for fullscreen positioning
        screen_width = self.width()
        screen_height = self.height()
        controls_height = self.bottom_controls_widget.height()
        
        x = 0
        y = screen_height - controls_height
        width = screen_width
        
        print(f"Positioning controls at: x={x}, y={y}, width={width}, height={controls_height}")
        
        # Set semi-transparent background for visibility FIRST
        self.bottom_controls_widget.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.8);
                border: none;
                border-radius: 8px;
                padding: 5px;
            }
        """)
        
        # Show controls immediately first
        self.bottom_controls_widget.show()
        self.bottom_controls_widget.raise_()
        
        # Create animation for smooth slide-up effect
        self.controls_animation = QtCore.QPropertyAnimation(self.bottom_controls_widget, b"geometry")
        self.controls_animation.setDuration(300)  # 300ms animation
        self.controls_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        
        # Start from below the screen
        start_geometry = QtCore.QRect(x, screen_height, width, controls_height)
        end_geometry = QtCore.QRect(x, y, width, controls_height)
        
        self.controls_animation.setStartValue(start_geometry)
        self.controls_animation.setEndValue(end_geometry)
        
        # Start animation
        self.controls_animation.start()
        
        # Also show title bar from top with animation (overlay)
        try:
            if self.title_bar_widget.parent() != self:
                self.title_bar_widget.setParent(self)
            top_h = self.title_bar_widget.height()
            top_start = QtCore.QRect(0, -top_h, self.width(), top_h)
            top_end = QtCore.QRect(0, 0, self.width(), top_h)
            # Start off-screen, then animate into place
            self.title_bar_widget.setGeometry(top_start)
            self.title_bar_widget.show()
            self.title_bar_widget.raise_()
            self.title_bar_animation = QtCore.QPropertyAnimation(self.title_bar_widget, b"geometry")
            self.title_bar_animation.setDuration(300)
            self.title_bar_animation.setEasingCurve(QtCore.QEasingCurve.OutCubic)
            self.title_bar_animation.setStartValue(top_start)
            self.title_bar_animation.setEndValue(top_end)
            self.title_bar_animation.start()
        except Exception as e:
            print(f"Error animating title bar: {e}")

        # Start timer to hide after 3 seconds of inactivity
        self.mouse_inactivity_timer.start(3000)
        
    def hide_fullscreen_controls(self):
        """Hide controls in fullscreen mode with animation"""
        if not self.is_fullscreen or not self.controls_visible_in_fullscreen:
            return
            
        self.controls_visible_in_fullscreen = False
        
        # Create animation for smooth slide-down effect
        self.controls_animation = QtCore.QPropertyAnimation(self.bottom_controls_widget, b"geometry")
        self.controls_animation.setDuration(300)  # 300ms animation
        self.controls_animation.setEasingCurve(QtCore.QEasingCurve.InCubic)
        
        screen_height = self.height()
        controls_height = self.bottom_controls_widget.height()
        current_geometry = self.bottom_controls_widget.geometry()
        
        # Slide down below the screen
        end_geometry = QtCore.QRect(current_geometry.x(), screen_height, current_geometry.width(), controls_height)
        
        self.controls_animation.setStartValue(current_geometry)
        self.controls_animation.setEndValue(end_geometry)
        self.controls_animation.finished.connect(self.bottom_controls_widget.hide)
        self.controls_animation.start()

        # Hide title bar with slide-up animation
        try:
            top_h = self.title_bar_widget.height()
            current_top_geo = self.title_bar_widget.geometry()
            top_end = QtCore.QRect(0, -top_h, current_top_geo.width(), top_h)
            self.title_bar_animation = QtCore.QPropertyAnimation(self.title_bar_widget, b"geometry")
            self.title_bar_animation.setDuration(300)
            self.title_bar_animation.setEasingCurve(QtCore.QEasingCurve.InCubic)
            self.title_bar_animation.setStartValue(current_top_geo)
            self.title_bar_animation.setEndValue(top_end)
            self.title_bar_animation.finished.connect(self.title_bar_widget.hide)
            self.title_bar_animation.start()
        except Exception as e:
            print(f"Error hiding title bar: {e}")
    
    def test_show_controls(self):
        """Test function to verify controls can be shown"""
        if self.is_fullscreen:
            print("TEST: Forcing controls to show for testing")
            self.show_fullscreen_controls()
    
    def eventFilter(self, obj, event):
        """Event filter to catch all mouse events for fullscreen controls and title bar dragging"""
        # Handle title bar dragging
        if obj == self.title_bar_widget or obj == self.content_widget:
            if event.type() == QtCore.QEvent.MouseButtonPress:
                print("Event filter: Title bar mouse press detected")
                self.title_bar_mouse_press(event)
                if self.is_fullscreen:
                    self.reset_mouse_cursor_timer()
                return True
            elif event.type() == QtCore.QEvent.MouseMove:
                if self.dragging:
                    print("Event filter: Title bar mouse move detected")
                    self.title_bar_mouse_move(event)
                    if self.is_fullscreen:
                        self.reset_mouse_cursor_timer()
                    return True
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                print("Event filter: Title bar mouse release detected")
                self.title_bar_mouse_release(event)
                if self.is_fullscreen:
                    self.reset_mouse_cursor_timer()
                return True
        
        # Handle fullscreen controls
        if self.is_fullscreen:
            if event.type() == QtCore.QEvent.MouseMove:
                print("Event filter: Mouse move detected")
                self.show_fullscreen_controls()
                self.reset_mouse_cursor_timer()
            elif event.type() == QtCore.QEvent.MouseButtonPress:
                print("Event filter: Mouse press detected")
                self.show_fullscreen_controls()
                self.reset_mouse_cursor_timer()
            elif event.type() == QtCore.QEvent.MouseButtonRelease:
                print("Event filter: Mouse release detected")
                self.show_fullscreen_controls()
                self.reset_mouse_cursor_timer()
            elif event.type() == QtCore.QEvent.Enter:
                print("Event filter: Mouse enter detected")
                self.show_fullscreen_controls()
                self.reset_mouse_cursor_timer()
        return super().eventFilter(obj, event)

    def reset_mouse_cursor_timer(self):
        """Show mouse cursor and start 5s timer to hide it in fullscreen"""
        if not self.is_fullscreen:
            return
        try:
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.cursor_inactivity_timer.stop()
            self.cursor_inactivity_timer.start(5000)
        except Exception as e:
            print(f"Error resetting cursor timer: {e}")

    def hide_mouse_cursor(self):
        """Hide mouse cursor if still in fullscreen"""
        try:
            if self.is_fullscreen:
                self.setCursor(QtCore.Qt.BlankCursor)
        except Exception as e:
            print(f"Error hiding mouse cursor: {e}")
    
    def previous_item_with_timer_reset(self):
        """Previous item with fullscreen timer reset"""
        if self.is_fullscreen and self.controls_visible_in_fullscreen:
            self.mouse_inactivity_timer.start(3000)
        self.previous_item()
    
    def next_item_with_timer_reset(self):
        """Next item with fullscreen timer reset"""
        if self.is_fullscreen and self.controls_visible_in_fullscreen:
            self.mouse_inactivity_timer.start(3000)
        self.next_item()
    
    def toggle_play_pause_with_timer_reset(self):
        """Toggle play/pause with fullscreen timer reset"""
        if self.is_fullscreen and self.controls_visible_in_fullscreen:
            self.mouse_inactivity_timer.start(3000)
        self.toggle_play_pause()
    
    def stop_and_return_to_background_with_timer_reset(self):
        """Stop and return to background with fullscreen timer reset"""
        if self.is_fullscreen and self.controls_visible_in_fullscreen:
            self.mouse_inactivity_timer.start(3000)
        self.stop_and_return_to_background()
    
    def change_playback_speed_with_timer_reset(self, delta):
        """Change playback speed with fullscreen timer reset"""
        if self.is_fullscreen and self.controls_visible_in_fullscreen:
            self.mouse_inactivity_timer.start(3000)
        self.change_playback_speed(delta)
    
    def set_playback_speed_from_bar_with_timer_reset(self, value):
        """Set playback speed from bar with fullscreen timer reset"""
        if self.is_fullscreen and self.controls_visible_in_fullscreen:
            self.mouse_inactivity_timer.start(3000)
        self.set_playback_speed_from_bar(value)

    def center_on_screen(self):
        """Center the window on the screen"""
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            screen.center().x() - size.width() // 2,
            screen.center().y() - size.height() // 2
        )
        
    def show_warning_message(self, message):
        """Show a warning message dialog"""
        alert = AlertMessage(message)
        alert.setWindowFlags(QtCore.Qt.FramelessWindowHint | QtCore.Qt.Dialog)
        alert.setFixedSize(400, 170)
        alert.setStyleSheet("""
            QDialog {
            background: #4d4d4d;
            border: none;
            border-radius: 12px;
            }
            QLabel {
            color: #fff;
            font-size: 16px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            padding: 12px;
            }
            QPushButton {
            background: #222;
            color: #fff;
            border-radius: 6px;
            font-size: 15px;
            font-family: 'Segoe UI', 'Arial', sans-serif;
            padding: 8px 24px;
            margin-top: 16px;
            }
            QPushButton:hover {
            background: #111;
            }
        """)
        alert.setWindowOpacity(0.9)
        alert.exec_()

    def position_overlay_controls(self):
        """Position the overlay controls at the bottom edge"""
        if hasattr(self, 'bottom_controls_widget'):
            controls_height = self.bottom_controls_widget.height()
            
            if not self.is_fullscreen:
                # In windowed mode, ensure controls parent is content_widget and position at absolute bottom
                if self.bottom_controls_widget.parent() != self.content_widget:
                    self.bottom_controls_widget.setParent(self.content_widget)
                
                content_width = self.content_widget.width()
                content_height = self.content_widget.height()
                
                # Position at absolute bottom edge of content area
                x = 0
                y = content_height - controls_height
                width = content_width
                
                self.bottom_controls_widget.setGeometry(x, y, width, controls_height)
                self.bottom_controls_widget.show()
                self.bottom_controls_widget.raise_()
                
                # Make controls invisible with 0 opacity in windowed mode (like fullscreen when hidden)
                self.bottom_controls_widget.setStyleSheet("""
                    QWidget {
                        background-color: rgba(0, 0, 0, 0.0);
                        border: none;
                        padding: 0px;
                    }
                """)
            else:
                # In fullscreen mode, initially hide controls (shown via animation on mouse events)
                self.bottom_controls_widget.hide()
                self.controls_visible_in_fullscreen = False

    def position_overlay_title_bar(self):
        """Position the overlay title bar at the top edge"""
        if hasattr(self, 'title_bar_widget'):
            title_height = self.title_bar_widget.height()
            
            if not self.is_fullscreen:
                # In windowed mode, ensure title bar parent is content_widget and position at absolute top
                if self.title_bar_widget.parent() != self.content_widget:
                    self.title_bar_widget.setParent(self.content_widget)
                
                content_width = self.content_widget.width()
                
                # Position at absolute top edge of content area
                x = 0
                y = 0
                width = content_width
                
                self.title_bar_widget.setGeometry(x, y, width, title_height)
                self.title_bar_widget.show()
                self.title_bar_widget.raise_()
                
                # Make title bar semi-transparent overlay in windowed mode (same as fullscreen style)
                self.title_bar_widget.setStyleSheet("""
                    QWidget {
                        background-color: rgba(40, 40, 40, 0.8);
                        border: none;
                        padding: 0px;
                    }
                """)
            else:
                # In fullscreen mode, initially hide title bar (shown via animation on mouse events)
                self.title_bar_widget.hide()

    def create_title_bar(self):
        """Create a custom title bar with window controls and media controls"""
        title_bar = QtWidgets.QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        title_bar.setSpacing(0)
        
        # Title label
        title_label = QtWidgets.QLabel("連続再生ビューア")
        title_label.setStyleSheet("""
            background-color: transparent;
            color: white;
            font-size: 15px;
            padding: 10px;
        """)
        # Make title label not capture mouse events for dragging
        title_label.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
        
        # --- Only the following controls: Previous, Play/Pause, Next, Speed Down, Playback Speed, Speed Up, Stop Full, Full Display (F11) ---
        pre_ico = QtGui.QIcon("icons/pre.png")  # your gray icon
        next_ico = QtGui.QIcon("icons/next.png")  # your gray icon
        stop_full_ico = QtGui.QIcon("icons/stop_full.png")  # complete stop icon
        play_ico = QtGui.QIcon("icons/play.png")  # play icon
        pause_ico = QtGui.QIcon("icons/stop.png")  # pause icon (using stop.png as pause)
        speed_down_ico = QtGui.QIcon("icons/speed_previous.png")  # speed down icon
        speed_up_ico = QtGui.QIcon("icons/speed_next.png")  # speed up icon

        # --- Previous Button ---
        prev_btn = QtWidgets.QPushButton()
        prev_btn.setIcon(pre_ico)
        prev_btn.setIconSize(QtCore.QSize(20, 20))
        prev_btn.setFixedSize(40, 32)
        prev_btn.setToolTip("Previous")
        prev_btn.clicked.connect(self.previous_item_with_timer_reset)

        # --- Play/Pause toggle button ---
        self.play_pause_btn = QtWidgets.QPushButton()
        self.play_pause_btn.setIcon(play_ico)
        self.play_pause_btn.setIconSize(QtCore.QSize(20, 20))
        self.play_pause_btn.setFixedSize(40, 32)
        self.play_pause_btn.setToolTip("Play")
        self.play_pause_btn.clicked.connect(self.toggle_play_pause_with_timer_reset)

        # Store icons for toggling
        self.play_icon = play_ico
        self.pause_icon = pause_ico

        # --- Next Button ---
        next_btn = QtWidgets.QPushButton()
        next_btn.setIcon(next_ico)
        next_btn.setIconSize(QtCore.QSize(20, 20))
        next_btn.setFixedSize(40, 32)
        next_btn.setToolTip("Next")
        next_btn.clicked.connect(self.next_item_with_timer_reset)


        # --- Speed Down Button ---
        speed_down_btn = QtWidgets.QPushButton()
        speed_down_btn.setIcon(speed_down_ico)
        speed_down_btn.setIconSize(QtCore.QSize(20, 20))
        speed_down_btn.setToolTip("Speed Down")
        speed_down_btn.setFixedSize(32, 32)

        speed_bar = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        speed_bar.setMinimum(25)
        speed_bar.setMaximum(400)
        speed_bar.setValue(100)
        speed_bar.setFixedWidth(80)
        speed_bar.setToolTip("Playback Speed (0.25x ~ 4x)")
        self.speed_bar = speed_bar  # Save for later use

        # --- Speed Up Button ---
        speed_up_btn = QtWidgets.QPushButton()
        speed_up_btn.setIcon(speed_up_ico)
        speed_up_btn.setIconSize(QtCore.QSize(20, 20))
        speed_up_btn.setToolTip("Speed Up")
        speed_up_btn.setFixedSize(32, 32)

        # --- Stop Full Button ---
        stop_full_btn = QtWidgets.QPushButton()
        stop_full_btn.setIcon(stop_full_ico)
        stop_full_btn.setIconSize(QtCore.QSize(20, 20))
        stop_full_btn.setToolTip("Stop and Return to Background")
        stop_full_btn.setFixedSize(40, 32)


        # fullscreen_btn = QtWidgets.QPushButton("⛶")
        # fullscreen_btn.setToolTip("Full Display (F11)")
        # fullscreen_btn.setFixedSize(40, 32)

        # Window control buttons
        minimize_btn = QtWidgets.QPushButton("─")
        maximize_btn = QtWidgets.QPushButton("□")
        close_btn = QtWidgets.QPushButton("✕")
        for btn in [minimize_btn, maximize_btn, close_btn]:
            btn.setFixedSize(40, 40)
            btn.setMouseTracking(True)

        # Connect media buttons
        stop_full_btn.clicked.connect(self.stop_and_return_to_background_with_timer_reset)
        # fullscreen_btn.clicked.connect(self.toggle_fullscreen)
        speed_down_btn.clicked.connect(lambda: self.change_playback_speed_with_timer_reset(-0.25))
        speed_up_btn.clicked.connect(lambda: self.change_playback_speed_with_timer_reset(0.25))
        speed_bar.valueChanged.connect(self.set_playback_speed_from_bar_with_timer_reset)

        # Window button connections
        minimize_btn.clicked.connect(self.showMinimized)
        maximize_btn.clicked.connect(self.toggle_fullscreen)  # Make □ button same as F11
        close_btn.clicked.connect(self.close)

        # Window controls group
        window_controls = QtWidgets.QWidget()
        window_controls.setStyleSheet("background-color: transparent;")
        window_layout = QtWidgets.QHBoxLayout()
        window_layout.setContentsMargins(0, 0, 0, 0)
        window_layout.setSpacing(0)
        for btn in [minimize_btn, maximize_btn, close_btn]:
            window_layout.addWidget(btn)
        window_controls.setLayout(window_layout)

        title_bar.addWidget(title_label)
        title_bar.addStretch()

        # Store media controls for later use at bottom
        self.media_controls = QtWidgets.QWidget()
        self.media_controls.setStyleSheet("background-color: rgba(40, 40, 40, 0.8); border-radius: 8px; padding: 5px;")
        media_layout = QtWidgets.QHBoxLayout()
        media_layout.setContentsMargins(10, 5, 10, 5)
        media_layout.setSpacing(8)
        # Button order: Previous, Play/Pause, Next, Speed Down, Playback Speed, Speed Up, Stop Full, Full Display (F11)
        for btn in [prev_btn, self.play_pause_btn, next_btn, speed_down_btn, speed_bar, speed_up_btn, stop_full_btn]:
            media_layout.addWidget(btn)
        self.media_controls.setLayout(media_layout)
        self.media_controls.setFixedHeight(50)

        title_bar.addWidget(window_controls)

        # Create title bar widget with custom styling
        self.title_bar_widget = QtWidgets.QWidget()
        self.title_bar_widget.setAutoFillBackground(False)
        self.title_bar_widget.setAttribute(QtCore.Qt.WA_TranslucentBackground, False)
        self.title_bar_widget.setLayout(title_bar)
        self.title_bar_widget.setFixedHeight(40)
        # Remove background from stylesheet as we handle it in paintEvent
        self.title_bar_widget.setStyleSheet("")
        
        # Enable mouse tracking for the title bar
        self.title_bar_widget.setMouseTracking(True)
        self.title_bar_widget.setAttribute(QtCore.Qt.WA_Hover, True)

        # Don't override paintEvent - let the stylesheet handle background

        # Make the entire title bar draggable
        self.title_bar_widget.mousePressEvent = self.title_bar_mouse_press
        self.title_bar_widget.mouseMoveEvent = self.title_bar_mouse_move
        self.title_bar_widget.mouseReleaseEvent = self.title_bar_mouse_release
        
        # Install event filter for better mouse event handling
        self.title_bar_widget.installEventFilter(self)
        
        # Add a visible drag handle for Linux compatibility
        self.create_drag_handle()

        # Style media control buttons to be clearly visible
        for btn in [prev_btn, self.play_pause_btn, next_btn, speed_down_btn, speed_up_btn, stop_full_btn]:
            btn.setFixedSize(50, 40)  # Normal button size
            btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(40, 40, 40, 0.3);
                    color: #ffffff;
                    border: none;
                    border-radius: 8px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: rgba(60, 60, 60, 0.5);
                    color: #f0f0f0;
                    border: none;
                }
                QPushButton:pressed {
                    background-color: rgba(20, 20, 20, 0.4);
                    color: #cccccc;
                    border: none;
                }
            """)
            
            # Make black icons appear white
            icon = btn.icon()
            if not icon.isNull():
                # Create a white version of the icon
                pixmap = icon.pixmap(20, 20)
                if not pixmap.isNull():
                    # Create a white mask
                    white_pixmap = pixmap.copy()
                    painter = QtGui.QPainter(white_pixmap)
                    painter.setCompositionMode(QtGui.QPainter.CompositionMode_SourceIn)
                    painter.fillRect(white_pixmap.rect(), QtGui.QColor(255, 255, 255))
                    painter.end()
                    
                    # Set the white icon
                    white_icon = QtGui.QIcon(white_pixmap)
                    btn.setIcon(white_icon)
        # Style speed bar to be clearly visible
        speed_bar.setFixedWidth(100)  # Normal width for the slider
        speed_bar.setStyleSheet("""
            QSlider::groove:horizontal {
                border: none;
                height: 8px;
                background: rgba(60, 60, 60, 0.9);
                margin: 3px 0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: rgba(240, 240, 240, 1.0);
                border: 2px solid rgba(255, 255, 255, 0.8);
                width: 18px;
                margin: -5px 0;
                border-radius: 9px;
            }
            QSlider::handle:horizontal:hover {
                background: rgba(255, 255, 255, 1.0);
                border: 2px solid rgba(255, 255, 255, 1.0);
            }
            QSlider::handle:horizontal:pressed {
                background: rgba(200, 200, 200, 1.0);
                border: 2px solid rgba(255, 255, 255, 1.0);
            }
        """)

        # Style window control buttons
        minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 0.3);
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        maximize_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 0.3);
                color: white;
                border: none;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(100, 100, 100, 0.3);
                color: white;
                border: none;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(232, 17, 35, 0.9);
            }
        """)

        # DON'T add title bar to main layout - it will be positioned as overlay later
        # self.main_layout.addWidget(self.title_bar_widget)
        
        # Parent will be set to content_widget after it's created
    
    def create_drag_handle(self):
        """Create a visible drag handle for Linux compatibility"""
        # Add a small drag handle at the left side of the title bar
        drag_handle = QtWidgets.QLabel("⋮⋮")
        drag_handle.setFixedSize(20, 40)
        drag_handle.setAlignment(QtCore.Qt.AlignCenter)
        drag_handle.setStyleSheet("""
            QLabel {
                background-color: rgba(60, 60, 60, 0.8);
                color: #ffffff;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QLabel:hover {
                background-color: rgba(80, 80, 80, 0.9);
            }
        """)
        
        # Make the drag handle draggable
        drag_handle.mousePressEvent = self.drag_handle_press
        drag_handle.mouseMoveEvent = self.drag_handle_move
        drag_handle.mouseReleaseEvent = self.drag_handle_release
        
        # Add to title bar layout
        if hasattr(self, 'title_bar_widget'):
            title_layout = self.title_bar_widget.layout()
            if title_layout:
                title_layout.insertWidget(0, drag_handle)

    def set_playback_speed_from_bar(self, value):
        """Set playback speed from slider (value: 25~400)"""
        speed = value / 100.0
        self.playback_speed = speed
        if hasattr(self, 'media_player'):
            self.media_player.setPlaybackRate(speed)

    def title_bar_paint_event(self, event):
        """Paint the title bar with 0.7 opacity background"""
        painter = QtGui.QPainter(self.title_bar_widget)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        # Set semi-transparent black background with 0.7 opacity (178 = 0.7 * 255)
        painter.fillRect(self.title_bar_widget.rect(), QtGui.QColor(40, 40, 40, 178))
        painter.end()
        # Call the default paint event to draw child widgets
        QtWidgets.QWidget.paintEvent(self.title_bar_widget, event)

    def title_bar_mouse_press(self, event):
        """Handle mouse press on title bar for dragging"""
        print(f"Title bar mouse press: {event.button()}, pos: {event.pos()}")
        if event.button() == QtCore.Qt.LeftButton:
            # Check if we're clicking on a button or control
            widget = self.title_bar_widget.childAt(event.pos())
            if not self.is_control_widget(widget):
                # Prefer native system move when available (Qt 5.15+)
                try:
                    win = self.windowHandle()
                    if win is not None and hasattr(win, 'startSystemMove'):
                        if win.startSystemMove():
                            event.accept()
                            return
                except Exception as e:
                    print(f"startSystemMove failed on title bar: {e}")
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                self.dragging = True
                self.setCursor(QtCore.Qt.ClosedHandCursor)
                print(f"Started dragging from title bar, position: {self.drag_position}")
                event.accept()
                return
        event.ignore()

    def title_bar_mouse_move(self, event):
        """Handle mouse move on title bar for dragging"""
        if event.buttons() == QtCore.Qt.LeftButton and self.dragging and self.drag_position is not None:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            print(f"Dragging window to: {new_pos}")
            event.accept()
            return
        event.ignore()
    
    def title_bar_mouse_release(self, event):
        """Handle mouse release on title bar"""
        if event.button() == QtCore.Qt.LeftButton:
            if self.dragging:
                print("Stopped dragging from title bar")
            self.dragging = False
            self.drag_position = None
            self.setCursor(QtCore.Qt.ArrowCursor)
            event.accept()
            return
        event.ignore()
    
    def drag_handle_press(self, event):
        """Handle mouse press on drag handle"""
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            self.dragging = True
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            event.accept()
    
    def drag_handle_move(self, event):
        """Handle mouse move on drag handle"""
        if event.buttons() == QtCore.Qt.LeftButton and self.dragging and self.drag_position is not None:
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            event.accept()
    
    def drag_handle_release(self, event):
        """Handle mouse release on drag handle"""
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
            self.drag_position = None
            self.setCursor(QtCore.Qt.ArrowCursor)
            event.accept()

    def toggle_fullscreen(self):
        """Toggle fullscreen mode"""
        # Allow fullscreen regardless of play state
        
        if self.is_fullscreen:
            self.showNormal()
            self.is_fullscreen = False
            # Restore fixed size and geometry
            self.setFixedSize(self.FIXED_WIDTH, self.FIXED_HEIGHT)
            # Center the window when exiting fullscreen
            x = (self.screen_width - self.FIXED_WIDTH) // 2
            y = (self.screen_height - self.FIXED_HEIGHT) // 2
            self.setGeometry(x, y, self.FIXED_WIDTH, self.FIXED_HEIGHT)
            self.setCursor(QtCore.Qt.ArrowCursor)
            print(f"Exited fullscreen, window size: {self.FIXED_WIDTH}x{self.FIXED_HEIGHT}")
            # Restore title bar as overlay at top (not in layout)
            try:
                self.title_bar_widget.setParent(self.content_widget)
                self.position_overlay_title_bar()
            except Exception as e:
                print(f"Error restoring title bar overlay: {e}")
            # Stop mouse inactivity timer when exiting fullscreen
            self.mouse_inactivity_timer.stop()
            # Ensure cursor timer is stopped and cursor visible
            try:
                self.cursor_inactivity_timer.stop()
                self.setCursor(QtCore.Qt.ArrowCursor)
            except Exception as e:
                print(f"Error stopping cursor timer on exit: {e}")
            self.controls_visible_in_fullscreen = False
            # Restore controls widget parent to content_widget for windowed mode
            self.bottom_controls_widget.setParent(self.content_widget)
            self.position_overlay_controls()  # This will show the controls
            self.position_overlay_title_bar()  # This will show the title bar overlay
            self.refresh_current_content()
        else:
            self.showFullScreen()
            self.is_fullscreen = True
            # Use full screen resolution for maximum quality
            self.setFixedSize(self.screen_width, self.screen_height)
            self.setCursor(QtCore.Qt.BlankCursor)
            print(f"Entered fullscreen, screen resolution: {self.screen_width}x{self.screen_height}")
            # Prepare title bar as overlay (will be shown via animation)
            try:
                if self.title_bar_widget.parent() != self:
                    self.title_bar_widget.setParent(self)
                self.title_bar_widget.hide()
                self.title_bar_widget.raise_()
            except Exception as e:
                print(f"Error preparing title bar overlay: {e}")
            # Hide controls initially in fullscreen
            self.bottom_controls_widget.hide()
            self.controls_visible_in_fullscreen = False
            print("Entered fullscreen mode - controls will show on mouse movement")
            
            # Test: Force show controls after a short delay to verify they work
            QTimer.singleShot(1000, self.test_show_controls)
            
            self.refresh_current_content()

    def toggle_maximize(self):
        """Toggle maximize/restore window with optimal resolution"""
        if self.is_maximized:
            self.showNormal()
            self.setFixedSize(self.FIXED_WIDTH, self.FIXED_HEIGHT)
            # Center the window when restoring
            x = (self.screen_width - self.FIXED_WIDTH) // 2
            y = (self.screen_height - self.FIXED_HEIGHT) // 2
            self.setGeometry(x, y, self.FIXED_WIDTH, self.FIXED_HEIGHT)
            self.is_maximized = False
            print(f"Restored window, size: {self.FIXED_WIDTH}x{self.FIXED_HEIGHT}")
            self.refresh_current_content()  # Ensure background/image/video fills window
        else:
            self.old_geometry = self.geometry()
            self.showMaximized()
            self.is_maximized = True
            print(f"Maximized window, using full screen area: {self.screen_width}x{self.screen_height}")
            self.refresh_current_content()  # Ensure background/image/video fills window
    
    def set_high_resolution_mode(self):
        """Set window to 90% of screen size for high resolution display"""
        # Allow high resolution mode regardless of play state
        
        # Exit fullscreen/maximize if active
        if self.is_fullscreen:
            self.toggle_fullscreen()
        if self.is_maximized:
            self.toggle_maximize()
        
        # Set to 90% of screen size
        new_width = int(self.screen_width * 1)
        new_height = int(self.screen_height * 1)
        
        # Center the window
        x = (self.screen_width - new_width) // 2
        y = (self.screen_height - new_height) // 2
        
        self.setFixedSize(new_width, new_height)
        self.setGeometry(x, y, new_width, new_height)
        print(f"High resolution mode: {new_width}x{new_height}")
        self.refresh_current_content()
    
    def set_ultra_high_resolution_mode(self):
        """Set window to 100% of screen size (borderless fullscreen)"""
        # Allow ultra high resolution mode regardless of play state
        
        # Exit fullscreen/maximize if active
        if self.is_fullscreen:
            self.toggle_fullscreen()
        if self.is_maximized:
            self.toggle_maximize()
        
        # Set to full screen size but keep windowed mode
        self.setFixedSize(self.screen_width, self.screen_height)
        self.setGeometry(0, 0, self.screen_width, self.screen_height)
        print(f"Ultra high resolution mode: {self.screen_width}x{self.screen_height}")
        
        # Hide title bar for maximum content area
        self.title_bar_widget.hide()
        self.refresh_current_content()
    
    def restore_title_bar(self):
        """Restore title bar visibility"""
        if hasattr(self, 'title_bar_widget'):
            self.title_bar_widget.show()
            self.refresh_current_content()
    
    def restore_normal_mode(self):
        """Restore to normal windowed mode with original size"""
        # Exit fullscreen/maximize if active
        if self.is_fullscreen:
            self.toggle_fullscreen()
        if self.is_maximized:
            self.toggle_maximize()
        
        # Restore to original calculated size
        x = (self.screen_width - self.FIXED_WIDTH) // 2
        y = (self.screen_height - self.FIXED_HEIGHT) // 2
        
        self.setFixedSize(self.FIXED_WIDTH, self.FIXED_HEIGHT)
        self.setGeometry(x, y, self.FIXED_WIDTH, self.FIXED_HEIGHT)
        
        # Restore title bar
        self.restore_title_bar()
        print(f"Restored to normal mode: {self.FIXED_WIDTH}x{self.FIXED_HEIGHT}")

    def keyPressEvent(self, event):
        """Handle key press events with resolution controls"""
        if event.key() == QtCore.Qt.Key_F11:
            # Allow fullscreen regardless of play state
            self.toggle_fullscreen()
        elif event.key() == QtCore.Qt.Key_F10:
            # Toggle maximize for better resolution
            self.toggle_maximize()
        elif event.key() == QtCore.Qt.Key_F9:
            # Set to 90% of screen size for high resolution
            self.set_high_resolution_mode()
        elif event.key() == QtCore.Qt.Key_F8:
            # Set to 100% of screen size (borderless fullscreen)
            self.set_ultra_high_resolution_mode()
        elif event.key() == QtCore.Qt.Key_F7:
            # Restore to normal windowed mode
            self.restore_normal_mode()
        elif event.key() == QtCore.Qt.Key_Left:
            self.previous_item()
        elif event.key() == QtCore.Qt.Key_Right:
            self.next_item()
        elif event.key() == QtCore.Qt.Key_Space:
            self.toggle_play_pause()
        elif event.key() == QtCore.Qt.Key_Escape:
            if self.is_fullscreen:
                self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)

    def get_content_dimensions(self):
        """Get the appropriate content dimensions based on current mode"""
        try:
            if self.is_fullscreen:
                # In fullscreen, use the entire screen size for maximum resolution
                return self.screen_width, self.screen_height
            elif self.is_maximized:
                # In maximized mode, use the full screen minus taskbar/panel areas
                return self.screen_width, self.screen_height - 40  # Account for title bar
            else:
                # In windowed mode, use fixed window size minus title bar (controls overlay on top)
                return self.FIXED_WIDTH, self.FIXED_HEIGHT - 40
        except Exception as e:
            print(f"Error getting content dimensions: {e}")
            # Fallback to safe default dimensions
            try:
                return getattr(self, 'FIXED_WIDTH', 800), getattr(self, 'FIXED_HEIGHT', 600) - 40
            except:
                return 800, 560  # Absolute fallback

    def refresh_current_content(self):
        """Refresh current content to use correct dimensions and avoid overlapping widgets"""
        self.clear_layout()  # Always clear previous content first

        if not self.is_playing or not self.playlist:
            return

        # Get current item
        current_item = self.playlist[self.current_index - 1] if self.current_index > 0 else self.playlist[-1]
        path = current_item['path']

        # Determine if it's a video or image and refresh accordingly
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
        if path.lower().endswith(video_extensions):
            # If it's a video, restart it with new dimensions
            self.media_player.stop()
            if hasattr(self, 'gst_player'):
                self.gst_player.stop()
            self.play_video_flexible(path, current_item['duration'])
        else:
            # If it's an image, refresh it with new dimensions
            self.show_image(path, current_item['duration'])

    def get_currently_running_file(self):
        """Get the currently running file path"""
        if not self.playlist or self.current_index < 0 or self.current_index >= len(self.playlist):
            return None
        
        item = self.playlist[self.current_index]
        return item['path']

    def find_file_index_in_playlist(self, file_path):
        """Find the index of a specific file in the playlist"""
        for i, item in enumerate(self.playlist):
            if item['path'] == file_path:
                return i
        return -1

    def previous_item(self):
        """Go to previous file in playlist"""
        try:
            if not self.playlist:
                print("No playlist available")
                self.clear_layout()
                return
            
            if len(self.playlist) == 0:
                print("Playlist is empty")
                self.clear_layout()
                return
                
            print(f"Previous: Current index {self.current_index}")
            
            # Safely stop all current media
            self.safe_stop_all_media()
            
            # Clear all timers
            self.clear_all_timers()
            
            # Go to previous file (skip "repeat" entries). Wrap to last.
            new_index = self.current_index
            attempts = 0
            max_attempts = len(self.playlist)
            while attempts < max_attempts:
                new_index -= 1
                if new_index < 0:
                    new_index = len(self.playlist) - 1
                # Skip "repeat" entries
                if (isinstance(self.playlist[new_index], dict) and 
                    'path' in self.playlist[new_index] and 
                    self.playlist[new_index]['path'].lower() != "repeat"):
                    break
                attempts += 1
            
            self.current_index = new_index
            
            # Validate the new index is within bounds
            if self.current_index < 0 or self.current_index >= len(self.playlist):
                print(f"Invalid index {self.current_index}, resetting to 0")
                self.current_index = 0
                
            if self.current_index < len(self.playlist):
                new_file = self.playlist[self.current_index].get('path', 'unknown') if isinstance(self.playlist[self.current_index], dict) else 'unknown'
                print(f"Previous: Now at '{new_file}' (index {self.current_index})")
                
                # If currently playing, continue playing the new item
                if self.is_playing:
                    QTimer.singleShot(100, lambda: self.play_next(auto_advance=False))  # Don't auto-advance
                else:
                    # If not playing, immediately start playback of the selected item
                    self.is_stopped_at_frame = False
                    self.is_playing = True
                    self.play_pause_btn.setIcon(self.pause_icon)
                    self.play_pause_btn.setToolTip("Pause")
                    QTimer.singleShot(50, lambda: self.play_next(auto_advance=False))
            else:
                print("No valid items found, showing background")
                self.clear_layout()
        except Exception as e:
            print(f"Critical error in previous_item: {e}")
            import traceback
            traceback.print_exc()
            # Last resort: show background
            try:
                self.clear_layout()
            except:
                pass

    def next_item(self):
        """Go to next file in playlist"""
        try:
            if not self.playlist:
                print("No playlist available")
                self.clear_layout()
                return
            
            if len(self.playlist) == 0:
                print("Playlist is empty")
                self.clear_layout()
                return
                
            print(f"Next: Current index {self.current_index}")
            
            # Safely stop all current media
            self.safe_stop_all_media()
            
            # Clear all timers
            self.clear_all_timers()
            
            # Go to next file (skip "repeat" entries)
            new_index = self.current_index
            attempts = 0
            max_attempts = len(self.playlist)
            
            # If we're already at the last item, stay there
            if new_index == len(self.playlist) - 1:
                print("Already at the last item")
                # Show the current (last) item
                if self.current_index < len(self.playlist):
                    new_file = self.playlist[self.current_index].get('path', 'unknown') if isinstance(self.playlist[self.current_index], dict) else 'unknown'
                    print(f"Next: Staying at '{new_file}' (index {self.current_index})")
                    
                    # If not playing, just show the current item without auto-advancing
                    if not self.is_playing:
                        try:
                            self.show_current_item_only()
                        except Exception as e:
                            print(f"Error showing current item: {e}")
                            self.clear_layout()
                    else:
                        QTimer.singleShot(100, lambda: self.play_next(auto_advance=False))
                return
            
            while attempts < max_attempts:
                new_index += 1
                if new_index >= len(self.playlist):
                    # This shouldn't happen now, but just in case
                    new_index = len(self.playlist) - 1
                    break
                
                # Skip "repeat" entries
                if (isinstance(self.playlist[new_index], dict) and 
                    'path' in self.playlist[new_index] and 
                    self.playlist[new_index]['path'].lower() != "repeat"):
                    break
                attempts += 1
            
            self.current_index = new_index
            
            # Validate the new index is within bounds
            if self.current_index < 0 or self.current_index >= len(self.playlist):
                print(f"Invalid index {self.current_index}, resetting to 0")
                self.current_index = 0
                
            if self.current_index < len(self.playlist):
                new_file = self.playlist[self.current_index].get('path', 'unknown') if isinstance(self.playlist[self.current_index], dict) else 'unknown'
                print(f"Next: Now at '{new_file}' (index {self.current_index})")
                
                # If currently playing, continue playing the new item
                if self.is_playing:
                    QTimer.singleShot(100, lambda: self.play_next(auto_advance=False))  # Don't auto-advance
                else:
                    # If not playing, immediately start playback of the selected item
                    self.is_stopped_at_frame = False
                    self.is_playing = True
                    self.play_pause_btn.setIcon(self.pause_icon)
                    self.play_pause_btn.setToolTip("Pause")
                    QTimer.singleShot(50, lambda: self.play_next(auto_advance=False))
            else:
                print("No valid items found, showing background")
                self.clear_layout()
        except Exception as e:
            print(f"Critical error in next_item: {e}")
            import traceback
            traceback.print_exc()
            # Last resort: show background
            try:
                self.clear_layout()
            except:
                pass

    def show_current_item_only(self):
        """Show current item without auto-advancing to next"""
        try:
            if not self.playlist:
                print("No playlist items available")
                self.clear_layout()
                return

            if len(self.playlist) == 0:
                print("Playlist is empty")
                self.clear_layout()
                return
                
            # Validate current index
            if self.current_index < 0 or self.current_index >= len(self.playlist):
                print(f"Invalid current index {self.current_index}, resetting to 0")
                self.current_index = 0

            # Double-check index is still valid after reset
            if self.current_index >= len(self.playlist):
                print("Index still invalid after reset, showing background")
                self.clear_layout()
                return

            item = self.playlist[self.current_index]
            print(f"Showing: {item['path']}")

            # Validate item structure
            if not isinstance(item, dict) or 'path' not in item:
                print(f"Invalid item structure: {item}")
                self.clear_layout()
                return

            # Check for repeat
            if item['path'].lower() == "repeat":
                self.current_index = 0
                if len(self.playlist) > 0:
                    item = self.playlist[self.current_index]
                    if not isinstance(item, dict) or 'path' not in item:
                        print("Invalid item after repeat")
                        self.clear_layout()
                        return
                else:
                    print("No items in playlist after repeat")
                    self.clear_layout()
                    return

            path = item['path']
            duration = item.get('duration', 5)  # Default duration if missing

            # Check if file exists
            if not os.path.exists(path):
                print(f"File not found: {path}")
                # Show background instead
                self.clear_layout()
                return

            # Determine if it's a video or image
            video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
            if path.lower().endswith(video_extensions):
                # For videos, show first frame only (don't auto-play)
                self.show_video_first_frame(path)
            else:
                # For images, show them indefinitely
                self.show_image_indefinitely(path)
        except Exception as e:
            print(f"Critical error in show_current_item_only: {e}")
            import traceback
            traceback.print_exc()
            # Show background as fallback
            try:
                self.clear_layout()
            except Exception as e2:
                print(f"Error in fallback clear_layout: {e2}")
                # Last resort: just set black background
                try:
                    self.content_widget.setStyleSheet("background-color: black;")
                except:
                    pass

    def show_video_first_frame(self, path):
        """Show first frame of video without playing"""
        if not OPENCV_AVAILABLE:
            print("OpenCV not available for video preview")
            self.clear_layout()  # Show background instead
            return
            
        try:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                print(f"Could not open video file: {path}")
                self.clear_layout()  # Show background instead
                return
            
            # Read first frame
            ret, frame = cap.read()
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # Create pixmap and scale
                pixmap = QPixmap.fromImage(qt_image)
                content_width, content_height = self.get_content_dimensions()
                scaled_pixmap = pixmap.scaled(content_width, content_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                
                # Clear layout and show frame (no background while previewing)
                self.clear_layout(show_background=False)
                self.current_label = QLabel()
                self.current_label.setPixmap(scaled_pixmap)
                self.current_label.setAlignment(QtCore.Qt.AlignCenter)
                self.current_label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
                self.current_label.setFixedSize(content_width, content_height)
                self.content_layout.addWidget(self.current_label)
                
                # Ensure controls are visible
                if not self.is_fullscreen:
                    self.position_overlay_controls()
                    self.position_overlay_title_bar()
                
                print(f"Showing first frame of video: {path}")
            else:
                print(f"Could not read first frame from video: {path}")
                self.clear_layout()  # Show background instead
            
            cap.release()
            
        except Exception as e:
            print(f"Error showing video frame: {e}")
            self.clear_layout()  # Show background instead

    def show_image_indefinitely(self, path):
        """Show image indefinitely without timer"""
        print(f"Showing image indefinitely: {path}")
        
        try:
            # Clear any existing widgets (no background during preview)
            self.clear_layout(show_background=False)
            
            # Try to load image with multiple methods
            pixmap = None
            
            # Method 1: Try PyQt5 QPixmap (primary method)
            try:
                pixmap = QPixmap(path)
                if not pixmap.isNull():
                    print("Image loaded successfully with PyQt5")
                else:
                    pixmap = None
            except Exception as e:
                print(f"PyQt5 image loading failed: {e}")
                pixmap = None
            
            # Method 2: Try OpenCV as fallback if PyQt5 failed
            if pixmap is None and OPENCV_AVAILABLE:
                try:
                    print("Trying OpenCV for image loading...")
                    img = cv2.imread(path)
                    if img is not None:
                        # Convert BGR to RGB
                        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                        h, w, ch = img_rgb.shape
                        bytes_per_line = ch * w
                        qt_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                        pixmap = QPixmap.fromImage(qt_image)
                        print("Image loaded successfully with OpenCV")
                except Exception as e:
                    print(f"OpenCV image loading failed: {e}")
                    pixmap = None
            
            # If all methods failed
            if pixmap is None or pixmap.isNull():
                print(f"Could not load image with any method: {path}")
                # Keep the cleared layout (shows background)
                return
                
            self.current_label = QLabel()
            # Get appropriate content dimensions based on current mode
            content_width, content_height = self.get_content_dimensions()
            
            # Always show entire content (may have black bars)
            scaled_pixmap = pixmap.scaled(content_width, content_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            self.current_label.setPixmap(scaled_pixmap)
            self.current_label.setAlignment(QtCore.Qt.AlignCenter)
            self.current_label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
            self.current_label.setFixedSize(content_width, content_height)
            self.content_layout.addWidget(self.current_label)
            
            # Ensure controls are visible and positioned after showing image
            if not self.is_fullscreen:
                self.position_overlay_controls()
                self.position_overlay_title_bar()
                
        except Exception as e:
            print(f"Error in show_image_indefinitely: {e}")
            # Show background as fallback
            self.clear_layout()

    def stop_and_return_to_background(self):
        """Stop playback completely and return to background image"""
        print("Stopping all media and returning to background...")
        
        # Safely stop all media playback
        self.safe_stop_all_media()
        
        # Clear all timers
        self.clear_all_timers()
        
        # Reset all states completely
        self.is_playing = False
        self.currently_playing_video = False
        self.currently_showing_image = False
        self.is_stopped_at_frame = False
        
        # Update button state
        self.play_pause_btn.setIcon(self.play_icon)
        self.play_pause_btn.setToolTip("Play")
        
        # Clear layout and show background
        self.clear_layout()
        print("Stopped playback completely and returned to background")

    def pause_at_current_frame(self):
        """Pause playback at current frame (for play/pause button)"""
        # Pause all media playback to keep current frame displayed
        if hasattr(self, 'media_player'):
            self.media_player.pause()  # Pause instead of stop to keep frame
        if hasattr(self, 'gst_player'):
            self.gst_player.pause()  # Pause instead of stop to keep frame
        if hasattr(self, 'video_timer'):
            self.video_timer.stop()  # Stop timer but keep current frame
        # Keep video_cap open to maintain current frame
        
        # Clear all timers (this will stop image progression timers too)
        self.clear_all_timers()
        
        # Reset playing state but keep current content displayed
        self.is_playing = False
        # Set flag to indicate we're stopped at current frame
        self.is_stopped_at_frame = True
        # Don't reset currently_playing_video and currently_showing_image flags
        # so we can detect what type of media was paused
        
        # Update button state
        self.play_pause_btn.setIcon(self.play_icon)
        self.play_pause_btn.setToolTip("Play")
        
        print("Paused playback at current frame")

    def play_current(self):
        """Play current item"""
        if not self.is_playing:
            self.is_playing = True
            self.play_pause_btn.setIcon(self.pause_icon)
            self.play_pause_btn.setToolTip("Pause")
            self.play_next()
        elif hasattr(self, 'media_player'):
            self.media_player.play()
            # Update button state when resuming
            self.play_pause_btn.setIcon(self.pause_icon)
            self.play_pause_btn.setToolTip("Pause")

    def pause_current(self):
        """Pause current item"""
        if hasattr(self, 'media_player'):
            self.media_player.pause()
        if hasattr(self, 'gst_player'):
            self.gst_player.pause()
        if hasattr(self, 'video_timer'):
            self.video_timer.stop()
        # Keep video_cap open to maintain current frame
        
        # Clear all timers to pause image progression
        self.clear_all_timers()
        
        # Set playing state to False so play button can resume
        self.is_playing = False
        # Clear stopped at frame flag since we're pausing, not stopping
        self.is_stopped_at_frame = False
        
        # Update button state
        self.play_pause_btn.setIcon(self.play_icon)
        self.play_pause_btn.setToolTip("Play")
        print("⏸️ Paused playback")
    
    def resume_current(self):
        """Resume current item"""
        # Set playing state to True
        self.is_playing = True
        
        if hasattr(self, 'media_player'):
            self.media_player.play()
        if hasattr(self, 'gst_player'):
            self.gst_player.play()
        if hasattr(self, 'video_timer') and hasattr(self, 'video_cap') and self.video_cap is not None:
            # For OpenCV videos, restart the timer with proper delay
            if hasattr(self, 'video_fps') and hasattr(self, 'playback_speed'):
                self.video_frame_delay = max(16, int(1000 / (self.video_fps * self.playback_speed)))
                self.video_timer.start(self.video_frame_delay)
                # Restore the video playing state
                self.currently_playing_video = True
            else:
                self.video_timer.start()
                # Restore the video playing state
                self.currently_playing_video = True
        
        # Update button state
        self.play_pause_btn.setIcon(self.pause_icon)
        self.play_pause_btn.setToolTip("Pause")
        print("▶️ Resumed playback")

    def stop_current(self):
        """Stop playback and clear display"""
        # Safely stop all media
        self.safe_stop_all_media()
        
        self.is_playing = False
        self.play_pause_btn.setIcon(self.play_icon)
        self.play_pause_btn.setToolTip("Play")
        self.clear_layout()  # Clear the display immediately

    def toggle_play_pause(self):
        """Toggle between play and pause"""
        if not self.is_playing:
            # Currently stopped, check if we can resume from current frame
            can_resume = False
            
            # Check if media player is paused (Qt Multimedia)
            if hasattr(self, 'media_player') and self.media_player.state() == QMediaPlayer.PausedState:
                can_resume = True
                self.resume_current()
                print("▶️ Resumed video playback from paused state")
            
            # Check if GStreamer player is paused
            elif hasattr(self, 'gst_player') and self.gst_player and not self.gst_player.is_playing:
                can_resume = True
                self.resume_current()
                print("▶️ Resumed GStreamer video playback from paused state")
            
            # Check if OpenCV video is paused (has video_cap but timer stopped)
            elif hasattr(self, 'video_cap') and self.video_cap is not None and hasattr(self, 'video_timer') and not self.video_timer.isActive():
                can_resume = True
                self.resume_current()
                print("▶️ Resumed OpenCV video playback from paused state")
            
            # Check if we have a paused video (from stop button or pause)
            elif self.is_stopped_at_frame and hasattr(self, 'current_label') and self.current_label and hasattr(self, 'video_cap') and self.video_cap is not None:
                can_resume = True
                self.is_stopped_at_frame = False  # Clear the flag
                self.resume_current()
                print("▶️ Resumed video playback from stopped state")
            
            # Check if an image is being shown (has current_label but no active timers)
            elif hasattr(self, 'current_label') and self.current_label and len(self.active_timers) == 0:
                can_resume = True
                self.is_playing = True
                self.play_pause_btn.setIcon(self.pause_icon)
                self.play_pause_btn.setToolTip("Pause")
                # For images, we need to restart the timer for the current item
                current_item = self.playlist[self.current_index]
                duration = current_item['duration']
                self.safe_timer_singleShot(duration * 1000, self.play_next)
                print("▶️ Resumed image playback from paused state")
            
            if not can_resume:
                # No paused media to resume, start fresh playback
                self.is_playing = True
                self.is_stopped_at_frame = False  # Clear stopped flag for fresh start
                self.play_pause_btn.setIcon(self.pause_icon)
                self.play_pause_btn.setToolTip("Pause")
                print("🎬 Starting fresh playback...")
                self.play_next()
        else:
            # Currently playing, pause it
            self.pause_current()

    def seek_relative(self, seconds):
        """Seek forward or backward by seconds"""
        if hasattr(self, 'media_player') and self.media_player.isAvailable():
            pos = self.media_player.position() + int(seconds * 1000)
            self.media_player.setPosition(max(0, pos))

    def change_playback_speed(self, delta):
        """Change playback speed (0.25x to 4x) and update slider"""
        if not hasattr(self, 'playback_speed'):
            self.playback_speed = 1.0
        new_speed = min(4.0, max(0.25, self.playback_speed + delta))
        self.playback_speed = new_speed
        self.speed_bar.blockSignals(True)
        self.speed_bar.setValue(int(new_speed * 100))
        self.speed_bar.blockSignals(False)
        if hasattr(self, 'media_player'):
            self.media_player.setPlaybackRate(new_speed)

    def load_playlist(self, file_path):
        playlist = []
        if not os.path.exists(file_path):
            print(f"Playlist file not found: {file_path}")
            # Create a sample playlist for testing
            return [
                {'path': 'test_image.jpg', 'duration': 3, 'start_time': '08:00:00', 'end_time': '08:00:03'},
                {'path': 'test_video.mp4', 'duration': 10, 'start_time': '08:00:03', 'end_time': '08:00:13'}
            ]
        
        try:
            with open(file_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    parts = line.split(',')
                    if len(parts) < 3:
                        continue
                    
                    # Handle both old format (3 fields) and new format (5+ fields)
                    if len(parts) >= 5:
                        # New format: index, path, duration, start_time, end_time
                        index, path, duration, start_time, end_time = parts[:5]
                        playlist.append({
                            'path': path, 
                            'duration': int(duration),
                            'start_time': start_time,
                            'end_time': end_time
                        })
                    else:
                        # Old format: index, path, duration
                        index, path, duration = parts[:3]
                        playlist.append({
                            'path': path, 
                            'duration': int(duration),
                            'start_time': '00:00:00',
                            'end_time': '00:00:00'
                        })
        except Exception as e:
            print(f"Error loading playlist: {e}")
            
        return playlist

    def shuffle_playlist(self):
        import random
        random.shuffle(self.playlist)
        self.current_index = 0

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        if self.shuffle:
            self.shuffle_playlist()

    def toggle_repeat(self):
        self.repeat = not self.repeat

    def play_next(self, auto_advance=True):
        if not self.is_playing:
            return  # Do not auto-play unless play button was pressed

        # Reset media states before playing next item
        self.currently_playing_video = False
        self.currently_showing_image = False
        self.clear_all_timers()

        if not self.playlist:
            print("No playlist items available")
            return

        item = self.playlist[self.current_index]
        print(f"Playing: {item['path']}")

        # Check for repeat
        if item['path'].lower() == "repeat":
            self.current_index = 0
            item = self.playlist[self.current_index]

        path = item['path']
        duration = item['duration']

        # Check if file exists
        if not os.path.exists(path):
            print(f"File not found: {path}")
            if auto_advance:
                # In single file mode, just close the application
                if self.is_single_file_mode:
                    print("Single file not found, exiting")
                    self.close()
                    return
                
                self.current_index += 1
                if self.current_index >= len(self.playlist):
                    self.current_index = 0
                # Only continue if there are other items in playlist
                if len(self.playlist) > 1:
                    self.timer.singleShot(2000, self.play_next)
                else:
                    print("No valid files in playlist, exiting")
                    self.close()
            return

        # Determine if it's a video or image
        video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
        if path.lower().endswith(video_extensions):
            # Use the most flexible video playback method
            self.play_video_flexible(path, duration)
        else:
            self.show_image(path, duration)

        # Only auto-advance index if this is called from automatic progression
        if auto_advance and not self.repeat:
            self.current_index += 1
            if self.current_index >= len(self.playlist):
                self.current_index = 0

    def play_video(self, path):
        print(f"Playing video: {path}")
        # Clear any existing widgets (no background during preview)
        self.clear_layout(show_background=False)
        
        # Create video widget
        video_widget = QtMultimediaWidgets.QVideoWidget()
        video_widget.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
        video_widget.setAspectRatioMode(QtCore.Qt.IgnoreAspectRatio)
        video_widget.setAttribute(QtCore.Qt.WA_OpaquePaintEvent, True)
        
        # Set size for video widget to fill content area based on current mode
        content_width, content_height = self.get_content_dimensions()
        video_widget.setFixedSize(content_width, content_height)
        
        # Set aspect ratio mode based on current mode
        if self.is_fullscreen:
            video_widget.setAspectRatioMode(QtCore.Qt.IgnoreAspectRatio)  # Fill entire screen
        else:
            video_widget.setAspectRatioMode(QtCore.Qt.KeepAspectRatio)  # Show full content
        
        self.content_layout.addWidget(video_widget)
        
        # Ensure controls are visible and positioned after adding video widget
        if not self.is_fullscreen:
            self.position_overlay_controls()
            self.position_overlay_title_bar()
        
        # Set up media player with optimized settings
        self.media_player.setVideoOutput(video_widget)
        self.media_player.setVolume(100)  # Ensure audio is enabled
        
        # Convert path to proper URL format
        file_url = QUrl.fromLocalFile(os.path.abspath(path))
        media_content = QMediaContent(file_url)
        
        # Set media and start playing
        self.media_player.setMedia(media_content)
        
        # Try to play the video
        self.media_player.play()
        
        # If video fails to play, show error message and move to next
        QTimer.singleShot(3000, self.check_video_status)

    def show_image(self, path, duration):
        print(f"Showing image: {path} for {duration} seconds")
        
        # Set image showing state and clear any conflicting timers
        self.currently_showing_image = True
        self.currently_playing_video = False
        self.clear_all_timers()
        
        # Clear any existing widgets
        self.clear_layout()
        
        # Try to load image with multiple methods
        pixmap = None
        
        # Method 1: Try PyQt5 QPixmap (primary method)
        try:
            pixmap = QPixmap(path)
            if not pixmap.isNull():
                print("Image loaded successfully with PyQt5")
            else:
                pixmap = None
        except Exception as e:
            print(f"PyQt5 image loading failed: {e}")
            pixmap = None
        
        # Method 2: Try OpenCV as fallback if PyQt5 failed
        if pixmap is None and OPENCV_AVAILABLE:
            try:
                print("Trying OpenCV for image loading...")
                img = cv2.imread(path)
                if img is not None:
                    # Convert BGR to RGB
                    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    h, w, ch = img_rgb.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                    pixmap = QPixmap.fromImage(qt_image)
                    print("Image loaded successfully with OpenCV")
            except Exception as e:
                print(f"OpenCV image loading failed: {e}")
                pixmap = None
        
        # If all methods failed
        if pixmap is None or pixmap.isNull():
            print(f"Could not load image with any method: {path}")
            self.current_index += 1
            if self.current_index >= len(self.playlist):
                self.current_index = 0
            self.timer.singleShot(2000, self.play_next)
            return
            
        self.current_label = QLabel()
        # Get appropriate content dimensions based on current mode
        content_width, content_height = self.get_content_dimensions()
        
        # Always show entire content (may have black bars)
        scaled_pixmap = pixmap.scaled(content_width, content_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
        self.current_label.setPixmap(scaled_pixmap)
        self.current_label.setAlignment(QtCore.Qt.AlignCenter)
        self.current_label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
        self.current_label.setFixedSize(content_width, content_height)
        self.content_layout.addWidget(self.current_label)
        
        # Ensure controls are visible and positioned after showing image
        if not self.is_fullscreen:
            self.position_overlay_controls()
            self.position_overlay_title_bar()
        
        # Set timer for next item
        if self.is_single_file_mode:
            # In single file mode, close after duration
            QTimer.singleShot(duration * 1000, self.close)
        else:
            self.safe_timer_singleShot(duration * 1000, self.play_next)

    def clear_layout(self, show_background=True):
        try:
            # Remove all widgets from content layout
            while self.content_layout.count():
                child = self.content_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()

            # Show background image only when requested and not playing
            if show_background and not self.is_playing:
                try:
                    bg_path = "icons/background.jpg"
                    if os.path.exists(bg_path):
                        # Only one label for background
                        label = QLabel()
                        pixmap = QPixmap(bg_path)
                        if not pixmap.isNull():
                            # Use full content widget dimensions for background (overlays will sit on top)
                            content_width = self.content_widget.width()
                            content_height = self.content_widget.height()
                            # Fill entire content area - overlays will sit on top
                            scaled_pixmap = pixmap.scaled(content_width, content_height, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
                            label.setPixmap(scaled_pixmap)
                            label.setAlignment(QtCore.Qt.AlignCenter)
                            label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
                            label.setFixedSize(content_width, content_height)
                            self.content_layout.addWidget(label)
                            
                            # Ensure controls are visible and positioned after showing background
                            if not self.is_fullscreen:
                                self.position_overlay_controls()
                                self.position_overlay_title_bar()
                        else:
                            print("Background image is null, showing black background")
                            # Create a simple black background that fills entire content area
                            label = QLabel()
                            label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
                            content_width = self.content_widget.width()
                            content_height = self.content_widget.height()
                            label.setFixedSize(content_width, content_height)
                            self.content_layout.addWidget(label)
                    else:
                        print(f"Background image not found: {bg_path}")
                        # Create a simple black background that fills entire content area
                        label = QLabel()
                        label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
                        content_width = self.content_widget.width()
                        content_height = self.content_widget.height()
                        label.setFixedSize(content_width, content_height)
                        self.content_layout.addWidget(label)
                except Exception as e:
                    print(f"Error showing background: {e}")
                    # Create a simple black background as fallback that fills entire content area
                    try:
                        label = QLabel()
                        label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
                        content_width = self.content_widget.width()
                        content_height = self.content_widget.height()
                        label.setFixedSize(content_width, content_height)
                        self.content_layout.addWidget(label)
                    except Exception as e2:
                        print(f"Error creating fallback background: {e2}")
        except Exception as e:
            print(f"Error in clear_layout: {e}")
            # Last resort: just set black background
            try:
                self.content_widget.setStyleSheet("background-color: black;")
            except:
                pass

    def on_state_changed(self, state):
        print(f"Media player state changed to: {state}")
        if state == QMediaPlayer.StoppedState:
            print("Video finished, moving to next item")
            self.timer.singleShot(500, self.play_next)

    def on_media_status_changed(self, status):
        print(f"Media status changed to: {status}")
        if status == QMediaPlayer.EndOfMedia:
            print("Media finished, moving to next item")
            self.timer.singleShot(500, self.play_next)
        elif status == QMediaPlayer.LoadedMedia:
            print("Media loaded successfully")
        elif status == QMediaPlayer.InvalidMedia:
            print("Invalid media format, skipping to next item")
            self.timer.singleShot(1000, self.play_next)
        elif status == QMediaPlayer.NoMedia:
            print("No media loaded")

    def on_media_error(self, error):
        print(f"Media player error: {error}")
        print("Skipping to next item due to playback error")
        self.timer.singleShot(2000, self.play_next)

    def check_video_status(self):
        """Check if video is actually playing"""
        if hasattr(self, 'media_player'):
            if self.media_player.state() == QMediaPlayer.StoppedState:
                print("Video failed to play, moving to next item")
                self.timer.singleShot(1000, self.play_next)

    def play_video_flexible(self, path, duration=None):
        """Smart video player with multiple fallback strategies"""
        print(f"Playing video: {path}")
        
        # Determine the best playback method based on file format and available libraries
        video_extensions = {
            '.mp4': ['opencv', 'qt_multimedia', 'gstreamer'],
            '.avi': ['opencv', 'qt_multimedia', 'gstreamer'],
            '.mkv': ['gstreamer', 'opencv', 'qt_multimedia'],
            '.mov': ['qt_multimedia', 'gstreamer', 'opencv'],
            '.wmv': ['gstreamer', 'opencv', 'qt_multimedia'],
            '.flv': ['gstreamer', 'opencv', 'qt_multimedia'],
            '.webm': ['gstreamer', 'qt_multimedia', 'opencv']
        }
        
        # Get file extension
        file_ext = os.path.splitext(path)[1].lower()
        preferred_methods = video_extensions.get(file_ext, ['opencv', 'qt_multimedia', 'gstreamer'])
        
        # Try each method in order of preference
        for method in preferred_methods:
            if method == 'opencv' and OPENCV_AVAILABLE:
                print(f"Trying OpenCV for {file_ext} video...")
                if self.play_video_opencv_simple(path, duration):
                    return True
            elif method == 'qt_multimedia':
                print(f"Trying Qt Multimedia for {file_ext} video...")
                if self.play_video_qt_multimedia(path, duration):
                    return True
            elif method == 'gstreamer' and GSTREAMER_AVAILABLE:
                print(f"Trying GStreamer for {file_ext} video...")
                if self.play_video_direct_gstreamer(path, duration):
                    return True
        
        # If all methods fail, skip to next item
        print(f"All video playback methods failed for {path}")
        self.timer.singleShot(1000, self.play_next)
        return False
    
    def play_video_direct_gstreamer(self, path, duration=None):
        """Direct GStreamer video playback with fallback"""
        if not GSTREAMER_AVAILABLE:
            return False
            
        try:
            # Clear any existing widgets
            self.clear_layout()
            
            # Create custom GStreamer video player
            self.gst_player = GStreamerVideoPlayer()
            
            # Set size for video widget
            content_width, content_height = self.get_content_dimensions()
            self.gst_player.setFixedSize(content_width, content_height)
            self.gst_player.setStyleSheet("background-color: black;")
            
            self.content_layout.addWidget(self.gst_player)
            
            # Ensure controls are visible
            if not self.is_fullscreen:
                self.position_overlay_controls()
                self.position_overlay_title_bar()
            
            # Setup and start GStreamer pipeline
            if self.gst_player.setup_pipeline(path):
                self.gst_player.play()
                
                # Check if it actually started playing
                QTimer.singleShot(2000, self.check_gst_video_status)
                
                # Set timer for duration-based playback if specified
                if duration:
                    self.timer.singleShot(duration * 1000, self.play_next)
                
                return True
            else:
                return False
                
        except Exception as e:
            print(f"Direct GStreamer error: {e}")
            return False
    
    def check_gst_video_status(self):
        """Check if GStreamer video is actually playing"""
        if hasattr(self, 'gst_player') and self.gst_player:
            if not self.gst_player.is_playing:
                print("GStreamer video failed to start, trying next method...")
                # The flexible method will automatically try the next approach
                return False
            else:
                print("GStreamer video is playing successfully!")
                return True
        return False
    
    def play_video_qt_multimedia(self, path, duration=None):
        """Qt Multimedia video playback with GStreamer backend"""
        try:
            # Clear any existing widgets
            self.clear_layout()
            
            # Create video widget
            video_widget = QtMultimediaWidgets.QVideoWidget()
            video_widget.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
            
            # Set size for video widget to fill content area based on current mode
            content_width, content_height = self.get_content_dimensions()
            video_widget.setFixedSize(content_width, content_height)
            
            # Set aspect ratio mode based on current mode
            if self.is_fullscreen:
                video_widget.setAspectRatioMode(QtCore.Qt.IgnoreAspectRatio)  # Fill entire screen
            else:
                video_widget.setAspectRatioMode(QtCore.Qt.KeepAspectRatio)  # Show full content
            
            self.content_layout.addWidget(video_widget)
            
            # Ensure controls are visible and positioned after adding video widget
            if not self.is_fullscreen:
                self.position_overlay_controls()
                self.position_overlay_title_bar()
            
            # Set up media player
            self.media_player.setVideoOutput(video_widget)
            self.media_player.setVolume(100)  # Ensure audio is enabled
            
            # Convert path to proper URL format
            file_url = QUrl.fromLocalFile(os.path.abspath(path))
            media_content = QMediaContent(file_url)
            
            # Set media and start playing
            self.media_player.setMedia(media_content)
            
            # Set playback speed if it was changed
            if hasattr(self, 'playback_speed'):
                self.media_player.setPlaybackRate(self.playback_speed)
            
            # Start playing the video
            self.media_player.play()
            
            # Set timer for duration-based playback if specified
            if duration:
                self.timer.singleShot(duration * 1000, self.play_next)
            
            # Check if video actually started playing after a short delay
            QTimer.singleShot(2000, self.check_qt_video_status)
            
            return True
            
        except Exception as e:
            print(f"Qt Multimedia error: {e}")
            return False
    
    def check_qt_video_status(self):
        """Check Qt Multimedia video status"""
        if hasattr(self, 'media_player'):
            state = self.media_player.state()
            if state == QMediaPlayer.PlayingState:
                print("Qt Multimedia video is playing successfully!")
            else:
                print(f"Qt Multimedia video state: {state}, may need fallback")
    
    def check_video_playback_status(self):
        """Check if video is actually playing and handle fallback"""
        if hasattr(self, 'media_player'):
            state = self.media_player.state()
            print(f"Video playback state: {state}")
            
            if state == QMediaPlayer.StoppedState:
                print("Video failed to start, trying OpenCV fallback...")
                # Skip retry and go directly to OpenCV fallback
                if OPENCV_AVAILABLE:
                    current_item = self.playlist[self.current_index - 1] if self.current_index > 0 else self.playlist[-1]
                    path = current_item['path']
                    duration = current_item['duration']
                    
                    # Only try OpenCV fallback for video files
                    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
                    if path.lower().endswith(video_extensions):
                        self.play_video_opencv_fallback(path, duration)
                    else:
                        print("Not a video file, moving to next item")
                        self.timer.singleShot(1000, self.play_next)
                else:
                    print("No fallback available, moving to next item")
                    self.timer.singleShot(1000, self.play_next)
            elif state == QMediaPlayer.PlayingState:
                print("Video is playing successfully!")
    
    def retry_video_playback(self):
        """Retry video playback with different settings"""
        try:
            # Get current item
            current_item = self.playlist[self.current_index - 1] if self.current_index > 0 else self.playlist[-1]
            path = current_item['path']
            duration = current_item['duration']
            
            # Only retry if it's actually a video file
            video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
            if not path.lower().endswith(video_extensions):
                print("Not a video file, skipping retry")
                self.timer.singleShot(1000, self.play_next)
                return
            
            print(f"Retrying video playback: {path}")
            
            # Try with different media player settings
            self.media_player.setVolume(0)  # Try without audio first
            file_url = QUrl.fromLocalFile(os.path.abspath(path))
            media_content = QMediaContent(file_url)
            self.media_player.setMedia(media_content)
            self.media_player.play()
            
            # Check again after retry
            QTimer.singleShot(2000, self.final_video_check)
            
        except Exception as e:
            print(f"Video retry failed: {e}")
            self.timer.singleShot(1000, self.play_next)
    
    def final_video_check(self):
        """Final check for video playback"""
        if hasattr(self, 'media_player'):
            state = self.media_player.state()
            if state != QMediaPlayer.PlayingState:
                print("GStreamer video playback failed, trying OpenCV fallback...")
                if OPENCV_AVAILABLE:
                    # Get current item and try OpenCV fallback
                    current_item = self.playlist[self.current_index - 1] if self.current_index > 0 else self.playlist[-1]
                    path = current_item['path']
                    duration = current_item['duration']
                    
                    # Only try OpenCV fallback for video files
                    video_extensions = ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm')
                    if path.lower().endswith(video_extensions):
                        self.play_video_opencv_fallback(path, duration)
                    else:
                        print("Not a video file, moving to next item")
                        self.timer.singleShot(1000, self.play_next)
                else:
                    print("No fallback available, moving to next item")
                    self.timer.singleShot(1000, self.play_next)
    
    def play_video_opencv_simple(self, path, duration=None):
        """Simple and reliable OpenCV video player"""
        print(f"Playing video with OpenCV: {path}")
        
        # Set video playing state and clear any conflicting timers
        self.currently_playing_video = True
        self.currently_showing_image = False
        self.clear_all_timers()
        
        try:
            cap = cv2.VideoCapture(path)
            if not cap.isOpened():
                print(f"OpenCV could not open video file: {path}")
                self.currently_playing_video = False
                return False
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            video_duration = frame_count / fps if fps > 0 else (duration or 30)
            
            # Use playlist duration if provided, otherwise use video duration
            play_duration = duration if duration else video_duration
            
            print(f"OpenCV Video FPS: {fps}, Video duration: {video_duration:.2f}s, Play duration: {play_duration:.2f}s")
            
            # Create label for displaying frames
            self.clear_layout()
            self.current_label = QLabel()
            self.current_label.setAlignment(QtCore.Qt.AlignCenter)
            self.current_label.setStyleSheet("background-color: black;")
            
            # Set size for video display area based on current mode
            content_width, content_height = self.get_content_dimensions()
            self.current_label.setFixedSize(content_width, content_height)
            self.current_label.setStyleSheet("background-color: black; margin: 0px; padding: 0px; border: none;")
            
            self.content_layout.addWidget(self.current_label)
            
            # Ensure controls are visible and positioned after adding video label
            if not self.is_fullscreen:
                self.position_overlay_controls()
                self.position_overlay_title_bar()
            
            # Initialize video playback variables
            self.video_cap = cap
            self.video_fps = fps if fps > 0 else 30
            self.video_duration = play_duration  # Use playlist duration
            self.video_start_time = time.time()
            self.playback_speed = getattr(self, 'playback_speed', 1.0)
            self.video_frame_delay = max(16, int(1000 / (self.video_fps * self.playback_speed)))  # Minimum 16ms for smooth playback
            
            # Set slider to current speed
            self.speed_bar.blockSignals(True)
            self.speed_bar.setValue(int(self.playback_speed * 100))
            self.speed_bar.blockSignals(False)
            
            # Use optimized timer for smooth playback
            self.video_timer = QTimer()
            self.video_timer.timeout.connect(self.update_video_frame)
            self.video_timer.start(self.video_frame_delay)
            
            print("OpenCV video playback started successfully!")
            return True
            
        except Exception as e:
            print(f"OpenCV video playback error: {e}")
            return False

    def update_video_frame(self):
        """Update video frame using OpenCV timer-based approach"""
        if not hasattr(self, 'video_cap') or self.video_cap is None:
            return
            
        try:
            # Calculate current position in video
            current_time = time.time() - self.video_start_time
            
            # Check if video has finished based on playlist duration
            if current_time >= self.video_duration:
                try:
                    if self.video_cap is not None:
                        self.video_cap.release()
                        self.video_cap = None
                except Exception as e:
                    print(f"Error releasing video capture: {e}")
                self.video_timer.stop()
                print(f"OpenCV video finished after {current_time:.2f} seconds")
                # Reset video state before moving to next
                self.currently_playing_video = False
                if self.is_single_file_mode:
                    print("Single file playback completed, closing application")
                    self.close()
                else:
                    self.safe_timer_singleShot(500, self.play_next)
                return
            
            # Read frame
            ret, frame = self.video_cap.read()
            if ret:
                # Convert BGR to RGB efficiently
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Convert to QImage with proper format
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
                
                # Create pixmap and always show full content (may have black bars)
                pixmap = QPixmap.fromImage(qt_image)
                content_width, content_height = self.get_content_dimensions()
                scaled_pixmap = pixmap.scaled(content_width, content_height, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                self.current_label.setPixmap(scaled_pixmap)
                
                # Update timer interval dynamically for consistent FPS
                if hasattr(self, 'video_frame_delay'):
                    self.video_timer.setInterval(self.video_frame_delay)
            else:
                # End of video file
                try:
                    if self.video_cap is not None:
                        self.video_cap.release()
                        self.video_cap = None
                except Exception as e:
                    print(f"Error releasing video capture: {e}")
                self.video_timer.stop()
                print("OpenCV video finished (end of file)")
                # Reset video state before moving to next
                self.currently_playing_video = False
                if self.is_single_file_mode:
                    print("Single file playback completed, closing application")
                    self.close()
                else:
                    self.safe_timer_singleShot(500, self.play_next)
                
        except Exception as e:
            print(f"Error updating video frame: {e}")
            self.video_timer.stop()
            try:
                if hasattr(self, 'video_cap') and self.video_cap is not None:
                    self.video_cap.release()
                    self.video_cap = None
            except Exception as release_error:
                print(f"Error releasing video capture in exception handler: {release_error}")
            # Reset video state before moving to next
            self.currently_playing_video = False
            if self.is_single_file_mode:
                print("Single file playback completed, closing application")
                self.close()
            else:
                self.safe_timer_singleShot(1000, self.play_next)

    def play_single_file(self, file_path, duration):
        """Play a single file for specified duration, then continue with playlist"""
        print(f"Playing single file: {file_path} for {duration} seconds, then continuing with playlist")
        
        # Load the full playlist
        playlist_path = "playlist.csv"
        if os.path.exists(playlist_path):
            self.playlist = self.load_playlist(playlist_path)
        else:
            # Create a sample playlist if none exists
            self.playlist = [
                {'path': 'test/4.jpg', 'duration': 1, 'start_time': '08:00:00', 'end_time': '08:00:01'},
                {'path': 'test/3.jpg', 'duration': 1, 'start_time': '08:00:01', 'end_time': '08:00:02'},
                {'path': 'test/2.jpg', 'duration': 30, 'start_time': '08:00:02', 'end_time': '08:00:32'},
                {'path': 'test/1.mp4', 'duration': 10, 'start_time': '08:00:32', 'end_time': '08:00:42'},
                {'path': 'repeat', 'duration': 0, 'start_time': '08:00:42', 'end_time': '08:00:42'}
            ]
        
        # Find the specified file in the playlist
        file_found = False
        for i, item in enumerate(self.playlist):
            if item['path'] == file_path:
                self.current_index = i
                # Override the duration with the specified duration
                self.playlist[i]['duration'] = duration
                file_found = True
                print(f"Found file at index {i}, overriding duration to {duration} seconds")
                break
        
        if not file_found:
            # If file not found in playlist, add it at the beginning
            print(f"File not found in playlist, adding at beginning")
            self.playlist.insert(0, {'path': file_path, 'duration': duration, 'start_time': '00:00:00', 'end_time': '00:00:00'})
            self.current_index = 0
        
        # Not single file mode - will continue with playlist
        self.is_single_file_mode = False
        
        # Start playing the file
        self.play_current()

    def check_for_commands(self):
        """Check for incoming commands from other instances"""
        import tempfile
        
        command_file = os.path.join(tempfile.gettempdir(), 'video_player_command.txt')
        
        try:
            if os.path.exists(command_file):
                with open(command_file, 'r') as f:
                    command_line = f.read().strip()
                
                if command_line:
                    parts = command_line.split(',')
                    if len(parts) >= 3 and parts[0] == 'play':
                        file_path = parts[1]
                        duration = int(parts[2])
                        
                        print(f"Received command: play {file_path} for {duration} seconds")
                        
                        # Execute the command
                        self.play_single_file(file_path, duration)
                        
                        # Remove the command file
                        os.remove(command_file)
                        
        except Exception as e:
            print(f"Error checking for commands: {e}")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Only reposition overlay controls when not in fullscreen mode
        if not self.is_fullscreen:
            self.position_overlay_controls()
            self.position_overlay_title_bar()

    def start_press_timer(self, event, action):
        """Start the timer for detecting long press"""
        if event.button() == QtCore.Qt.LeftButton:
            self.press_action = action  # Store the action (next or previous)
            self.is_long_press = False  # Reset the flag
            self.press_timer.start()  # Start the timer

    def stop_press_timer(self, event):
        """Stop the timer and check if it was a long press"""
        if event.button() == QtCore.Qt.LeftButton:
            self.press_timer.stop()  # Stop the timer
            if self.is_long_press:
                # Long press detected, perform the action
                if self.press_action == "next":
                    self.next_item()
                elif self.press_action == "previous":
                    self.previous_item()

    def handle_long_press(self):
        """Handle the long press action"""
        self.is_long_press = True  # Set the flag to indicate a long press
    
    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging and fullscreen controls"""
        if event.button() == QtCore.Qt.LeftButton:
            # Check if we're clicking on a button or control
            widget = self.childAt(event.pos())
            if not self.is_control_widget(widget):
                # Prefer native system move when available
                try:
                    win = self.windowHandle()
                    if win is not None and hasattr(win, 'startSystemMove'):
                        if win.startSystemMove():
                            event.accept()
                            return
                except Exception as e:
                    print(f"startSystemMove failed on window: {e}")
                # Fallback manual dragging
                self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
                self.dragging = True
                self.setCursor(QtCore.Qt.ClosedHandCursor)
                event.accept()
                return
        
        # Show controls on mouse press in fullscreen mode
        if self.is_fullscreen:
            self.show_fullscreen_controls()
            self.reset_mouse_cursor_timer()
            
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging and fullscreen controls"""
        if event.buttons() == QtCore.Qt.LeftButton and self.dragging and self.drag_position is not None:
            # Use globalPos for better Linux compatibility
            new_pos = event.globalPos() - self.drag_position
            self.move(new_pos)
            event.accept()
            return
        
        # Show controls on mouse movement in fullscreen mode
        if self.is_fullscreen:
            print(f"Mouse move detected in fullscreen - showing controls")
            self.show_fullscreen_controls()
            self.reset_mouse_cursor_timer()
            
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = False
            self.drag_position = None
            self.setCursor(QtCore.Qt.ArrowCursor)
            event.accept()
            return
        
        # Show controls on mouse release in fullscreen mode
        if self.is_fullscreen:
            print(f"Mouse release detected in fullscreen - showing controls")
            self.show_fullscreen_controls()
            self.reset_mouse_cursor_timer()
            
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event):
        """Handle mouse enter events for fullscreen controls"""
        if self.is_fullscreen:
            self.show_fullscreen_controls()
            self.reset_mouse_cursor_timer()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave events"""
        # Don't hide controls on mouse leave, let the timer handle it
        super().leaveEvent(event)
    
    def is_control_widget(self, widget):
        """Check if the widget is a control (button, slider, etc.)"""
        if widget is None:
            return False
            
        # Check if widget is a button, slider, or other control
        if isinstance(widget, (QtWidgets.QPushButton, QtWidgets.QSlider)):
            return True
        
        # Check if widget is inside media control areas (but NOT title bar)
        try:
            if hasattr(self, 'media_controls') and self.media_controls.isAncestorOf(widget):
                return True
            if hasattr(self, 'bottom_controls_widget') and self.bottom_controls_widget.isAncestorOf(widget):
                return True
        except:
            pass
            
        return False

class AlertMessage(QtWidgets.QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Alert")
        self.setModal(True)
        self.setFixedSize(400, 180)
        self.setStyleSheet("""
            QDialog {
                background: #f6f8fa;
                border: 2px solid #4d4d4d;
                border-radius: 12px;
            }
            QLabel {
                color: #222;
                font-size: 16px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                padding: 12px;
            }
            QPushButton {
                background: #4d4d4d;
                color: #fff;
                border-radius: 6px;
                font-size: 15px;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                padding: 8px 24px;
                margin-top: 16px;
            }
            QPushButton:hover {
                background: #222;
            }
        """)  # OfficeCity 0.9 style

        layout = QtWidgets.QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(10)

        label = QtWidgets.QLabel(message)
        label.setAlignment(QtCore.Qt.AlignCenter)
        layout.addWidget(label)

        button = QtWidgets.QPushButton("はい。")
        button.clicked.connect(self.accept)
        button.setFixedWidth(80)
        button.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Center the dialog on the screen
        self.center_on_screen()

    def center_on_screen(self):
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            screen.center().x() - size.width() // 2,
            screen.center().y() - size.height() // 2
        )

def parse_arguments():
    """Parse command line arguments"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Video Player with Playlist Support')
    parser.add_argument('--start', help='Start player with playlist file')
    parser.add_argument('--play', nargs=2, metavar=('FILE_PATH', 'DURATION'), 
                       help='Play specific file for duration seconds')
    parser.add_argument('--single-instance', action='store_true', 
                       help='Enable single instance mode (VLC-like behavior)')
    
    return parser.parse_args()

def check_single_instance():
    """Check if another instance is already running"""
    import fcntl
    import tempfile
    
    lock_file = os.path.join(tempfile.gettempdir(), 'video_player.lock')
    
    try:
        # Try to create and lock the file
        with open(lock_file, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            f.write(str(os.getpid()))
            return False  # No other instance running
    except (IOError, OSError):
        return True  # Another instance is running

def send_command_to_instance(file_path, duration):
    """Send play command to running instance via file"""
    import tempfile
    
    command_file = os.path.join(tempfile.gettempdir(), 'video_player_command.txt')
    try:
        with open(command_file, 'w') as f:
            f.write(f"play,{file_path},{duration}\n")
        print(f"Command sent to running instance: play {file_path} for {duration} seconds")
        return True
    except Exception as e:
        print(f"Failed to send command to running instance: {e}")
        return False

def create_sample_playlist(playlist_path):
    """Create sample playlist file"""
    if not os.path.exists(playlist_path):
        print(f"Creating sample playlist file: {playlist_path}")
        with open(playlist_path, 'w') as f:
            f.write("1,test/4.jpg,1,08:00:00,08:00:01,\n")
            f.write("2,test/3.jpg,1,08:00:01,08:00:02,\n")
            f.write("3,test/2.jpg,30,08:00:02,08:00:32,\n")
            f.write("4,test/1.mp4,60,08:00:32,08:01:32,\n")
            f.write("5,repeat,0,08:01:32,08:01:32,\n")
        print("Sample playlist created. Please add your media files and update the playlist.")

if __name__ == "__main__":
    args = parse_arguments()
    
    # Handle single-instance mode
    if args.single_instance or args.play:
        if args.play:
            # Check if another instance is running
            if check_single_instance():
                # Another instance is running, send command to it
                file_path, duration = args.play
                duration = int(duration)
                
                if not os.path.exists(file_path):
                    print(f"Error: File '{file_path}' not found!")
                    sys.exit(1)
                
                if send_command_to_instance(file_path, duration):
                    print("Command sent to running instance successfully")
                    sys.exit(0)
                else:
                    print("Failed to send command to running instance")
                    sys.exit(1)
            else:
                # No other instance running, start new one
                print("No running instance found, starting new player...")
        else:
            # Start mode with single-instance check
            if check_single_instance():
                print("Another instance is already running. Use --play command to send commands to it.")
                sys.exit(1)
    
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("Viewer")
    
    try:
        if args.start:
            # Start mode with playlist - auto fullscreen
            playlist_path = args.start
            create_sample_playlist(playlist_path)
            player = VideoPlayer(playlist_path, auto_fullscreen=True)
            player.show()
            sys.exit(app.exec_())
            
        elif args.play:
            # Play mode with specific file and duration
            file_path, duration = args.play
            duration = int(duration)
            
            if not os.path.exists(file_path):
                print(f"Error: File '{file_path}' not found!")
                sys.exit(1)
            
            # Create player with playlist for continuous playback
            playlist_path = "playlist.csv"
            create_sample_playlist(playlist_path)
            player = VideoPlayer(playlist_path, auto_fullscreen=False)
            player.play_single_file(file_path, duration)
            player.show()
            sys.exit(app.exec_())
            
        else:
            # Default mode - use default playlist (no auto fullscreen)
            playlist_path = "playlist.csv"
            create_sample_playlist(playlist_path)
            player = VideoPlayer(playlist_path, auto_fullscreen=False)
            player.show()
            sys.exit(app.exec_())
            
    except Exception as e:
        print(f"Error running application: {e}")
        sys.exit(1)
