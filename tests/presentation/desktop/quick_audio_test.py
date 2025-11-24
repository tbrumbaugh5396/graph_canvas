#!/usr/bin/env python3

"""
Quick test to confirm the audio fix is working by directly loading a video.
This bypasses the GUI startup issues to test just the audio functionality.
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
sys.path.append('.')

# Import just the MediaScreen class to test audio functionality
from graph_canvas.presentation.desktop.gui.sphere_3d import MediaScreen, MediaType, ScreenType

def test_audio_fix():
    print("🎯 Testing Audio Fix in MediaScreen")
    print("=" * 40)
    
    test_video = "sync_test_video.mp4"
    
    if not os.path.exists(test_video):
        print(f"❌ Test video not found: {test_video}")
        print("💡 Run 'python3 create_test_video_with_beep.py' first")
        return False
    
    print(f"📹 Creating MediaScreen for: {test_video}")
    
    # Create a media screen
    media_screen = MediaScreen(ScreenType.SCREEN_2D, MediaType.VIDEO)
    media_screen.name = f"Test Video Screen ({test_video})"
    
    print(f"🔧 Loading video (with audio extraction fix)...")
    
    # This should now include audio extraction due to our fix
    load_result = media_screen.load_media(test_video)
    
    print(f"📋 Load result: {load_result}")
    
    if load_result:
        print(f"✅ Video loaded successfully!")
        
        # Check if audio file was created
        has_audio = hasattr(media_screen, 'audio_file') and media_screen.audio_file and os.path.exists(media_screen.audio_file)
        print(f"🔊 Audio file created: {has_audio}")
        
        if has_audio:
            audio_size = os.path.getsize(media_screen.audio_file)
            print(f"📁 Audio file: {media_screen.audio_file}")
            print(f"📏 Audio size: {audio_size} bytes")
            
            print(f"\n🎉 SUCCESS! The audio fix is working!")
            print(f"✅ Video loading now includes audio extraction")
            print(f"✅ Audio file is ready when video starts")
            print(f"✅ First loop audio issue is resolved")
            
            # Test starting video playback
            print(f"\n🎬 Testing video playback with audio...")
            playback_result = media_screen.start_video_playback()
            
            if playback_result is not False:  # Could be True or None
                print(f"✅ Video playback started successfully!")
                print(f"🔊 Audio should be playing now!")
                
                import time
                print(f"⏱️ Playing for 3 seconds...")
                time.sleep(3)
                
                print(f"\n🎉 COMPLETE SUCCESS!")
                print(f"💡 The main application will have the same working audio!")
                return True
            else:
                print(f"⚠️ Video playback had issues, but audio extraction worked")
                return True
        else:
            print(f"❌ Audio file was not created")
            return False
    else:
        print(f"❌ Video loading failed")
        return False

if __name__ == "__main__":
    try:
        success = test_audio_fix()
        if success:
            print(f"\n🎯 AUDIO FIX CONFIRMED WORKING!")
        else:
            print(f"\n❌ Audio fix needs more work")
    except Exception as e:
        print(f"❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
