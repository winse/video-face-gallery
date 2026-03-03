import sys
sys.path.insert(0, '.')

import os
# Set required environment
os.environ['DCIM_ROOT'] = r'E:\local\home\xwechat_files\winseliu_f4ec'
os.environ['FFMPEG_PATH'] = r'E:\local\ffmpeg\bin\ffmpeg.exe'
os.environ['FFPROBE_PATH'] = r'E:\local\ffmpeg\bin\ffprobe.exe'

from face_storage import FaceStorage
from config import get_config
from face_clusterer import FaceClusterer
import numpy as np

# Get config
config = get_config()
data_file = config['paths']['data_file']

print(f"Loading data from: {data_file}")
storage = FaceStorage(data_file=data_file)

faces = storage.get_all_faces()
print(f"Faces loaded: {len(faces)}")

faces_with_embeddings = {k: v for k, v in faces.items() if 'embedding' in v and v['embedding']}
print(f"Faces with embeddings: {len(faces_with_embeddings)}")

if faces_with_embeddings:
    print("\nRunning clustering...")
    clusterer = FaceClusterer()
    # Extract embeddings from face dictionaries
    embeddings = [np.array(f['embedding']) for f in faces_with_embeddings.values()]
    labels = clusterer.fit_predict(embeddings)

    # Count unique clusters (excluding -1 for noise)
    unique_labels = set(labels)
    n_clusters = len([l for l in unique_labels if l != -1])
    n_noise = sum(1 for l in labels if l == -1)

    print(f"Clustering result:")
    print(f"  Total faces: {len(labels)}")
    print(f"  Clusters: {n_clusters}")
    print(f"  Noise: {n_noise}")
    print(f"  Unique labels: {unique_labels}")
else:
    print("No faces with embeddings to cluster!")


