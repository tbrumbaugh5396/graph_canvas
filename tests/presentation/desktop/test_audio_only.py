#!/usr/bin/env python3
"""
Test basic audio functionality to isolate the issue
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
import numpy as np
import time
import sys
import os

def test_pygame_audio_basic():
    """Test basic pygame audio with generated sound"""
    print("=== Testing Basic Pygame Audio ===")
    
    try:
        # Initialize pygame mixer
        pygame.mixer.quit()  # Clean slate
        pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
        pygame.mixer.init()
        
        print("✅ Pygame mixer initialized")
        
        # Generate a simple test tone (440Hz for 2 seconds)
        sample_rate = 44100
        duration = 2.0
        frequency = 440  # A note
        
        # Generate sine wave
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2))  # Stereo
        
        for i in range(frames):
            wave = np.sin(2 * np.pi * frequency * i / sample_rate)
            arr[i][0] = wave * 0.3  # Left channel
            arr[i][1] = wave * 0.3  # Right channel
        
        # Convert to pygame sound
        sound_array = (arr * 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(sound_array)
        
        print(f"🎵 Playing test tone (440Hz) for {duration} seconds...")
        print("   You should hear a clear musical note")
        
        # Play the sound
        channel = pygame.mixer.Channel(0)
        channel.play(sound)
        
        # Wait for it to finish
        while channel.get_busy():
            time.sleep(0.1)
            
        print("✅ Test tone completed")
        return True
        
    except Exception as e:
        print(f"❌ Basic audio test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_pygame_music():
    """Test pygame music functionality"""
    print("\n=== Testing Pygame Music Module ===")
    
    try:
        # Create a simple WAV file for testing
        import wave
        import struct
        
        # Generate test audio data
        sample_rate = 44100
        duration = 1.0
        frequency = 880  # Higher pitch
        
        frames = int(duration * sample_rate)
        
        # Create WAV file
        test_wav = "/tmp/test_audio.wav"
        with wave.open(test_wav, 'w') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            for i in range(frames):
                wave_val = int(32767 * 0.3 * np.sin(2 * np.pi * frequency * i / sample_rate))
                # Write stereo frame
                wav_file.writeframes(struct.pack('<hh', wave_val, wave_val))
        
        print(f"📁 Created test WAV file: {test_wav}")
        
        # Test pygame music
        pygame.mixer.music.load(test_wav)
        pygame.mixer.music.set_volume(1.0)
        
        print("🎵 Playing test WAV with pygame.mixer.music...")
        pygame.mixer.music.play()
        
        # Wait for playback
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
            
        print("✅ Pygame music test completed")
        
        # Clean up
        os.unlink(test_wav)
        return True
        
    except Exception as e:
        print(f"❌ Pygame music test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_system_audio():
    """Test system audio using macOS say command"""
    print("\n=== Testing System Audio ===")
    
    try:
        import subprocess
        
        print("🔊 Testing system audio with 'say' command...")
        result = subprocess.run(['say', 'Audio test successful'], timeout=10)
        
        if result.returncode == 0:
            print("✅ System audio test completed")
            return True
        else:
            print("❌ System audio test failed")
            return False
            
    except Exception as e:
        print(f"❌ System audio test failed: {e}")
        return False

def main():
    print("Audio Troubleshooting Script")
    print("=" * 40)
    print("This will test different audio components to isolate the issue.\n")
    
    # Test system audio first
    system_ok = test_system_audio()
    
    # Test basic pygame audio
    pygame_basic_ok = test_pygame_audio_basic()
    
    # Test pygame music
    pygame_music_ok = test_pygame_music()
    
    print("\n" + "=" * 40)
    print("RESULTS:")
    print(f"System Audio (say command): {'✅ PASS' if system_ok else '❌ FAIL'}")
    print(f"Pygame Basic Audio:         {'✅ PASS' if pygame_basic_ok else '❌ FAIL'}")
    print(f"Pygame Music Module:        {'✅ PASS' if pygame_music_ok else '❌ FAIL'}")
    
    if all([system_ok, pygame_basic_ok, pygame_music_ok]):
        print("\n🎉 All audio tests passed!")
        print("The issue is likely with video audio extraction or file format.")
    else:
        print("\n💥 Some audio tests failed!")
        print("This indicates a system-level audio issue.")
        
        if not system_ok:
            print("• System audio is not working - check macOS audio settings")
        if not pygame_basic_ok:
            print("• Pygame basic audio failed - may need to reinstall pygame")
        if not pygame_music_ok:
            print("• Pygame music module failed - file format or pygame issue")

if __name__ == "__main__":
    main()
