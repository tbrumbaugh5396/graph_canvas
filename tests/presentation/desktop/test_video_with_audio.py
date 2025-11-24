#!/usr/bin/env python3
"""
Simple test script to verify video and audio functionality
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import sys
import os

# Add the project directory to Python path
sys.path.insert(0, '/Users/tombrumbaugh/Desktop/Dependency-Chart')

from graph_canvas.presentation.desktop.gui.sphere_3d import MediaScreen, MediaType, ScreenType
import time

def test_video_audio(video_path):
    """Test video loading and audio playback with a specific file"""
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print(f"🎥 Testing video: {video_path}")
    print("=" * 50)
    
    # Create a media screen
    screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.VIDEO)
    screen.name = f"Test Video ({os.path.basename(video_path)})"
    
    # Load the video
    print("📁 Loading video...")
    if screen.load_media(video_path):
        print("✅ Video loaded successfully")
        
        # Start playback
        print("▶️  Starting playback...")
        screen.start_video_playback()
        
        # Wait a few seconds to test
        print("⏳ Testing for 10 seconds...")
        for i in range(10):
            time.sleep(1)
            print(f"  {i+1}/10 seconds - Video playing: {screen.video_playing}, Audio time: {time.time() - screen.audio_start_time if screen.audio_start_time else 'None':.1f}s")
        
        # Stop playback
        print("⏹️  Stopping playback...")
        screen.stop_video_playback()
        
        print("✅ Test completed successfully")
        return True
        
    else:
        print("❌ Failed to load video")
        return False

def main():
    print("Video and Audio Test Script")
    print("=" * 40)
    
    if len(sys.argv) < 2:
        print("Usage: python3 test_video_with_audio.py <video_file_path>")
        print("\nExample:")
        print("  python3 test_video_with_audio.py /path/to/your/video.mp4")
        return
    
    video_path = sys.argv[1]
    success = test_video_audio(video_path)
    
    if success:
        print("\n🎉 Test passed! Your video should work in the main application.")
    else:
        print("\n💥 Test failed. Check the debug output above for issues.")

if __name__ == "__main__":
    main()
