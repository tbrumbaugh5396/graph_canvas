#!/usr/bin/env python3
"""
Debug the specific audio issue in the main application
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
import time

# Add the project directory to Python path
sys.path.insert(0, '/Users/tombrumbaugh/Desktop/Dependency-Chart')

def test_media_screen_audio():
    """Test the MediaScreen audio functionality directly"""
    
    # Import after setting path
    from graph_canvas.presentation.desktop.gui.sphere_3d import MediaScreen, MediaType, ScreenType
    
    video_path = "/Users/tombrumbaugh/Desktop/simple_audio_test.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Test video not found: {video_path}")
        return False
    
    print("🎥 Testing MediaScreen audio functionality directly")
    print("=" * 50)
    
    # Create media screen
    screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.VIDEO)
    screen.name = "Test Audio Screen"
    
    print("📁 Loading video...")
    if not screen.load_media(video_path):
        print("❌ Failed to load video")
        return False
    
    print("✅ Video loaded successfully")
    
    # Check if audio file was created
    if hasattr(screen, 'audio_file') and screen.audio_file:
        print(f"📄 Audio file: {screen.audio_file}")
        if os.path.exists(screen.audio_file):
            size = os.path.getsize(screen.audio_file)
            print(f"📊 Audio file size: {size} bytes")
        else:
            print("❌ Audio file doesn't exist")
            return False
    else:
        print("❌ No audio file created")
        return False
    
    print("\n🎵 Starting video playback...")
    screen.start_video_playback()
    
    print("⏳ Waiting 5 seconds for audio...")
    for i in range(5):
        time.sleep(1)
        
        # Check audio status
        import pygame
        music_busy = pygame.mixer.music.get_busy() if pygame.mixer.get_init() else False
        channel_busy = screen.audio_channel.get_busy() if hasattr(screen, 'audio_channel') and screen.audio_channel else False
        
        print(f"  {i+1}/5 - Music: {music_busy}, Channel: {channel_busy}, Video: {screen.video_playing}")
    
    print("\n⏹️ Stopping playback...")
    screen.stop_video_playback()
    
    return True

def check_audio_permissions():
    """Check macOS audio permissions"""
    print("\n🔒 Checking macOS audio permissions...")
    
    try:
        import subprocess
        
        # Try to play a system sound
        result = subprocess.run(['afplay', '/System/Library/Sounds/Ping.aiff'], 
                              capture_output=True, timeout=3)
        
        if result.returncode == 0:
            print("✅ System audio works (afplay)")
        else:
            print("❌ System audio failed (afplay)")
            
    except Exception as e:
        print(f"❌ Audio permission test failed: {e}")

def check_pygame_mixer_state():
    """Check pygame mixer state"""
    print("\n🎮 Checking pygame mixer state...")
    
    try:
        import pygame
        
        # Check if mixer is initialized
        mixer_init = pygame.mixer.get_init()
        print(f"Mixer initialized: {mixer_init}")
        
        if mixer_init:
            print(f"Mixer settings: {mixer_init}")
            
            # Check number of channels
            num_channels = pygame.mixer.get_num_channels()
            print(f"Number of channels: {num_channels}")
            
            # Check if music is busy
            music_busy = pygame.mixer.music.get_busy()
            print(f"Music busy: {music_busy}")
            
        else:
            print("Pygame mixer not initialized")
            
    except Exception as e:
        print(f"❌ Pygame mixer check failed: {e}")

def main():
    print("Audio Issue Debug Tool")
    print("=" * 30)
    
    # Check system audio
    check_audio_permissions()
    
    # Check pygame state
    check_pygame_mixer_state()
    
    # Test MediaScreen audio
    try:
        success = test_media_screen_audio()
        
        if success:
            print("\n🎉 MediaScreen audio test completed")
        else:
            print("\n💥 MediaScreen audio test failed")
            
    except Exception as e:
        print(f"\n❌ MediaScreen test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
