import json
with open('face_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
face = list(data['faces'].values())[0]
print("source_video:", face.get('source_video'))
print("video_name:", face.get('video_name'))
