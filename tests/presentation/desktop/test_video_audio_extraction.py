#!/usr/bin/env python3
"""
Test video audio extraction specifically
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
import json
import os
import sys
import tempfile
import pygame

def test_video_file(video_path):
    """Test a specific video file for audio extraction"""
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print(f"🎥 Testing video file: {video_path}")
    print(f"📊 File size: {os.path.getsize(video_path)} bytes")
    
    # Test 1: Check video streams with ffprobe
    print("\n=== Step 1: Analyzing video streams ===")
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_format', '-show_streams', video_path
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            data = json.loads(result.stdout)
            
            # Check streams
            video_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'video']
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            
            print(f"✅ FFprobe successful")
            print(f"📹 Video streams: {len(video_streams)}")
            print(f"🔊 Audio streams: {len(audio_streams)}")
            
            if video_streams:
                vs = video_streams[0]
                print(f"   Video: {vs.get('codec_name', 'unknown')} {vs.get('width', '?')}x{vs.get('height', '?')}")
                
            if audio_streams:
                aus = audio_streams[0]
                print(f"   Audio: {aus.get('codec_name', 'unknown')} {aus.get('sample_rate', '?')}Hz {aus.get('channels', '?')} channels")
                
                # Get duration
                duration = float(data.get('format', {}).get('duration', 0))
                print(f"   Duration: {duration:.2f} seconds")
                
                if len(audio_streams) == 0:
                    print("❌ NO AUDIO STREAMS FOUND - This video has no audio!")
                    return False
                    
            else:
                print("❌ NO AUDIO STREAMS - This video has no audio track!")
                return False
                
        else:
            print(f"❌ FFprobe failed: {result.stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"❌ FFprobe error: {e}")
        return False
    
    # Test 2: Extract audio
    print("\n=== Step 2: Testing audio extraction ===")
    try:
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_audio:
            audio_file = temp_audio.name
        
        print(f"📁 Extracting audio to: {audio_file}")
        
        result = subprocess.run([
            'ffmpeg', '-i', video_path,
            '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y',
            '-loglevel', 'error',
            audio_file
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0 and os.path.exists(audio_file):
            audio_size = os.path.getsize(audio_file)
            print(f"✅ Audio extraction successful - {audio_size} bytes")
            
            if audio_size == 0:
                print("❌ Extracted audio file is empty!")
                os.unlink(audio_file)
                return False
                
        else:
            error_msg = result.stderr if result.stderr else "Unknown error"
            print(f"❌ Audio extraction failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Audio extraction error: {e}")
        return False
    
    # Test 3: Test pygame with extracted audio
    print("\n=== Step 3: Testing pygame with extracted audio ===")
    try:
        # Initialize pygame
        pygame.mixer.quit()
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        print("✅ Pygame mixer initialized")
        
        # Test loading the audio file
        sound = pygame.mixer.Sound(audio_file)
        duration = sound.get_length()
        print(f"✅ Audio file loaded - duration: {duration:.2f}s")
        
        if duration <= 0:
            print("❌ Invalid audio duration!")
            os.unlink(audio_file)
            return False
        
        # Test playback
        print("🎵 Playing extracted audio for 3 seconds...")
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play()
        
        import time
        start_time = time.time()
        while pygame.mixer.music.get_busy() and (time.time() - start_time) < 3:
            time.sleep(0.1)
            
        pygame.mixer.music.stop()
        print("✅ Audio playback test completed")
        
        # Clean up
        os.unlink(audio_file)
        return True
        
    except Exception as e:
        print(f"❌ Pygame audio test failed: {e}")
        if os.path.exists(audio_file):
            os.unlink(audio_file)
        return False

def find_test_videos():
    """Look for video files to test with"""
    print("🔍 Looking for video files to test...")
    
    # Common video locations
    test_paths = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/Movies"),
        "/Users/tombrumbaugh/Desktop/Dependency-Chart"
    ]
    
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.m4v']
    found_videos = []
    
    for path in test_paths:
        if os.path.exists(path):
            try:
                for file in os.listdir(path):
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        full_path = os.path.join(path, file)
                        if os.path.getsize(full_path) > 1024:  # At least 1KB
                            found_videos.append(full_path)
            except PermissionError:
                continue
    
    return found_videos[:5]  # Return first 5 found

def main():
    print("Video Audio Extraction Test")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # Test specific file provided
        video_path = sys.argv[1]
        success = test_video_file(video_path)
        
        if success:
            print("\n🎉 Video audio extraction test PASSED!")
            print("The issue might be in the main application's audio synchronization.")
        else:
            print("\n💥 Video audio extraction test FAILED!")
            print("This video file has issues with audio extraction.")
    else:
        # Look for video files to test
        videos = find_test_videos()
        
        if not videos:
            print("No video files found to test.")
            print("\nUsage: python3 test_video_audio_extraction.py <video_file_path>")
            print("\nOr place a video file in:")
            print("  - ~/Desktop")
            print("  - ~/Downloads") 
            print("  - ~/Movies")
            return
        
        print(f"Found {len(videos)} video file(s) to test:")
        for i, video in enumerate(videos):
            print(f"  {i+1}. {os.path.basename(video)}")
        
        print(f"\nTesting first video: {videos[0]}")
        success = test_video_file(videos[0])
        
        if not success and len(videos) > 1:
            print(f"\nTrying second video: {videos[1]}")
            success = test_video_file(videos[1])

if __name__ == "__main__":
    main()
