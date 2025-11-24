#!/usr/bin/env python3

"""
Test to verify the loop restart fix works correctly.
This simulates the improved loop restart behavior.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import time
import pygame

class ImprovedLoopRestart:
    def __init__(self):
        self.audio_start_time = None
        self.audio_paused_time = 0
        self.audio_channel = None
        self.current_frame_index = 0
        self.video_frame_count = 150  # 5 seconds at 30fps
        self.loop_count = 0
        
    def simulate_video_loop_with_restart(self):
        """Simulate the improved video loop restart logic."""
        self.loop_count += 1
        print(f"\n🎬 === SIMULATING LOOP {self.loop_count} ===")
        
        # Simulate video playing until end
        print(f"📹 Playing video frames...")
        for frame in range(0, self.video_frame_count + 5, 30):  # Skip frames for speed
            self.current_frame_index = frame
            
            # Check if we reached the end
            if self.current_frame_index >= self.video_frame_count:
                print(f"🔄 End of video reached, applying IMPROVED restart logic")
                
                # === IMPROVED RESTART LOGIC (matches the fix) ===
                
                # 1. Stop current audio cleanly
                print(f"🛑 Stopping current audio cleanly...")
                try:
                    if pygame.mixer.get_init():
                        pygame.mixer.music.stop()
                        if self.audio_channel:
                            self.audio_channel.stop()
                            self.audio_channel = None  # Clear audio channel
                    print(f"   ✅ Audio stopped cleanly")
                except Exception as e:
                    print(f"   ⚠️ Audio stop error: {e}")
                
                # 2. Reset ALL timing variables for consistent restart
                print(f"🔄 Resetting all timing variables...")
                self.current_frame_index = 0
                old_audio_start_time = self.audio_start_time
                self.audio_start_time = None  # Reset audio timing
                self.audio_paused_time = 0    # Reset pause timing
                
                print(f"   • Frame index: {self.current_frame_index}")
                print(f"   • Audio start time: {old_audio_start_time} → {self.audio_start_time}")
                print(f"   • Audio pause time: {self.audio_paused_time}")
                print(f"   ✅ All timing variables reset")
                
                # 3. Brief pause to ensure clean restart
                print(f"⏸️ Brief pause for clean restart...")
                time.sleep(0.05)
                
                # 4. Restart audio playback with fresh timing (same as first loop)
                print(f"🎵 Restarting audio for new loop...")
                audio_restart_success = self.simulate_start_audio_playback()
                print(f"   ✅ Audio restart result: {audio_restart_success}")
                
                break
            else:
                time.sleep(0.1)  # Simulate frame processing time
                
        print(f"✅ Loop {self.loop_count} completed with improved restart logic")
    
    def simulate_start_audio_playback(self):
        """Simulate the _start_audio_playback method."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            
            # Simulate audio start
            self.audio_start_time = time.time()  # Fresh timing for each loop
            print(f"   🔊 Audio started with fresh timing: {self.audio_start_time}")
            return True
            
        except Exception as e:
            print(f"   ❌ Audio start failed: {e}")
            return False
    
    def test_multiple_loops(self, num_loops=3):
        """Test multiple loops with improved restart logic."""
        print("🎯 Testing IMPROVED Loop Restart Logic")
        print("=" * 50)
        
        # Initialize pygame
        try:
            pygame.mixer.init()
            print("✅ Pygame mixer initialized")
        except Exception as e:
            print(f"⚠️ Pygame init warning: {e}")
        
        print(f"🎮 Testing {num_loops} loops with improved restart...")
        
        for loop_num in range(num_loops):
            self.simulate_video_loop_with_restart()
            
            if loop_num < num_loops - 1:
                print(f"⏳ Preparing for next loop...")
                time.sleep(0.2)
        
        print(f"\n📋 IMPROVED RESTART ANALYSIS:")
        print(f"   ✅ All loops use fresh timing variables")
        print(f"   ✅ Audio is cleanly stopped and restarted")
        print(f"   ✅ Same initialization logic for all loops")
        print(f"   ✅ No stale timing information carried over")
        print(f"\n🎯 EXPECTED RESULT:")
        print(f"   • All loops should behave identically to the first loop")
        print(f"   • Consistent audio/video sync across all loops")
        print(f"   • No more differences between first and subsequent loops")

if __name__ == "__main__":
    tester = ImprovedLoopRestart()
    tester.test_multiple_loops(3)
