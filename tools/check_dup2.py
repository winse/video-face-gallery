import json

with open("face_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

faces = data.get("faces", {})

# Check for duplicate thumbnails (same frame_index + video_name = duplicate?)
by_video_frame = {}
for fid, face in faces.items():
    vid = face.get("video_name", "")
    frame_idx = face.get("frame_index", -1)
    key = f"{vid}_frame{frame_idx}"
    
    if key not in by_video_frame:
        by_video_frame[key] = []
    by_video_frame[key].append(fid)

# Find keys with multiple entries
duplicates = {k: v for k, v in by_video_frame.items() if len(v) > 1}

print(f"Total unique (video, frame) pairs: {len(by_video_frame)}")
print(f"Pairs with multiple faces: {len(duplicates)}")

if duplicates:
    print("\nDuplicates found:")
    for k, v in list(duplicates.items())[:5]:
        print(f"\n{k}:")
        for fid in v:
            face = faces[fid]
            print(f"  {fid[:16]}... - timestamp: {face.get('timestamp', 0):.2f}s, bbox: {face.get('bbox', [])[:2]}")
