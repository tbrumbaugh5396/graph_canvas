#!/usr/bin/env python3
"""
Test the exact workflow that happens in the main application
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

def test_exact_video_workflow():
    """Test the exact same workflow as the main application"""
    
    # Import the exact classes used in the main app
    from graph_canvas.presentation.desktop.gui.sphere_3d import MediaScreen, MediaType, ScreenType
    
    video_path = "/Users/tombrumbaugh/Desktop/loud_beep_test.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print("🎬 Testing EXACT main application workflow")
    print("=" * 50)
    
    # Step 1: Create MediaScreen exactly like the main app
    print("📱 Creating MediaScreen...")
    media_screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.VIDEO)
    media_screen.name = f"Video Screen ({os.path.basename(video_path)})"
    media_screen.set_position(1, 0, 1)
    media_screen.set_size(2.0, 1.5)
    media_screen.camera_id = None
    
    print(f"✅ MediaScreen created: {media_screen.name}")
    
    # Step 2: Load media exactly like the main app
    print("📁 Loading media...")
    load_success = media_screen.load_media(video_path)
    
    if not load_success:
        print("❌ Media loading failed")
        return False
    
    print("✅ Media loaded successfully")
    
    # Step 3: Check audio file status
    if hasattr(media_screen, 'audio_file') and media_screen.audio_file:
        if os.path.exists(media_screen.audio_file):
            size = os.path.getsize(media_screen.audio_file)
            print(f"📄 Audio file: {media_screen.audio_file}")
            print(f"📊 Audio file size: {size} bytes")
        else:
            print("❌ Audio file path exists but file doesn't exist")
            return False
    else:
        print("❌ No audio_file attribute or it's None")
        print(f"Available attributes: {[attr for attr in dir(media_screen) if 'audio' in attr.lower()]}")
        return False
    
    # Step 4: Start video playback exactly like the main app
    print("▶️  Starting video playback...")
    media_screen.start_video_playback()
    
    # Step 5: Monitor for 5 seconds
    print("⏳ Monitoring for 5 seconds...")
    for i in range(50):  # 5 seconds at 0.1s intervals
        time.sleep(0.1)
        
        # Check if video is playing
        if hasattr(media_screen, 'video_playing'):
            video_status = media_screen.video_playing
        else:
            video_status = "unknown"
            
        # Check audio status
        if hasattr(media_screen, 'audio_start_time') and media_screen.audio_start_time:
            audio_elapsed = time.time() - media_screen.audio_start_time
            audio_status = f"playing {audio_elapsed:.1f}s"
        else:
            audio_status = "not started"
        
        # Check pygame status
        try:
            import pygame
            if pygame.mixer.get_init():
                music_busy = pygame.mixer.music.get_busy()
                pygame_status = f"mixer ready, music: {music_busy}"
            else:
                pygame_status = "mixer not initialized"
        except:
            pygame_status = "pygame error"
        
        if i % 10 == 0:  # Print every second
            print(f"  {i//10 + 1}s - Video: {video_status}, Audio: {audio_status}, Pygame: {pygame_status}")
    
    # Step 6: Stop playback
    print("⏹️ Stopping playback...")
    media_screen.stop_video_playback()
    
    return True

def main():
    print("Exact Main Application Workflow Test")
    print("=" * 40)
    
    try:
        success = test_exact_video_workflow()
        
        if success:
            print("\n🎉 Workflow test completed")
        else:
            print("\n💥 Workflow test failed")
            
    except Exception as e:
        print(f"\n❌ Workflow test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
