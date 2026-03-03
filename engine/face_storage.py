"""
Face data storage module using JSON
"""
import logging
import orjson
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from utils import ensure_dir

logger = logging.getLogger("video_face")


class FaceStorage:
    """Store and retrieve face data using JSON"""

    def __init__(
        self,
        data_file: Union[str, Path] = "face_data.json",
        auto_save: bool = True
    ):
        """
        Initialize face storage

        Args:
            data_file: Path to JSON data file
            auto_save: Automatically save on each write
        """
        self.data_file = Path(data_file)
        self.auto_save = auto_save

        self.data = {
            'metadata': {
                'version': '1.0.0',
                'created_at': datetime.now().isoformat(),
                'updated_at': None
            },
            'faces': {},
            'videos': {},
            'persons': {}
        }

        # Load existing data if file exists
        if self.data_file.exists():
            self.load()

    def load(self) -> None:
        """Load data from file"""
        try:
            with open(self.data_file, 'rb') as f:
                loaded_data = orjson.loads(f.read())

            # Merge with default structure
            for key in ['faces', 'videos', 'persons']:
                if key not in loaded_data:
                    loaded_data[key] = {}

            self.data = loaded_data
            logger.info(f"Loaded data from {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")

    def save(self) -> None:
        """Save data to file"""
        self.data['metadata']['updated_at'] = datetime.now().isoformat()

        try:
            ensure_dir(self.data_file.parent)
            with open(self.data_file, 'wb') as f:
                f.write(orjson.dumps(self.data, option=orjson.OPT_INDENT_2 | orjson.OPT_SERIALIZE_NUMPY))
            logger.debug(f"Saved data to {self.data_file}")
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
            raise

    def save_face(self, face_id: str, face_data: Dict[str, Any]) -> None:
        """
        Save a single face

        Args:
            face_id: Unique face identifier
            face_data: Face data dict
        """
        self.data['faces'][face_id] = face_data
        if self.auto_save:
            self.save()

    def bulk_save_faces(self, faces_data: Dict[str, Dict[str, Any]]) -> None:
        """
        Save multiple faces

        Args:
            faces_data: Dictionary of face_id -> face_data
        """
        self.data['faces'].update(faces_data)
        if self.auto_save:
            self.save()

    def get_face(self, face_id: str) -> Optional[Dict[str, Any]]:
        """
        Get face data by ID

        Args:
            face_id: Face identifier

        Returns:
            Face data or None if not found
        """
        return self.data['faces'].get(face_id)

    def query_by_video(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Query faces by source video

        Args:
            video_path: Video file path

        Returns:
            List of face data
        """
        video_path = str(video_path)
        return [
            face for face_id, face in self.data['faces'].items()
            if face.get('source_video') == video_path
        ]

    def query_by_person(self, person_id: str) -> List[Dict[str, Any]]:
        """
        Query faces by person ID

        Args:
            person_id: Person identifier

        Returns:
            List of face data
        """
        person_data = self.data['persons'].get(person_id, {})
        face_ids = person_data.get('faces', [])

        return [self.get_face(fid) for fid in face_ids if fid]

    def save_person(self, person_id: str, person_data: Dict[str, Any]) -> None:
        """
        Save person data

        Args:
            person_id: Person identifier
            person_data: Person data dict
        """
        self.data['persons'][person_id] = person_data
        if self.auto_save:
            self.save()

    def save_clustering_results(
        self,
        cluster_labels: List[int],
        face_ids: List[str],
        representative_embeddings: Optional[List] = None
    ) -> Dict[int, str]:
        """
        Save clustering results as persons

        Args:
            cluster_labels: Cluster label for each face
            face_ids: Face ID for each label
            representative_embeddings: Representative embedding for each cluster

        Returns:
            Mapping of cluster label -> person_id
        """
        from numpy import array

        # Group faces by cluster
        clusters = {}
        for face_id, label in zip(face_ids, cluster_labels):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(face_id)

        # Create person entries
        cluster_to_person = {}
        for cluster_id, face_id_list in clusters.items():
            # Generate person ID
            person_id = f"person_{cluster_id:04d}"
            cluster_to_person[cluster_id] = person_id

            # Collect all face data
            faces = [self.get_face(fid) for fid in face_id_list if self.get_face(fid)]

            # Get timestamps
            timestamps = [f.get('timestamp', 0) for f in faces if f.get('timestamp')]
            videos = [f.get('source_video') for f in faces if f.get('source_video')]

            # Calculate representative face index
            rep_idx = 0
            if representative_embeddings and cluster_id < len(representative_embeddings):
                rep_embedding = array(representative_embeddings[cluster_id])
                # Find closest face
                best_sim = -1
                for i, face in enumerate(faces):
                    if 'embedding' in face:
                        emb = array(face['embedding'])
                        sim = float(emb.dot(rep_embedding))
                        if sim > best_sim:
                            best_sim = sim
                            rep_idx = i

            # Create person data
            person_data = {
                'id': person_id,
                'cluster_id': int(cluster_id),
                'faces': face_id_list,
                'face_count': len(face_id_list),
                'representative_face_id': face_id_list[rep_idx] if face_id_list else None,
                'first_seen': min(timestamps) if timestamps else None,
                'last_seen': max(timestamps) if timestamps else None,
                'unique_videos': list(set(videos)),
                'video_count': len(set(videos))
            }

            self.save_person(person_id, person_data)

        return cluster_to_person

    def export_clustering_results(self, output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Export clustering results to separate file

        Args:
            output_path: Output file path (default: clustering_results.json)

        Returns:
            Path to exported file
        """
        if output_path is None:
            output_path = self.data_file.parent / "clustering_results.json"

        export_data = {
            'persons': self.data['persons'],
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_persons': len(self.data['persons'])
            }
        }

        ensure_dir(output_path.parent)
        with open(output_path, 'wb') as f:
            f.write(orjson.dumps(export_data, option=orjson.OPT_INDENT_2))

        logger.info(f"Exported clustering results to {output_path}")
        return Path(output_path)

    def count(self) -> Dict[str, int]:
        """
        Get counts of stored data

        Returns:
            Dictionary with counts
        """
        return {
            'faces': len(self.data['faces']),
            'videos': len(self.data['videos']),
            'persons': len(self.data['persons'])
        }

    def get_all_faces(self) -> Dict[str, Dict[str, Any]]:
        """Get all faces"""
        return self.data['faces']

    def get_all_persons(self) -> Dict[str, Dict[str, Any]]:
        """Get all persons"""
        return self.data['persons']
