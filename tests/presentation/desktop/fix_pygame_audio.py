#!/usr/bin/env python3
"""
Fix pygame audio routing issue
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import pygame
import os
import subprocess

def fix_pygame_audio():
    """Try to fix pygame audio routing"""
    
    print("🔧 Attempting to fix pygame audio routing...")
    
    # Method 1: Set SDL audio driver explicitly
    print("Method 1: Setting SDL audio driver...")
    os.environ['SDL_AUDIODRIVER'] = 'coreaudio'
    
    # Method 2: Initialize with different buffer sizes
    print("Method 2: Testing different buffer sizes...")
    
    buffer_sizes = [512, 1024, 2048, 4096]
    
    for buffer_size in buffer_sizes:
        try:
            pygame.mixer.quit()
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=buffer_size)
            pygame.mixer.init()
            
            print(f"✅ Buffer size {buffer_size}: {pygame.mixer.get_init()}")
            
            # Test with a simple beep
            import numpy as np
            import time
            
            # Generate 0.5 second beep
            sample_rate = 44100
            duration = 0.5
            frequency = 1000
            
            frames = int(duration * sample_rate)
            arr = np.zeros((frames, 2))
            
            for i in range(frames):
                wave = np.sin(2 * np.pi * frequency * i / sample_rate)
                arr[i][0] = wave * 0.8  # Louder
                arr[i][1] = wave * 0.8
            
            sound_array = (arr * 32767).astype(np.int16)
            sound = pygame.sndarray.make_sound(sound_array)
            
            print(f"🎵 Testing buffer size {buffer_size} - playing beep...")
            channel = pygame.mixer.Channel(0)
            channel.play(sound)
            
            while channel.get_busy():
                time.sleep(0.1)
                
            print(f"   Did you hear the beep with buffer size {buffer_size}?")
            
        except Exception as e:
            print(f"❌ Buffer size {buffer_size} failed: {e}")
    
    # Method 3: Check available audio devices
    print("\nMethod 3: Checking available audio devices...")
    try:
        # Use system_profiler to list audio devices
        result = subprocess.run(['system_profiler', 'SPAudioDataType'], 
                              capture_output=True, text=True, timeout=10)
        
        if "Built-in Output" in result.stdout:
            print("✅ Built-in Output detected")
        if "Headphones" in result.stdout:
            print("✅ Headphones detected")
            
    except Exception as e:
        print(f"Could not check audio devices: {e}")

if __name__ == "__main__":
    fix_pygame_audio()
