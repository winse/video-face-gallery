#!/usr/bin/env python
import json

with open('face_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Show structure of faces (first 2)
print("=== FACES STRUCTURE ===")
faces = data['faces']
for i, (fid, fdata) in enumerate(list(faces.items())[:3]):
    print(f"\nFace {fid}:")
    for k, v in fdata.items():
        if k != 'embedding':
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: [{len(v)} dimensions]")

# Show structure of persons
print("\n\n=== PERSONS STRUCTURE ===")
persons = data['persons']
for pid, pdata in list(persons.items())[:3]:
    print(f"\n{pid}:")
    for k, v in pdata.items():
        if k != 'faces':
            print(f"  {k}: {v}")
        else:
            print(f"  {k}: [{len(v)} face_ids]")

print(f"\n\nTotal: {len(faces)} faces, {len(persons)} persons")
