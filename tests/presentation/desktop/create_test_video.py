#!/usr/bin/env python3
"""
Create a simple test video with audio for testing
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import subprocess
import os

def create_test_video_with_audio():
    """Create a simple test video with audio using FFmpeg"""
    
    output_path = "/Users/tombrumbaugh/Desktop/test_video_with_audio.mp4"
    
    print("🎬 Creating test video with audio...")
    print(f"📁 Output: {output_path}")
    
    try:
        # Create a 10-second test video with:
        # - Colored bars video (testsrc pattern)
        # - 440Hz sine wave audio
        result = subprocess.run([
            'ffmpeg', '-y',  # Overwrite if exists
            '-f', 'lavfi', '-i', 'testsrc=duration=10:size=640x480:rate=30',  # Video: test pattern
            '-f', 'lavfi', '-i', 'sine=frequency=440:duration=10',  # Audio: 440Hz tone
            '-c:v', 'libx264', '-pix_fmt', 'yuv420p',  # Video codec
            '-c:a', 'aac', '-b:a', '128k',  # Audio codec
            '-shortest',  # Stop when shortest stream ends
            output_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✅ Test video created successfully!")
            print(f"📊 File size: {size} bytes")
            print(f"🎵 Contains: 10-second video with 440Hz audio tone")
            print(f"📍 Location: {output_path}")
            return output_path
        else:
            print(f"❌ Failed to create test video")
            print(f"Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating test video: {e}")
        return None

def create_simple_audio_video():
    """Create an even simpler video - just audio with black screen"""
    
    output_path = "/Users/tombrumbaugh/Desktop/simple_audio_test.mp4"
    
    print("\n🎵 Creating simple audio test video...")
    print(f"📁 Output: {output_path}")
    
    try:
        # Create 5-second black video with beeping audio
        result = subprocess.run([
            'ffmpeg', '-y',
            '-f', 'lavfi', '-i', 'color=black:size=320x240:duration=5',  # Black video
            '-f', 'lavfi', '-i', 'sine=frequency=800:duration=5',  # 800Hz beep
            '-c:v', 'libx264', '-c:a', 'aac',
            '-shortest',
            output_path
        ], capture_output=True, text=True, timeout=20)
        
        if result.returncode == 0 and os.path.exists(output_path):
            size = os.path.getsize(output_path)
            print(f"✅ Simple test video created!")
            print(f"📊 File size: {size} bytes")
            print(f"🎵 Contains: 5-second black screen with 800Hz beep")
            return output_path
        else:
            print(f"❌ Failed to create simple test video")
            print(f"Error: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Error creating simple test video: {e}")
        return None

def main():
    print("Test Video Creator")
    print("=" * 30)
    print("This will create test videos with audio for testing the video player.\n")
    
    # Try to create test videos
    test_video = create_test_video_with_audio()
    simple_video = create_simple_audio_video()
    
    print("\n" + "=" * 50)
    print("SUMMARY:")
    
    if test_video:
        print(f"✅ Test video: {test_video}")
    if simple_video:
        print(f"✅ Simple video: {simple_video}")
        
    if test_video or simple_video:
        print("\n🎉 Test videos created successfully!")
        print("\nNow you can test the video player with these files:")
        print("1. Run the main application: python3 gui/sphere_3d.py")
        print("2. Go to Screens → Add Video Screen")
        print("3. Select one of the created test videos")
        print("4. You should hear audio when the video plays")
        
        if simple_video:
            print(f"\n🔊 Try the simple video first: {os.path.basename(simple_video)}")
            print("   It has a clear 800Hz beep that should be easy to hear")
    else:
        print("❌ Failed to create test videos")
        print("You may need to install FFmpeg or check your FFmpeg installation")

if __name__ == "__main__":
    main()
