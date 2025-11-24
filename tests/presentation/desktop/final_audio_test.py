#!/usr/bin/env python3
"""
Final audio test - play both system audio and pygame simultaneously
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
import subprocess
import threading
import time
import tempfile
import os

def play_system_audio():
    """Play system audio while pygame is playing"""
    time.sleep(1)  # Wait 1 second
    print("🔊 SYSTEM: Playing system sound...")
    subprocess.run(['say', 'pygame audio should be playing now'])
    time.sleep(1)
    subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'])

def main():
    print("🎵 FINAL AUDIO TEST")
    print("=" * 30)
    print("This test will play:")
    print("1. Pygame audio (loud beep)")
    print("2. System voice announcement")
    print("3. System ping sound")
    print("All at the same time!")
    print()
    
    # Initialize pygame
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    
    # Extract audio from loud beep video
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp:
        temp_path = temp.name
    
    result = subprocess.run([
        'ffmpeg', '-i', '/Users/tombrumbaugh/Desktop/loud_beep_test.mp4',
        '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y',
        temp_path
    ], capture_output=True)
    
    if result.returncode != 0:
        print("❌ Failed to extract audio")
        return
    
    # Start system audio thread
    system_thread = threading.Thread(target=play_system_audio)
    system_thread.start()
    
    # Play pygame audio
    print("🎮 PYGAME: Starting loud 1000Hz beep...")
    pygame.mixer.music.load(temp_path)
    pygame.mixer.music.set_volume(1.0)
    pygame.mixer.music.play()
    
    # Monitor for 5 seconds
    start_time = time.time()
    while pygame.mixer.music.get_busy() or (time.time() - start_time) < 5:
        elapsed = time.time() - start_time
        pygame_status = "PLAYING" if pygame.mixer.music.get_busy() else "STOPPED"
        print(f"⏱️  {elapsed:.1f}s - Pygame: {pygame_status}")
        time.sleep(0.5)
    
    system_thread.join()
    
    print("\n" + "=" * 50)
    print("TEST RESULTS:")
    print("🔊 Did you hear the system voice say 'pygame audio should be playing now'?")
    print("🔔 Did you hear the system ping sound?")
    print("🎵 Did you hear the 1000Hz beep from pygame?")
    print()
    print("If you heard the voice and ping but NOT the beep:")
    print("→ Pygame audio is going to a different output device")
    print("→ Check your audio output settings in System Preferences")
    print()
    print("If you heard NOTHING:")
    print("→ Check if your speakers/headphones are connected")
    print("→ Check system volume")
    print("→ Check if audio is muted")
    
    # Cleanup
    os.unlink(temp_path)

if __name__ == "__main__":
    main()
