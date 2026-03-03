#!/usr/bin/env python
"""Debug video metadata extraction"""
import os
import subprocess

# 测试视频路径
video_paths = [
    r'E:/local/home/xwechat_files/winseliu_f4ec/msg/video/2018-05/48be333c54a4017532723493a3c90815.mp4',
    r'E:\local\home\xwechat_files\winseliu_f4ec\msg\video\2018-05\48be333c54a4017532723493a3c90815.mp4',
]

ffprobe_path = r'E:\local\ffmpeg\bin\ffprobe.exe'

for vp in video_paths:
    print(f'Path: {vp}')
    print(f'  Exists: {os.path.exists(vp)}')
    if os.path.exists(vp):
        # Test ffprobe for duration
        result = subprocess.run(
            [ffprobe_path, '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', vp],
            capture_output=True, text=True, timeout=10
        )
        print(f'  Duration stdout: {repr(result.stdout)}')
        print(f'  Duration returncode: {result.returncode}')
        if result.stderr:
            print(f'  Duration stderr: {repr(result.stderr[:200])}')
        else:
            print(f'  Duration stderr: empty')
    print()
