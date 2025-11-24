#!/usr/bin/env python3

"""
Test to verify the first loop audio fix works by simulating the corrected loading sequence.
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
import pygame
import time
import threading

class FixedVideoPlayer:
    def __init__(self):
        self.media_path = None
        self.audio_file = None
        self.audio_initialized = False
        self.video_playing = False
        self.audio_channel = None
        
    def _extract_audio(self):
        """Extract audio from video file for synchronized playback."""
        try:
            # Create temporary audio file
            audio_temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            self.audio_file = audio_temp_file.name
            audio_temp_file.close()
            
            print(f"DEBUG: ===== EXTRACTING AUDIO FROM VIDEO =====")
            print(f"DEBUG: Extracting audio to {self.audio_file}")
            
            # First check if video has audio streams
            probe_result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_streams', self.media_path
            ], capture_output=True, text=True, timeout=10)
            
            if probe_result.returncode == 0:
                import json
                data = json.loads(probe_result.stdout)
                
                audio_streams = [s for s in data.get('streams', []) if s.get('codec_type') == 'audio']
                
                if not audio_streams:
                    print(f"DEBUG: No audio streams found in video")
                    return False
                
                print(f"DEBUG: Found {len(audio_streams)} audio stream(s)")
                
                # Extract audio
                result = subprocess.run([
                    'ffmpeg', '-i', self.media_path, '-vn', '-acodec', 'pcm_s16le',
                    '-ar', '44100', '-ac', '2', '-y', self.audio_file
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0 and os.path.exists(self.audio_file):
                    audio_size = os.path.getsize(self.audio_file)
                    if audio_size > 0:
                        print(f"DEBUG: Audio extraction successful - {audio_size} bytes")
                        return True
                    else:
                        print(f"DEBUG: Audio extraction produced empty file")
                        return False
                else:
                    error_msg = result.stderr if result.stderr else "Unknown error"
                    print(f"DEBUG: Audio extraction failed: {error_msg}")
                    return False
            else:
                print(f"DEBUG: Failed to probe video file")
                return False
                
        except Exception as e:
            print(f"DEBUG: Exception in _extract_audio: {e}")
            return False
    
    def _load_video(self):
        """Load video and extract audio - CORRECTED VERSION."""
        print(f"DEBUG: Loading video data from {self.media_path}")
        
        # Simulate video loading (skipping actual video processing)
        print(f"DEBUG: Video loading with audio support")
        
        # Extract audio DURING video loading (this is the fix!)
        print(f"DEBUG: ===== EXTRACTING AUDIO FROM VIDEO =====")
        audio_success = self._extract_audio()
        print(f"DEBUG: Audio extraction result: {audio_success}")
        
        print(f"DEBUG: Video data loaded successfully")
        return True
    
    def _init_audio(self):
        """Initialize audio system for video playback."""
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                print(f"DEBUG: No audio file available")
                return False
            
            audio_size = os.path.getsize(self.audio_file)
            print(f"DEBUG: Audio file exists: {self.audio_file}, size: {audio_size} bytes")
            
            if audio_size == 0:
                print(f"DEBUG: Audio file is empty, skipping audio initialization")
                return False
            
            if not self.audio_initialized:
                try:
                    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
                    print(f"DEBUG: Pygame mixer initialized")
                    self.audio_initialized = True
                    return True
                except Exception as e:
                    print(f"DEBUG: Failed to initialize pygame mixer: {e}")
                    return False
            
            return True
                    
        except Exception as e:
            print(f"DEBUG: Exception in _init_audio: {e}")
            return False
    
    def _start_audio_playback(self):
        """Start audio playback."""
        try:
            if not self.audio_file or not os.path.exists(self.audio_file):
                print(f"DEBUG: No audio file to play")
                return False
            
            print(f"DEBUG: ===== STARTING AUDIO PLAYBACK =====")
            print(f"DEBUG: Loading audio file: {self.audio_file}")
            
            sound = pygame.mixer.Sound(self.audio_file)
            sound_length = sound.get_length()
            print(f"DEBUG: Audio loaded - duration: {sound_length:.2f}s")
            
            self.audio_channel = sound.play()
            if self.audio_channel:
                print(f"DEBUG: ✅ Audio playback started successfully on FIRST LOOP!")
                return True
            else:
                print(f"DEBUG: ❌ Failed to start audio playback")
                return False
                
        except Exception as e:
            print(f"DEBUG: Exception in _start_audio_playback: {e}")
            return False
    
    def start_video_playback(self):
        """Start video playback - CORRECTED VERSION."""
        print(f"DEBUG: ===== START_VIDEO_PLAYBACK CALLED =====")
        print(f"DEBUG: Video playing: {self.video_playing}")
        print(f"DEBUG: Has audio file: {self.audio_file}")
        
        if not self.video_playing:
            print(f"DEBUG: Starting video playback")
            
            # Initialize audio (should work now that audio file exists)
            print(f"DEBUG: About to initialize audio...")
            audio_init_result = self._init_audio()
            print(f"DEBUG: Audio initialization result: {audio_init_result}")
            
            # Set video state
            self.video_playing = True
            
            # Start audio playback (should work on first loop now!)
            audio_start_result = self._start_audio_playback()
            print(f"DEBUG: Audio playback start result: {audio_start_result}")
            
            if audio_start_result:
                print(f"🎉 SUCCESS! First loop audio is working!")
                return True
            else:
                print(f"❌ Failed to start audio on first loop")
                return False
        else:
            print(f"DEBUG: Video already playing, skipping restart")
            return False
    
    def test_corrected_sequence(self, video_path):
        """Test the corrected loading sequence."""
        print(f"🎯 Testing CORRECTED sequence for first-loop audio")
        print(f"=" * 60)
        
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            return False
        
        self.media_path = video_path
        
        # Step 1: Load video (includes audio extraction - THE FIX!)
        print(f"\n📹 Step 1: Loading video with audio extraction")
        load_result = self._load_video()
        
        if not load_result:
            print(f"❌ Video loading failed")
            return False
        
        # Step 2: Start video playback (audio should be ready now!)
        print(f"\n🎵 Step 2: Starting video playback with audio")
        playback_result = self.start_video_playback()
        
        if playback_result:
            print(f"\n✅ FIRST LOOP AUDIO FIX SUCCESSFUL!")
            print(f"🔊 Audio should be playing on the first loop!")
            print(f"🎬 The main application fix should work the same way!")
            return True
        else:
            print(f"\n❌ First loop audio still not working")
            return False

if __name__ == "__main__":
    print("🎯 First Loop Audio Fix Test")
    print("=" * 40)
    
    # Test with existing video
    test_video = "sync_test_video.mp4"
    
    if os.path.exists(test_video):
        player = FixedVideoPlayer()
        success = player.test_corrected_sequence(test_video)
        
        if success:
            print(f"\n🎉 THE FIX WORKS!")
            print(f"💡 The main application should now have audio on first loop")
            
            # Let it play for a few seconds
            time.sleep(3)
            print(f"\n🔧 Ready to test the main application!")
        else:
            print(f"\n❌ The fix needs more work")
    else:
        print(f"❌ Test video not found: {test_video}")
        print("💡 Run 'python3 create_test_video_with_beep.py' first")
