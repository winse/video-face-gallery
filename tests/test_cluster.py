import sys
sys.path.insert(0, '.')

from pipeline import FaceExtractionPipeline
from face_storage import FaceStorage

# Check data first
storage = FaceStorage()
faces = storage.get_all_faces()
print(f"Total faces: {len(faces)}")

# Count faces with embeddings
faces_with_embeddings = {k: v for k, v in faces.items() if 'embedding' in v and v['embedding']}
print(f"Faces with embeddings: {len(faces_with_embeddings)}")

# Check embedding shape from first face
if faces_with_embeddings:
    first_face = list(faces_with_embeddings.values())[0]
    emb = first_face.get('embedding')
    if emb:
        print(f"Embedding type: {type(emb)}")
        print(f"Embedding length: {len(emb) if isinstance(emb, (list, tuple)) else 'unknown'}")

# Now run clustering
print("\nRunning clustering...")
p = FaceExtractionPipeline()
try:
    result = p.run_clustering()
    print("Clustering result:", result)
except Exception as e:
    print(f"Clustering error: {e}")
    import traceback
    traceback.print_exc()
