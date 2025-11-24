#!/usr/bin/env python3
"""
Simple test to verify video display with audio sync works
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
import subprocess
import time
import numpy as np

def test_ffmpeg_frame_extraction():
    """Test if FFmpeg can extract frames properly"""
    video_path = "sync_test_video.mp4"
    
    if not os.path.exists(video_path):
        print("❌ Test video not found")
        return False
    
    print("🎬 Testing FFmpeg frame extraction...")
    
    # Test extracting frame 0
    ffmpeg_cmd = [
        'ffmpeg', '-ss', '0.0', '-i', video_path,
        '-vframes', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', '768x432',
        '-an', '-loglevel', 'error', '-'
    ]
    
    try:
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, timeout=10)
        
        expected_size = 768 * 432 * 3
        actual_size = len(result.stdout)
        
        print(f"📊 FFmpeg result:")
        print(f"   Return code: {result.returncode}")
        print(f"   Output size: {actual_size} bytes")
        print(f"   Expected size: {expected_size} bytes")
        print(f"   Size match: {actual_size == expected_size}")
        
        if result.returncode == 0 and actual_size == expected_size:
            print("✅ FFmpeg frame extraction works!")
            
            # Test numpy conversion
            frame = np.frombuffer(result.stdout, dtype=np.uint8)
            frame = frame.reshape((432, 768, 3))
            frame = np.flipud(frame)
            
            print(f"✅ Numpy conversion works! Frame shape: {frame.shape}")
            return True
        else:
            print("❌ FFmpeg frame extraction failed")
            if result.stderr:
                print(f"   Error: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during FFmpeg test: {e}")
        return False

def test_audio_extraction():
    """Test if audio extraction works"""
    video_path = "sync_test_video.mp4"
    audio_path = "temp_audio_test.wav"
    
    if not os.path.exists(video_path):
        print("❌ Test video not found")
        return False
    
    print("🔊 Testing audio extraction...")
    
    # Extract audio
    ffmpeg_cmd = [
        'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
        '-ar', '44100', '-ac', '2', '-y', audio_path
    ]
    
    try:
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, 
                              stderr=subprocess.PIPE, timeout=10)
        
        if result.returncode == 0 and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
            print(f"✅ Audio extraction works! File size: {file_size} bytes")
            
            # Clean up
            os.remove(audio_path)
            return True
        else:
            print("❌ Audio extraction failed")
            if result.stderr:
                print(f"   Error: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ Exception during audio test: {e}")
        return False

def main():
    print("🧪 Testing Video Display Components")
    print("=" * 50)
    
    frame_test = test_ffmpeg_frame_extraction()
    audio_test = test_audio_extraction()
    
    print("\n📋 Test Results:")
    print(f"   Frame extraction: {'✅ PASS' if frame_test else '❌ FAIL'}")
    print(f"   Audio extraction: {'✅ PASS' if audio_test else '❌ FAIL'}")
    
    if frame_test and audio_test:
        print("\n🎉 All components working! Video display should work.")
        print("\n💡 To test in the main app:")
        print("   1. Start the application")
        print("   2. Go to Screens > Add Video Screen")
        print("   3. Select your video file")
        print("   4. You should see video with synchronized audio")
    else:
        print("\n⚠️  Some components failed. Video display may not work properly.")

if __name__ == "__main__":
    main()
