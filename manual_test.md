# Manual Test Examples for Video Player

## Quick Test Commands

Here are real commands you can run to test the single file playback functionality:

### 1. Test Single Video File (10 seconds)
```bash
./run.sh play "/home/administrator001/Downloads/player/test/1.mp4" 10
```

### 2. Test Single Image File (5 seconds)
```bash
./run.sh play "/home/administrator001/Downloads/player/test/2.jpg" 5
```

### 3. Test Another Image (3 seconds)
```bash
./run.sh play "/home/administrator001/Downloads/player/test/3.jpg" 3
```

### 4. Test with Playlist
```bash
./run.sh start playlist.csv
```

## Single-Instance Test (VLC-like behavior)

### Step 1: Start a background player
```bash
./run.sh start playlist.csv &
```

### Step 2: Send commands to the running instance
```bash
# Wait a few seconds, then send play commands
./run.sh play "/home/administrator001/Downloads/player/test/1.mp4" 15
./run.sh play "/home/administrator001/Downloads/player/test/2.jpg" 8
./run.sh play "/home/administrator001/Downloads/player/test/3.jpg" 5
```

## Expected Behavior

1. **Single file mode**: Each `play` command should:
   - Open the video player window
   - Play the specified file for exactly the duration given
   - Close automatically when finished

2. **Single-instance mode**: 
   - First `start` command creates a running player
   - Subsequent `play` commands are sent to the running instance
   - No new windows should open for `play` commands

3. **Duration accuracy**: Files should play for exactly the specified number of seconds

## Troubleshooting

If you get errors:
- Make sure the file paths are correct
- Check that the files exist in the test directory
- Ensure the virtual environment is set up properly
- Try running `./run.sh` without arguments to see the help message
