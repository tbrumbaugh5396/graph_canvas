#!/usr/bin/env python3

"""
Test audio extraction from video to confirm the fix works.
This tests the specific audio extraction functionality.
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
import subprocess
import tempfile

def test_audio_extraction(video_file):
    """Test audio extraction from a video file."""
    print(f"🎬 Testing audio extraction from: {video_file}")
    
    if not os.path.exists(video_file):
        print(f"❌ Video file not found: {video_file}")
        return False
    
    try:
        # Create temporary audio file
        audio_temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        audio_file = audio_temp_file.name
        audio_temp_file.close()
        
        print(f"📁 Extracting audio to: {audio_file}")
        
        # First check if video has audio streams
        print("🔍 Checking for audio streams...")
        probe_result = subprocess.run([
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', video_file
        ], capture_output=True, text=True, timeout=10)
        
        if probe_result.returncode == 0:
            import json
            data = json.loads(probe_result.stdout)
            
            audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
            
            if not audio_streams:
                print("⚠️  No audio streams found in video")
                return False
            
            print(f"✅ Found {len(audio_streams)} audio stream(s)")
            
            # Extract audio using FFmpeg
            print("🎵 Extracting audio...")
            result = subprocess.run([
                'ffmpeg', '-i', video_file, '-vn', '-acodec', 'pcm_s16le',
                '-ar', '44100', '-ac', '2', '-y', audio_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(audio_file):
                audio_size = os.path.getsize(audio_file)
                if audio_size > 0:
                    print(f"✅ Audio extraction successful - {audio_size} bytes")
                    print(f"🎵 Audio file created: {audio_file}")
                    
                    # Test if we can load it with pygame
                    try:
                        import pygame
                        pygame.mixer.init()
                        sound = pygame.mixer.Sound(audio_file)
                        print(f"✅ Audio file can be loaded by pygame")
                        pygame.mixer.quit()
                        return True
                    except Exception as e:
                        print(f"⚠️  Audio file created but pygame can't load it: {e}")
                        return False
                else:
                    print(f"❌ Audio extraction produced empty file")
                    return False
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                print(f"❌ Audio extraction failed: {error_msg}")
                return False
        else:
            print(f"❌ Failed to probe video file")
            return False
            
    except Exception as e:
        print(f"❌ Exception during audio extraction: {e}")
        return False
    finally:
        # Clean up
        if 'audio_file' in locals() and os.path.exists(audio_file):
            os.unlink(audio_file)
            print(f"🧹 Cleaned up temporary audio file")

if __name__ == "__main__":
    print("🎯 Audio Extraction Test")
    print("=" * 40)
    
    # Test with the sync test video
    test_video = "sync_test_video.mp4"
    
    if os.path.exists(test_video):
        success = test_audio_extraction(test_video)
        if success:
            print("\n✅ AUDIO EXTRACTION TEST PASSED!")
            print("🎬 The audio extraction fix should work in the main application")
        else:
            print("\n❌ AUDIO EXTRACTION TEST FAILED!")
            print("🔧 The audio system needs more debugging")
    else:
        print(f"❌ Test video not found: {test_video}")
        print("💡 Run 'python3 create_test_video_with_beep.py' first to create a test video")
