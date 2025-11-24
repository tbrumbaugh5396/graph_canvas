#!/usr/bin/env python3

"""
Test to diagnose video loop behavior issues.
This helps understand what happens between first and subsequent loops.
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

class LoopBehaviorTest:
    def __init__(self):
        self.audio_file = None
        self.audio_channel = None
        self.loop_count = 0
        self.video_duration = 5.0  # Test video is 5 seconds
        
    def extract_audio(self, video_path):
        """Extract audio for testing."""
        try:
            audio_temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            self.audio_file = audio_temp_file.name
            audio_temp_file.close()
            
            result = subprocess.run([
                'ffmpeg', '-i', video_path, '-vn', '-acodec', 'pcm_s16le',
                '-ar', '44100', '-ac', '2', '-y', self.audio_file
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and os.path.exists(self.audio_file):
                return True
            return False
        except Exception as e:
            print(f"Audio extraction failed: {e}")
            return False
    
    def start_audio_loop(self):
        """Start audio playback for one loop."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            
            sound = pygame.mixer.Sound(self.audio_file)
            self.audio_channel = sound.play()
            
            if self.audio_channel:
                print(f"🔊 Loop {self.loop_count}: Audio started successfully")
                return True
            else:
                print(f"❌ Loop {self.loop_count}: Audio failed to start")
                return False
                
        except Exception as e:
            print(f"❌ Loop {self.loop_count}: Audio error: {e}")
            return False
    
    def stop_audio(self):
        """Stop current audio playback."""
        try:
            if self.audio_channel:
                self.audio_channel.stop()
                self.audio_channel = None
            pygame.mixer.music.stop()
            print(f"🛑 Loop {self.loop_count}: Audio stopped")
        except Exception as e:
            print(f"⚠️ Loop {self.loop_count}: Error stopping audio: {e}")
    
    def simulate_video_loop(self):
        """Simulate one complete video loop."""
        self.loop_count += 1
        print(f"\n🎬 === STARTING LOOP {self.loop_count} ===")
        
        # Start audio for this loop
        audio_started = self.start_audio_loop()
        
        if audio_started:
            # Simulate video playback duration
            print(f"⏱️ Loop {self.loop_count}: Playing for {self.video_duration} seconds...")
            
            # Check audio status during playback
            for i in range(int(self.video_duration)):
                time.sleep(1)
                if self.audio_channel:
                    playing = self.audio_channel.get_busy()
                    print(f"📊 Loop {self.loop_count}: Second {i+1} - Audio playing: {playing}")
                else:
                    print(f"📊 Loop {self.loop_count}: Second {i+1} - No audio channel")
            
            # Stop audio at end of loop
            self.stop_audio()
            
            print(f"✅ Loop {self.loop_count}: Completed")
            return True
        else:
            print(f"❌ Loop {self.loop_count}: Failed to start")
            return False
    
    def test_multiple_loops(self, num_loops=3):
        """Test multiple video loops to see behavior differences."""
        print("🎯 Testing Video Loop Behavior")
        print("=" * 50)
        
        test_video = "sync_test_video.mp4"
        
        if not os.path.exists(test_video):
            print(f"❌ Test video not found: {test_video}")
            return False
        
        # Extract audio once
        print("🔧 Extracting audio...")
        if not self.extract_audio(test_video):
            print("❌ Audio extraction failed")
            return False
        
        print(f"✅ Audio extracted successfully")
        print(f"🎵 Testing {num_loops} loops to compare behavior...\n")
        
        # Test multiple loops
        for loop_num in range(num_loops):
            success = self.simulate_video_loop()
            
            if not success:
                print(f"❌ Test failed at loop {loop_num + 1}")
                break
            
            # Brief pause between loops
            if loop_num < num_loops - 1:
                print(f"⏸️ Brief pause before next loop...")
                time.sleep(0.5)
        
        # Cleanup
        if self.audio_file and os.path.exists(self.audio_file):
            os.unlink(self.audio_file)
        
        print(f"\n📋 Analysis:")
        print(f"   • Loop 1: Should work perfectly (first loop)")
        print(f"   • Loop 2+: May show different behavior")
        print(f"   • Look for patterns in audio playback status")
        print(f"\n🔍 If loops behave differently, the issue is likely:")
        print(f"   • Audio restart timing")
        print(f"   • Audio channel management")
        print(f"   • Video/audio synchronization reset")

if __name__ == "__main__":
    tester = LoopBehaviorTest()
    tester.test_multiple_loops(3)
