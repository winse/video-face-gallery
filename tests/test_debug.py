#!/usr/bin/env python
"""Test clustering and HTML generation"""
import sys
import traceback
sys.path.insert(0, '.')

import orjson
import numpy as np
from config import get_config

print("=" * 60)
print("Testing Clustering and HTML Generation")
print("=" * 60)

# Load faces
print("\n1. Loading face_data.json...")
with open('face_data.json', 'rb') as f:
    data = orjson.loads(f.read())

faces = data.get('faces', {})
print(f"   Total faces: {len(faces)}")

# Get faces with embeddings
faces_with_embeddings = [(fid, f) for fid, f in faces.items() if 'embedding' in f and f['embedding']]
print(f"   Faces with embeddings: {len(faces_with_embeddings)}")

if not faces_with_embeddings:
    print("ERROR: No faces with embeddings!")
    sys.exit(1)

# Extract embeddings
face_ids = [fid for fid, _ in faces_with_embeddings]
embeddings = [np.array(f['embedding']) for _, f in faces_with_embeddings]
print(f"   Embedding shape: {np.array(embeddings).shape}")

# Test clustering
print("\n2. Testing clustering...")
from face_clusterer import FaceClusterer

config = get_config()
cluster_config = config['clustering']
method = cluster_config['default_method']
params = cluster_config[method]

print(f"   Method: {method}")
print(f"   Params: {params}")

try:
    clusterer = FaceClusterer(method=method, **params)
    labels = clusterer.fit_predict(embeddings)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    print(f"   SUCCESS! Clusters: {n_clusters}")
except Exception as e:
    print(f"   FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Test HTML generation
print("\n3. Testing HTML generation...")
try:
    from html_generator import HTMLGenerator
    from face_storage import FaceStorage

    storage = FaceStorage()
    persons = storage.get_all_persons()
    print(f"   Persons: {len(persons)}")

    html_gen = HTMLGenerator()
    html_path = html_gen.generate(persons, faces)
    print(f"   SUCCESS! HTML: {html_path}")
except Exception as e:
    print(f"   FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("All tests passed!")
print("=" * 60)
