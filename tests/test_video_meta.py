#!/usr/bin/env python
"""Test video metadata extraction for specific video"""
import os
import subprocess
from datetime import datetime

# Test video path from HTML
video_path = r"E:\local\home\xwechat_files\winseliu_f4ec\msg\video\2026-02\e82b45af610ec15205ae9cfbd9d27071.mp4"
ffprobe_path = r"E:\local\ffmpeg\bin\ffprobe.exe"

print("=" * 60)
print("Video Metadata Test")
print("=" * 60)

print(f"Video path: {video_path}")
print(f"File exists: {os.path.exists(video_path)}")
print(f"File size: {os.path.getsize(video_path) if os.path.exists(video_path) else 'N/A'}")

if os.path.exists(video_path):
    # Test 1: Duration
    print("\n--- Test 1: Duration ---")
    result = subprocess.run(
        [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True, timeout=10
    )
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {repr(result.stdout)}")
    print(f"Stderr: {repr(result.stderr)}")

    # Test 2: Creation time
    print("\n--- Test 2: Creation time ---")
    result = subprocess.run(
        [ffprobe_path, '-v', 'error', '-show_entries', 'format_tags=creation_time',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True, timeout=10
    )
    print(f"Return code: {result.returncode}")
    print(f"Stdout: {repr(result.stdout)}")
    print(f"Stderr: {repr(result.stderr)}")

    # Test 3: All format tags
    print("\n--- Test 3: All format tags ---")
    result = subprocess.run(
        [ffprobe_path, '-v', 'error', '-show_entries', 'format_tags',
         '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
        capture_output=True, text=True, timeout=10
    )
    print(f"Return code: {result.returncode}")
    print(f"Stdout:\n{result.stdout}")
    print(f"Stderr: {repr(result.stderr)}")

    # Test 4: File modification time
    print("\n--- Test 4: File modification time ---")
    mtime = os.path.stat(video_path).st_mtime
    dt = datetime.fromtimestamp(mtime)
    print(f"mtime: {mtime}")
    print(f"Formatted: {dt.strftime('%Y-%m-%d %H:%M')}")
else:
    print("File does not exist!")

print("=" * 60)
