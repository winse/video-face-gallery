#!/usr/bin/env python
"""Check source_video field format"""

import json

with open('face_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Check source_video vs video_name
for i, (fid, face) in enumerate(data['faces'].items()):
    if i >= 5:
        break
    print(f"Face {fid[:8]}:")
    print(f"  source_video: {face.get('source_video')}")
    print(f"  video_name: {face.get('video_name')}")
    print()
