import json
from collections import defaultdict

print("Cleaning duplicate faces...")

with open("face_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

faces = data.get("faces", {})
persons = data.get("persons", {})

# Find unique faces (by video_name + frame_index + bbox position)
unique_faces = {}
seen_keys = set()

for fid, face in faces.items():
    vid = face.get("video_name", "")
    frame_idx = face.get("frame_index", -1)
    bbox = face.get("bbox", [])
    if len(bbox) >= 2:
        # Use bbox as part of key (first 2 values are x, y)
        key = f"{vid}_{frame_idx}_{int(bbox[0])}_{int(bbox[1])}"
    else:
        key = f"{vid}_{frame_idx}"
    
    if key not in seen_keys:
        seen_keys.add(key)
        unique_faces[fid] = face

print(f"Original faces: {len(faces)}")
print(f"Unique faces: {len(unique_faces)}")
print(f"Duplicates removed: {len(faces) - len(unique_faces)}")

# Update faces
data["faces"] = unique_faces

# Update persons with unique face IDs only
for pid, pdata in persons.items():
    face_ids = pdata.get("faces", [])
    unique_ids = [fid for fid in face_ids if fid in unique_faces]
    pdata["faces"] = unique_ids
    pdata["face_count"] = len(unique_ids)
    
    # Recalculate unique videos
    videos = set()
    for fid in unique_ids:
        face = unique_faces.get(fid, {})
        vid = face.get("source_video", "")
        if vid:
            videos.add(vid)
    pdata["unique_videos"] = list(videos)
    pdata["video_count"] = len(videos)

# Save cleaned data
with open("face_data.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"\nSaved cleaned data")
print(f"Total persons: {len(persons)}")

# Show updated counts
for pid, pdata in sorted(persons.items(), key=lambda x: -x[1].get("face_count", 0))[:5]:
    print(f"  {pid}: {pdata.get('face_count', 0)} faces, {pdata.get('video_count', 0)} videos")
