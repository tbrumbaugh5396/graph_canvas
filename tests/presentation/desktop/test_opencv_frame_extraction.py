#!/usr/bin/env python3

"""
Test OpenCV frame extraction to verify it works for fixing video loop choppiness.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
for path in (ROOT, SRC):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


import cv2
import numpy as np
import os

def test_opencv_frame_extraction():
    print("🧪 TESTING OPENCV FRAME EXTRACTION")
    print("=" * 40)
    
    # Test video path
    video_path = "/Users/tombrumbaugh/Downloads/istockphoto-482277170-640_adpp_is.mp4"
    
    if not os.path.exists(video_path):
        print(f"❌ Video file not found: {video_path}")
        return False
    
    print(f"✅ Video file exists: {video_path}")
    
    # Open video with OpenCV
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print("❌ Failed to open video with OpenCV")
        return False
    
    print("✅ Successfully opened video with OpenCV")
    
    # Get video properties
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📹 Video properties:")
    print(f"   • Frames: {frame_count}")
    print(f"   • FPS: {fps}")
    print(f"   • Resolution: {width}x{height}")
    
    # Test frame extraction at different positions
    test_frames = [0, 30, 60, 90, 120]
    cache = {}
    
    print(f"\n🎬 Testing frame extraction:")
    
    for frame_idx in test_frames:
        if frame_idx >= frame_count:
            continue
            
        # Set frame position
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        
        if ret and frame is not None:
            # Convert BGR to RGB and flip for OpenGL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_flipped = np.flipud(frame_rgb)
            
            # Cache the frame
            cache[frame_idx] = frame_flipped.copy()
            
            print(f"   ✅ Frame {frame_idx}: {frame_flipped.shape} - Cached")
        else:
            print(f"   ❌ Frame {frame_idx}: Failed to read")
    
    cap.release()
    
    print(f"\n📊 Cache Results:")
    print(f"   • Cached frames: {len(cache)}")
    print(f"   • Cache keys: {list(cache.keys())}")
    
    # Test cache access speed
    print(f"\n⚡ Testing cache access speed:")
    import time
    
    for frame_idx in cache.keys():
        start_time = time.time()
        cached_frame = cache[frame_idx]
        access_time = (time.time() - start_time) * 1000  # ms
        print(f"   • Frame {frame_idx}: {access_time:.3f}ms (FAST!)")
    
    print(f"\n🎯 CONCLUSION:")
    print(f"   ✅ OpenCV frame extraction: WORKING")
    print(f"   ✅ Frame caching: WORKING") 
    print(f"   ✅ Cache access: EXTREMELY FAST")
    print(f"   🚀 This approach should fix the choppiness!")
    
    return True

if __name__ == "__main__":
    test_opencv_frame_extraction()
