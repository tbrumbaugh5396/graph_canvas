#!/usr/bin/env python3
"""
Debug script to test video and audio functionality
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import os
import sys
import subprocess
import json
import tempfile

def test_ffmpeg():
    """Test FFmpeg functionality"""
    print("=== Testing FFmpeg ===")
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg is available")
            print(f"Version: {result.stdout.split()[2]}")
        else:
            print("❌ FFmpeg failed")
            print(f"Error: {result.stderr}")
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
    print()

def test_pygame_audio():
    """Test pygame audio functionality"""
    print("=== Testing Pygame Audio ===")
    try:
        import pygame
        print(f"✅ Pygame imported - version: {pygame.version.ver}")
        
        # Test mixer initialization
        pygame.mixer.quit()  # Clean slate
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
        pygame.mixer.init()
        
        mixer_info = pygame.mixer.get_init()
        if mixer_info:
            print(f"✅ Pygame mixer initialized: {mixer_info}")
        else:
            print("❌ Pygame mixer failed to initialize")
            
    except Exception as e:
        print(f"❌ Pygame audio test failed: {e}")
    print()

def test_opencv_video():
    """Test OpenCV video functionality"""
    print("=== Testing OpenCV Video ===")
    try:
        import cv2
        print(f"✅ OpenCV imported - version: {cv2.__version__}")
        
        # Test video capture creation (no file needed)
        cap = cv2.VideoCapture()
        if cap is not None:
            print("✅ VideoCapture object created")
            cap.release()
        else:
            print("❌ VideoCapture creation failed")
            
    except Exception as e:
        print(f"❌ OpenCV video test failed: {e}")
    print()

def test_video_file_processing(video_path=None):
    """Test processing a video file if provided"""
    if not video_path or not os.path.exists(video_path):
        print("=== Video File Test ===")
        print("No video file provided or file doesn't exist")
        print("To test with a video file, provide path as argument")
        print()
        return
        
    print(f"=== Testing Video File: {video_path} ===")
    
    # Test FFprobe
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            print("✅ FFprobe successful")
            
            # Check for video and audio streams
            video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            
            print(f"Video streams: {len(video_streams)}")
            print(f"Audio streams: {len(audio_streams)}")
            
            if video_streams:
                vs = video_streams[0]
                print(f"Video: {vs.get('codec_name', 'unknown')} {vs.get('width', '?')}x{vs.get('height', '?')}")
                fps = vs.get('r_frame_rate', '?/1')
                print(f"FPS: {fps}")
                
            if audio_streams:
                aus = audio_streams[0]
                print(f"Audio: {aus.get('codec_name', 'unknown')} {aus.get('sample_rate', '?')}Hz")
            else:
                print("⚠️  No audio streams found in video")
                
        else:
            print(f"❌ FFprobe failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Video file test failed: {e}")
    
    # Test audio extraction
    try:
        print("\nTesting audio extraction...")
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            temp_path = temp_audio.name
            
        result = subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y',
            temp_path
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0 and os.path.exists(temp_path):
            size = os.path.getsize(temp_path)
            print(f"✅ Audio extraction successful - {size} bytes")
            os.unlink(temp_path)  # Clean up
        else:
            print(f"❌ Audio extraction failed: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Audio extraction test failed: {e}")
    
    print()

def main():
    print("Video and Audio Debug Test")
    print("=" * 40)
    
    test_ffmpeg()
    test_pygame_audio()
    test_opencv_video()
    
    # Check if video file path provided
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
        test_video_file_processing(video_path)
    else:
        test_video_file_processing()
    
    print("Debug test completed.")
    print("\nIf all tests pass but you still have issues:")
    print("1. Check system audio volume/mute")
    print("2. Try with a different video file")
    print("3. Check macOS audio permissions")
    print("4. Verify video file has audio track")

if __name__ == "__main__":
    main()
