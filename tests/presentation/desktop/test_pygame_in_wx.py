#!/usr/bin/env python3
"""
Test pygame audio inside a wxPython application to see if that's the issue
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import wx
import pygame
import threading
import time
import subprocess
import tempfile
import os

class AudioTestFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="Pygame Audio in wxPython Test", size=(400, 300))
        
        panel = wx.Panel(self)
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Add some text
        text = wx.StaticText(panel, label="Testing pygame audio inside wxPython...")
        sizer.Add(text, 0, wx.ALL | wx.CENTER, 10)
        
        # Add test button
        self.test_btn = wx.Button(panel, label="Test Pygame Audio")
        self.test_btn.Bind(wx.EVT_BUTTON, self.on_test_audio)
        sizer.Add(self.test_btn, 0, wx.ALL | wx.CENTER, 10)
        
        # Add status text
        self.status_text = wx.StaticText(panel, label="Ready to test...")
        sizer.Add(self.status_text, 0, wx.ALL | wx.CENTER, 10)
        
        panel.SetSizer(sizer)
        
        # Initialize pygame
        self.init_pygame()
        
    def init_pygame(self):
        """Initialize pygame mixer"""
        try:
            pygame.mixer.quit()  # Clean slate
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
            pygame.mixer.init()
            
            mixer_info = pygame.mixer.get_init()
            self.status_text.SetLabel(f"Pygame initialized: {mixer_info}")
            print(f"DEBUG: Pygame mixer initialized in wxPython: {mixer_info}")
            
        except Exception as e:
            self.status_text.SetLabel(f"Pygame init failed: {e}")
            print(f"DEBUG: Pygame init failed: {e}")
    
    def on_test_audio(self, event):
        """Test pygame audio playback"""
        self.status_text.SetLabel("Testing audio...")
        self.test_btn.Enable(False)
        
        # Run audio test in thread to avoid blocking GUI
        thread = threading.Thread(target=self.test_audio_thread)
        thread.daemon = True
        thread.start()
    
    def test_audio_thread(self):
        """Test audio in separate thread"""
        try:
            print("DEBUG: Starting pygame audio test inside wxPython...")
            
            # Extract audio from our test video
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp:
                temp_path = temp.name
            
            result = subprocess.run([
                'ffmpeg', '-i', '/Users/tombrumbaugh/Desktop/loud_beep_test.mp4',
                '-vn', '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '2', '-y',
                temp_path
            ], capture_output=True)
            
            if result.returncode == 0:
                print("DEBUG: Audio extracted successfully")
                
                # Update GUI
                wx.CallAfter(self.status_text.SetLabel, "Playing loud beep...")
                
                # Play with pygame
                pygame.mixer.music.load(temp_path)
                pygame.mixer.music.set_volume(1.0)
                pygame.mixer.music.play()
                
                print("DEBUG: Pygame music started")
                print("DEBUG: 🔊 AUDIO SHOULD BE PLAYING NOW (inside wxPython)!")
                
                # Monitor playback
                start_time = time.time()
                while pygame.mixer.music.get_busy():
                    elapsed = time.time() - start_time
                    wx.CallAfter(self.status_text.SetLabel, f"Playing... {elapsed:.1f}s")
                    time.sleep(0.1)
                
                print("DEBUG: Audio playback finished")
                wx.CallAfter(self.status_text.SetLabel, "Audio test completed")
                
                # Clean up
                os.unlink(temp_path)
                
            else:
                print("DEBUG: Audio extraction failed")
                wx.CallAfter(self.status_text.SetLabel, "Audio extraction failed")
                
        except Exception as e:
            print(f"DEBUG: Audio test error: {e}")
            wx.CallAfter(self.status_text.SetLabel, f"Error: {e}")
        
        finally:
            wx.CallAfter(self.test_btn.Enable, True)

class AudioTestApp(wx.App):
    def OnInit(self):
        frame = AudioTestFrame()
        frame.Show()
        return True

def main():
    print("Testing pygame audio inside wxPython...")
    print("This will help us determine if wxPython is interfering with pygame audio.")
    print("=" * 60)
    
    app = AudioTestApp()
    app.MainLoop()

if __name__ == "__main__":
    main()
