"""
Portrait Data Module
Handles face storage, persons, identities, and clustering.
"""
import logging
import orjson
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import numpy as np

from engine.face_storage import FaceStorage
from engine.face_clusterer import FaceClusterer
from config import get_config

logger = logging.getLogger("video_face.portrait")

class PortraitData:
    def __init__(self, data_file: Optional[Path] = None, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        storage_config = self.config['storage']
        self.data_file = data_file or Path(storage_config['data_file'])
        self.face_storage = FaceStorage(
            data_file=self.data_file,
            auto_save=storage_config.get('auto_save', True)
        )
        self.clusterer = None

    def save_face(self, face_id: str, face_data: Dict[str, Any]) -> None:
        """Save a single face detection result."""
        self.face_storage.save_face(face_id, face_data)

    def get_all_faces(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all stored faces."""
        return self.face_storage.get_all_faces()

    def get_all_persons(self) -> Dict[str, Dict[str, Any]]:
        """Retrieve all stored person clustering results."""
        return self.face_storage.get_all_persons()

    def cluster_faces(self, method: str = 'dbscan', **params) -> Dict[int, str]:
        """Cluster existing faces into person identities."""
        logger.info("Running face clustering...")
        
        all_faces = self.face_storage.get_all_faces()
        faces_with_embeddings = [
            (fid, f) for fid, f in all_faces.items()
            if 'embedding' in f and f['embedding']
        ]

        if not faces_with_embeddings:
            logger.warning("No faces with embeddings found")
            return {}

        # Extract embeddings and IDs
        face_ids = [fid for fid, _ in faces_with_embeddings]
        embeddings = [np.array(f['embedding']) for _, f in faces_with_embeddings]

        # Use configuration if params not provided
        cluster_config = self.config['clustering']
        method = method or cluster_config.get('default_method', 'dbscan')
        clustering_params = params or cluster_config.get(method, {}).copy()
        
        # Clean params as per legacy pipeline
        clustering_params.pop('metric', None)
        clustering_params.pop('linkage', None)

        self.clusterer = FaceClusterer(method=method, **clustering_params)
        labels = self.clusterer.fit_predict(embeddings)

        # Get representatives for each cluster
        reps = self.clusterer.get_cluster_representatives()
        unique_labels = set(self.clusterer.labels_)
        unique_labels.discard(-1)  # Exclude noise

        rep_embeddings = []
        for label in sorted(unique_labels):
            if label in reps:
                rep_embeddings.append(embeddings[reps[label]])
            else:
                for idx, l in enumerate(self.clusterer.labels_):
                    if l == label:
                        rep_embeddings.append(embeddings[idx])
                        break

        # Save results into storage
        cluster_to_person = self.face_storage.save_clustering_results(
            labels,
            face_ids,
            representative_embeddings=rep_embeddings if rep_embeddings else None
        )

        metrics = self.clusterer.get_quality_metrics()
        logger.info(f"Clustering complete. Persons: {len(cluster_to_person)}. Quality: {metrics}")

        return cluster_to_person

    def save(self) -> None:
        """Explicitly save data to file."""
        self.face_storage.save()
