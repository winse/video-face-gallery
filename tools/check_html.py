import json
from collections import defaultdict

with open("face_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

faces = data.get("faces", {})
persons = data.get("persons", {})

# Check person_0000 details
pdata = persons["person_0000"]
face_ids = pdata.get("faces", [])

# Group by video_name
by_video = defaultdict(list)
for fid in face_ids:
    face = faces.get(fid, {})
    vid = face.get("video_name", "unknown")
    by_video[vid].append({
        "fid": fid,
        "timestamp": face.get("timestamp", 0),
        "frame_index": face.get("frame_index", 0)
    })

print("person_0000 video groups:")
for vid, face_list in sorted(by_video.items(), key=lambda x: -len(x[1])):
    print(f"\n{vid}: {len(face_list)} faces")
    for i, f in enumerate(face_list):
        print(f"  {i+1}. {f['fid'][:8]}... @ {f['timestamp']:.1f}s frame={f['frame_index']}")
