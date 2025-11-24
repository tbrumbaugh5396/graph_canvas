#!/usr/bin/env python3

"""
Test FFmpeg frame extraction directly to identify the issue.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import subprocess
import numpy as np
import os

def test_ffmpeg_extraction():
    print("🧪 TESTING FFMPEG FRAME EXTRACTION")
    print("=" * 40)
    
    video_path = "/Users/tombrumbaugh/Downloads/istockphoto-482277170-640_adpp_is.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print(f"✅ Video file exists: {video_path}")
    
    # Test FFmpeg command
    ffmpeg_cmd = [
        'ffmpeg', '-ss', '0.0', '-i', video_path,
        '-vframes', '1', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
        '-s', '768x432',
        '-an', '-loglevel', 'error', '-'
    ]
    
    print(f"🔧 FFmpeg command: {' '.join(ffmpeg_cmd)}")
    
    try:
        result = subprocess.run(ffmpeg_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
        
        print(f"📊 FFmpeg result:")
        print(f"   • Return code: {result.returncode}")
        print(f"   • Stdout size: {len(result.stdout)} bytes")
        print(f"   • Expected size: {768 * 432 * 3} bytes")
        
        if result.stderr:
            stderr_msg = result.stderr.decode()
            print(f"   • Stderr: {stderr_msg}")
        
        if result.returncode == 0 and len(result.stdout) == 768 * 432 * 3:
            print("✅ FFmpeg extraction: SUCCESS")
            
            # Test numpy conversion
            frame_data = result.stdout
            frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = frame.reshape((432, 768, 3))
            frame = np.flipud(frame)
            
            print(f"✅ Numpy conversion: SUCCESS")
            print(f"   • Frame shape: {frame.shape}")
            print(f"   • Frame dtype: {frame.dtype}")
            
            return True
        else:
            print("❌ FFmpeg extraction: FAILED")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg timeout")
        return False
    except Exception as e:
        print(f"❌ FFmpeg error: {e}")
        return False

if __name__ == "__main__":
    test_ffmpeg_extraction()
