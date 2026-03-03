"""
Face clustering module using DBSCAN and hierarchical clustering
"""
import logging
import numpy as np
from typing import List, Dict, Any, Optional
from sklearn.cluster import DBSCAN, AgglomerativeClustering
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from scipy.spatial.distance import cosine

logger = logging.getLogger("video_face")


class FaceClusterer:
    """Cluster face embeddings into person identities"""

    def __init__(
        self,
        method: str = 'dbscan',
        eps: float = 0.45,
        min_samples: int = 2,
        distance_threshold: Optional[float] = None,
        n_clusters: Optional[int] = None
    ):
        """
        Initialize face clusterer

        Args:
            method: Clustering method ('dbscan' or 'agglomerative')
            eps: DBSCAN epsilon parameter (cosine distance threshold)
            min_samples: DBSCAN minimum samples
            distance_threshold: Agglomerative distance threshold
            n_clusters: Agglomerative number of clusters (or None for auto)
        """
        self.method = method.lower()
        self.eps = eps
        self.min_samples = min_samples
        self.distance_threshold = distance_threshold or 0.55
        self.n_clusters = n_clusters

        if self.method not in ['dbscan', 'agglomerative']:
            raise ValueError(f"Unknown clustering method: {method}")

        self.labels_ = None
        self.embeddings_ = None

    def fit_predict(
        self,
        embeddings: List[np.ndarray]
    ) -> List[int]:
        """
        Fit clustering model and predict labels

        Args:
            embeddings: List of face embedding vectors

        Returns:
            Cluster labels (-1 for noise points in DBSCAN)
        """
        if len(embeddings) == 0:
            logger.warning("No embeddings provided for clustering")
            return []

        if len(embeddings) < 2:
            # If only 1 face, put it in its own cluster
            logger.info(f"Only {len(embeddings)} face, creating single cluster")
            self.labels_ = np.array([0])
            self.embeddings_ = np.array(embeddings)
            return self.labels_.tolist()

        # Convert to numpy array
        try:
            self.embeddings_ = np.array(embeddings)
        except Exception as e:
            logger.error(f"Failed to convert embeddings to numpy array: {e}")
            # Try individual conversion
            self.embeddings_ = np.array([np.array(e) for e in embeddings])

        if self.method == 'dbscan':
            self.labels_ = self._fit_dbscan()
        else:
            self.labels_ = self._fit_agglomerative()

        n_unique = len(set(self.labels_)) - (1 if -1 in self.labels_ else 0)
        logger.info(f"Clustered {len(embeddings)} faces into {n_unique} clusters")
        return self.labels_.tolist()

    def _fit_dbscan(self) -> np.ndarray:
        """
        Fit DBSCAN clustering

        Returns:
            Cluster labels
        """
        # Adjust min_samples if we have few embeddings
        actual_min_samples = min(self.min_samples, len(self.embeddings_) - 1)
        actual_min_samples = max(1, actual_min_samples)
        
        try:
            # Use cosine metric directly on embeddings
            clusterer = DBSCAN(
                eps=self.eps,
                min_samples=actual_min_samples,
                metric='cosine'
            )

            labels = clusterer.fit_predict(self.embeddings_)

            # Count clusters (excluding noise label -1)
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = sum(1 for l in labels if l == -1)
            logger.info(f"DBSCAN found {n_clusters} clusters, {n_noise} noise points")

        except Exception as e:
            logger.error(f"DBSCAN failed: {e}, falling back to all unique")
            labels = np.arange(len(self.embeddings_))

        return labels

    def _fit_agglomerative(self) -> np.ndarray:
        """
        Fit Agglomerative hierarchical clustering

        Returns:
            Cluster labels
        """
        try:
            # Determine number of clusters
            n_samples = len(self.embeddings_)
            
            # Use reasonable defaults
            if self.n_clusters is None:
                # Heuristic: sqrt(n_samples) clusters, but at least 1
                n_clusters = max(1, int(np.sqrt(n_samples)))
                n_clusters = min(n_clusters, n_samples)
            else:
                n_clusters = min(self.n_clusters, n_samples)

            clusterer = AgglomerativeClustering(
                n_clusters=n_clusters,
                affinity='cosine',
                linkage='average'
            )

            labels = clusterer.fit_predict(self.embeddings_)
            logger.info(f"Agglomerative found {len(set(labels))} clusters")

        except Exception as e:
            logger.error(f"Agglomerative failed: {e}, falling back to all unique")
            labels = np.arange(len(self.embeddings_))

        return labels

    def _compute_distance_matrix(self) -> np.ndarray:
        """
        Compute cosine distance matrix for embeddings

        Returns:
            Distance matrix
        """
        n = len(self.embeddings_)
        if n == 0:
            return np.array([])
        
        distances = np.zeros((n, n))

        for i in range(n):
            for j in range(i + 1, n):
                # Cosine distance = 1 - cosine similarity
                sim = np.dot(self.embeddings_[i], self.embeddings_[j]) / (
                    np.linalg.norm(self.embeddings_[i]) * np.linalg.norm(self.embeddings_[j])
                )
                dist = 1.0 - sim
                distances[i, j] = dist
                distances[j, i] = dist

        return distances

    def get_cluster_representatives(
        self,
        method: str = 'closest_to_center'
    ) -> Dict[int, int]:
        """
        Get representative index for each cluster

        Args:
            method: Selection method ('closest_to_center', 'first')

        Returns:
            Mapping of cluster label -> index
        """
        if self.labels_ is None:
            raise ValueError("Must fit clusterer first")

        representatives = {}
        unique_labels = set(self.labels_)
        unique_labels.discard(-1)  # Skip noise

        for label in unique_labels:
            indices = [i for i, l in enumerate(self.labels_) if l == label]
            
            if not indices:
                continue

            if method == 'closest_to_center' and len(indices) > 1:
                # Find embedding closest to cluster centroid
                embeddings = [self.embeddings_[i] for i in indices]
                try:
                    centroid = np.mean(embeddings, axis=0)
                    
                    closest_idx = indices[0]
                    min_dist = float('inf')

                    for idx in indices:
                        try:
                            dist = np.linalg.norm(self.embeddings_[idx] - centroid)
                            if dist < min_dist:
                                min_dist = dist
                                closest_idx = idx
                        except:
                            pass
                    
                    representatives[label] = closest_idx
                except:
                    representatives[label] = indices[0]
            else:
                # First element in cluster
                representatives[label] = indices[0]

        return representatives

    def get_cluster_members(self) -> Dict[int, List[int]]:
        """
        Get members of each cluster

        Returns:
            Mapping of cluster label -> list of indices
        """
        if self.labels_ is None:
            raise ValueError("Must fit clusterer first")

        clusters = {}
        for idx, label in enumerate(self.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(idx)

        return clusters

    def get_quality_metrics(self) -> Dict[str, float]:
        """
        Calculate clustering quality metrics

        Returns:
            Dictionary with quality scores
        """
        if self.labels_ is None or self.embeddings_ is None:
            raise ValueError("Must fit clusterer first")

        # Filter out noise points
        valid_mask = self.labels_ != -1
        if not np.any(valid_mask):
            logger.warning("No valid clusters (all points are noise)")
            return {'silhouette_score': 0.0, 'calinski_harabasz_score': 0.0, 'n_clusters': 0}

        valid_embeddings = self.embeddings_[valid_mask]
        valid_labels = self.labels_[valid_mask]

        # Need at least 2 samples and 2 different labels for metrics
        if len(np.unique(valid_labels)) < 2 or len(valid_embeddings) < 2:
            logger.warning("Not enough data for quality metrics")
            return {
                'silhouette_score': 0.0,
                'calinski_harabasz_score': 0.0,
                'n_clusters': len(set(valid_labels))
            }

        metrics = {}

        # Silhouette score (-1 to 1, higher is better)
        try:
            metrics['silhouette_score'] = silhouette_score(
                valid_embeddings,
                valid_labels,
                metric='cosine'
            )
        except Exception as e:
            logger.warning(f"Cannot compute silhouette score: {e}")
            metrics['silhouette_score'] = 0.0

        # Calinski-Harabasz score (higher is better)
        try:
            metrics['calinski_harabasz_score'] = calinski_harabasz_score(
                valid_embeddings,
                valid_labels
            )
        except Exception as e:
            logger.warning(f"Cannot compute CH score: {e}")
            metrics['calinski_harabasz_score'] = 0.0

        # Number of clusters
        metrics['n_clusters'] = len(set(valid_labels))

        return metrics
