#!/usr/bin/env python
"""Debug script for clustering issue"""
import sys
sys.path.insert(0, '.')

from pipeline import FaceExtractionPipeline
from face_clusterer import FaceClusterer

print("=" * 50)
print("Debugging Clustering Issue")
print("=" * 50)

# Initialize pipeline
p = FaceExtractionPipeline()
p.initialize_components()

# Get faces
faces = p.face_storage.get_all_faces()
print(f"Total faces stored: {len(faces)}")

# Check embeddings
faces_with_embeddings = [(fid, f) for fid, f in faces.items() if 'embedding' in f and f['embedding']]
print(f"Faces with embeddings: {len(faces_with_embeddings)}")

if not faces_with_embeddings:
    print("ERROR: No faces with embeddings found!")
    sys.exit(1)

# Check embedding structure
import numpy as np
face_ids = [fid for fid, _ in faces_with_embeddings]
embeddings = [np.array(f['embedding']) for _, f in faces_with_embeddings]

print(f"Embedding array shape: {np.array(embeddings).shape}")
print(f"Embedding dtype: {embeddings[0].dtype}")
print(f"Sample embedding (first 5): {embeddings[0][:5]}")

# Try clustering
print("\nTesting clustering...")
clusterer = FaceClusterer(method='dbscan', eps=0.45, min_samples=2)
try:
    labels = clusterer.fit_predict(embeddings)
    print(f"Clustering successful! Labels: {set(labels)}")
except Exception as e:
    print(f"Clustering failed: {e}")
    import traceback
    traceback.print_exc()
