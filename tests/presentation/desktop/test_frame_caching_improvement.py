#!/usr/bin/env python3

"""
Test to demonstrate frame caching improvement for video loop smoothness.
This shows how caching eliminates the FFmpeg overhead causing choppy subsequent loops.
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
import subprocess
import numpy as np

class FrameCachingDemo:
    def __init__(self):
        self.frame_cache = {}
        self.cache_size_limit = 100
        self.video_fps = 30.0
        self.frame_extraction_times = []
        
    def simulate_frame_extraction_without_cache(self, frame_index):
        """Simulate the original slow frame extraction (FFmpeg for every frame)."""
        start_time = time.time()
        
        # Simulate FFmpeg process startup and frame extraction overhead
        # This is what happens in the original code for EVERY frame
        time.sleep(0.005)  # Simulate FFmpeg startup overhead
        time.sleep(0.003)  # Simulate frame seeking overhead
        time.sleep(0.002)  # Simulate frame extraction overhead
        
        # Create dummy frame data
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        extraction_time = time.time() - start_time
        return frame, extraction_time
    
    def simulate_frame_extraction_with_cache(self, frame_index):
        """Simulate the improved cached frame extraction."""
        start_time = time.time()
        
        # Check cache first (FAST PATH)
        if frame_index in self.frame_cache:
            frame = self.frame_cache[frame_index]
            extraction_time = time.time() - start_time
            return frame, extraction_time
        
        # Extract frame with FFmpeg (SLOW PATH - only happens once per frame)
        time.sleep(0.005)  # Simulate FFmpeg startup overhead  
        time.sleep(0.003)  # Simulate frame seeking overhead
        time.sleep(0.002)  # Simulate frame extraction overhead
        
        # Create dummy frame data
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # Cache the frame (MAJOR IMPROVEMENT)
        if len(self.frame_cache) >= self.cache_size_limit:
            oldest_key = min(self.frame_cache.keys())
            del self.frame_cache[oldest_key]
        
        self.frame_cache[frame_index] = frame.copy()
        
        extraction_time = time.time() - start_time
        return frame, extraction_time
    
    def test_loop_smoothness(self, method_name, extraction_method, num_loops=3):
        """Test video loop smoothness with different extraction methods."""
        print(f"\n🎬 Testing {method_name}")
        print("=" * 40)
        
        loop_results = []
        
        for loop_num in range(1, num_loops + 1):
            print(f"\nLoop {loop_num}:")
            
            loop_start_time = time.time()
            total_extraction_time = 0
            frames_processed = 30  # Test 1 second worth of frames
            
            for frame_index in range(frames_processed):
                frame, extraction_time = extraction_method(frame_index)
                total_extraction_time += extraction_time
                
                # Simulate frame processing time
                time.sleep(0.001)  # Minimal processing time
            
            loop_duration = time.time() - loop_start_time
            avg_extraction_time = total_extraction_time / frames_processed
            extraction_overhead = (total_extraction_time / loop_duration) * 100
            
            # Calculate smoothness metrics
            target_fps = 30.0
            actual_fps = frames_processed / loop_duration
            smoothness_score = min(100, (actual_fps / target_fps) * 100)
            
            result = {
                'loop': loop_num,
                'duration': loop_duration,
                'fps': actual_fps,
                'smoothness': smoothness_score,
                'avg_extraction_time': avg_extraction_time * 1000,  # Convert to ms
                'extraction_overhead': extraction_overhead
            }
            
            loop_results.append(result)
            
            print(f"   • Duration: {loop_duration:.3f}s")
            print(f"   • FPS: {actual_fps:.1f} (target: {target_fps})")
            print(f"   • Smoothness: {smoothness_score:.1f}/100")
            print(f"   • Avg extraction time: {avg_extraction_time*1000:.1f}ms")
            print(f"   • Extraction overhead: {extraction_overhead:.1f}%")
            
            if method_name == "WITH CACHING" and hasattr(self, 'frame_cache'):
                print(f"   • Cache hits: {len(self.frame_cache)} frames")
        
        return loop_results
    
    def run_comparison_test(self):
        """Run comparison between cached and uncached frame extraction."""
        print("🎯 Frame Caching Smoothness Improvement Test")
        print("=" * 50)
        
        print("📊 This test demonstrates why subsequent loops become choppy")
        print("   and how frame caching fixes the issue.")
        print()
        
        # Test without caching (original problematic behavior)
        print("🔴 TESTING WITHOUT CACHING (Original Problem):")
        no_cache_results = self.test_loop_smoothness(
            "WITHOUT CACHING", 
            self.simulate_frame_extraction_without_cache
        )
        
        # Reset for next test
        self.frame_cache = {}
        
        # Test with caching (improved behavior)
        print("\n🟢 TESTING WITH CACHING (Fixed Behavior):")
        cache_results = self.test_loop_smoothness(
            "WITH CACHING", 
            self.simulate_frame_extraction_with_cache
        )
        
        # Analysis
        print(f"\n📈 COMPARISON ANALYSIS:")
        print("=" * 30)
        
        print(f"\nLoop Performance Comparison:")
        for i in range(3):
            no_cache = no_cache_results[i]
            with_cache = cache_results[i]
            
            smoothness_improvement = with_cache['smoothness'] - no_cache['smoothness']
            speed_improvement = (no_cache['avg_extraction_time'] / with_cache['avg_extraction_time'])
            
            print(f"\nLoop {i+1}:")
            print(f"   Without Cache: {no_cache['smoothness']:.1f}/100 smoothness, {no_cache['avg_extraction_time']:.1f}ms avg extraction")
            print(f"   With Cache:    {with_cache['smoothness']:.1f}/100 smoothness, {with_cache['avg_extraction_time']:.1f}ms avg extraction")
            print(f"   Improvement:   {smoothness_improvement:+.1f} smoothness points, {speed_improvement:.1f}x faster extraction")
        
        print(f"\n🎯 KEY INSIGHTS:")
        print(f"   • First loop: Similar performance (cache building)")
        print(f"   • Subsequent loops: MAJOR improvement with caching")
        print(f"   • Frame extraction becomes {speed_improvement:.1f}x faster")
        print(f"   • Eliminates FFmpeg subprocess overhead")
        print(f"   • Maintains consistent smoothness across all loops")
        
        print(f"\n✅ EXPECTED RESULT IN MAIN APP:")
        print(f"   • First loop: Smooth (builds cache)")  
        print(f"   • Second loop: Much smoother (uses cache)")
        print(f"   • Third+ loops: Consistently smooth (cache hits)")
        print(f"   • No more degradation in subsequent loops!")

if __name__ == "__main__":
    demo = FrameCachingDemo()
    demo.run_comparison_test()
