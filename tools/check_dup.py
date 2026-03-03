import json
from collections import Counter

with open("face_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

faces = data.get("faces", {})
persons = data.get("persons", {})

print(f"Total faces in data: {len(faces)}")
print(f"Total persons: {len(persons)}")

# Check a person with most faces
sorted_persons = sorted(persons.items(), key=lambda x: x[1].get("face_count", 0), reverse=True)
for pid, pdata in sorted_persons[:1]:
    face_ids = pdata.get("faces", [])
    print(f"\n{pid}:")
    print(f"  Faces count: {len(face_ids)}")
    print(f"  Sample face_ids: {face_ids[:5]}")
    
    # Check for duplicates in face_ids
    unique_ids = set(face_ids)
    if len(unique_ids) != len(face_ids):
        print(f"  ERROR: Duplicate face_ids found!")
        dup = [fid for fid, count in Counter(face_ids).items() if count > 1]
        print(f"  Duplicates: {dup}")
    else:
        print(f"  All face_ids are unique")
    
    # Group by video_name
    by_video = {}
    for fid in face_ids:
        face = faces.get(fid, {})
        vid = face.get("video_name", "unknown")
        if vid not in by_video:
            by_video[vid] = []
        by_video[vid].append(fid)
    
    print(f"  Videos: {len(by_video)}")
    for vid, fids in by_video.items():
        print(f"    {vid}: {len(fids)} faces")
        if len(fids) > 10:
            print(f"      (First 3: {fids[:3]})")
            print(f"      (Last 3: {fids[-3:]})")
