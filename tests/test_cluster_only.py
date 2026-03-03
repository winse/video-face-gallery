#!/usr/bin/env python
"""Test just the clustering step"""
import sys
sys.path.insert(0, '.')

import os
os.environ['DCIM_ROOT'] = r'E:\local\home\xwechat_files\winseliu_f4ec'

from face_storage import FaceStorage
from face_clusterer import FaceClusterer
import numpy as np

print("=" * 50)
print("Testing Clustering Only")
print("=" * 50)

# Load faces - use absolute path
storage = FaceStorage(data_file=r'E:\local\home\xwechat_files\winseliu_f4ec\msg\video\py\face_data.json', auto_save=False)
faces = storage.get_all_faces()
print(f"Total faces: {len(faces)}")

# Get faces with embeddings
faces_with_embeddings = [(fid, f) for fid, f in faces.items() if 'embedding' in f and f['embedding']]
print(f"Faces with embeddings: {len(faces_with_embeddings)}")

# Extract
face_ids = [fid for fid, _ in faces_with_embeddings]
embeddings = [np.array(f['embedding']) for _, f in faces_with_embeddings]
print(f"Embedding shape: {np.array(embeddings).shape}")

# Cluster
print("\nRunning DBSCAN...")
clusterer = FaceClusterer(method='dbscan', eps=0.45, min_samples=2)
labels = clusterer.fit_predict(embeddings)

unique_labels = set(labels)
unique_labels.discard(-1)
print(f"Unique clusters (excluding noise): {len(unique_labels)}")
print(f"Labels: {sorted(unique_labels)}")

# Get representatives
reps = clusterer.get_cluster_representatives()
print(f"Representatives: {reps}")

# Save clustering results
print("\nSaving clustering results...")
result = storage.save_clustering_results(
    labels,
    face_ids,
    representative_embeddings=[embeddings[reps[k]] for k in sorted(reps.keys())] if reps else None
)
print(f"Result: {result}")

# Check persons
persons = storage.get_all_persons()
print(f"\nPersons created: {len(persons)}")
for pid, pdata in persons.items():
    print(f"  {pid}: {pdata['face_count']} faces")

# Save
storage.save()
print("\nSaved to face_data.json")


