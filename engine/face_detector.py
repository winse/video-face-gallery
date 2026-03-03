"""
InsightFace face detection and embedding module
"""
import logging
import os
import sys
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from io import StringIO
import cv2

# Suppress OpenCV GStreamer warnings globally
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_VIDEOIO_PRIORITY_GSTREAMER'] = '0'

from gpu_config import get_face_detector_config, check_gpu_status

logger = logging.getLogger("video_face")

# Suppress ONNX Runtime/InsightFace info messages during init
_ORT_STDERR = sys.stderr
sys.stderr = StringIO()


class FaceDetector:
    """Face detection and embedding using InsightFace"""

    def __init__(
        self,
        use_gpu: bool = True,
        model_name: str = 'buffalo_l',
        confidence_threshold: float = 0.6,
        min_face_size: tuple[int, int] = (60, 60)
    ):
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold
        self.min_face_size = min_face_size

        config = get_face_detector_config(use_gpu=use_gpu)
        config['model_name'] = model_name

        try:
            import insightface
            self.app = insightface.app.FaceAnalysis(**config)
            
            # ctx_id: -1 for CPU, 0+ for GPU
            ctx_id = 0 if self.use_gpu else -1
            self.app.prepare(ctx_id=ctx_id, det_size=config['det_size'])
            
            logger.info("Initialized InsightFace with model: %s", model_name)
        except Exception as e:
            logger.error("Failed to initialize InsightFace: %s", e)
            raise
        finally:
            # Restore stderr
            sys.stderr = _ORT_STDERR

        gpu_status = check_gpu_status()
        self.gpu_available = gpu_status['available']
        if self.gpu_available:
            logger.info("Using GPU: %s", gpu_status.get('device', 'Unknown'))
        else:
            logger.info("Using CPU for inference")

    def detect_faces(
        self,
        image_path: Union[str, Path, np.ndarray],
        return_embedding: bool = True
    ) -> List[Dict[str, Any]]:
        if isinstance(image_path, (str, Path)):
            img = cv2.imread(str(image_path))
            if img is None:
                logger.error(f"Failed to load image: {image_path}")
                return []
        elif isinstance(image_path, np.ndarray):
            img = image_path
        else:
            raise TypeError("image_path must be str, Path, or np.ndarray")

        faces = self.app.get(img)
        results = []

        for face in faces:
            det_score = getattr(face, 'det_score',1.0)
            if det_score < self.confidence_threshold:
                continue

            bbox = face.bbox.astype(int).tolist()
            bbox_w = bbox[2] - bbox[0]
            bbox_h = bbox[3] - bbox[1]
            if bbox_w < self.min_face_size[0] or bbox_h < self.min_face_size[1]:
                continue

            result = {'bbox': bbox, 'confidence': float(det_score)}

            if return_embedding and hasattr(face, 'embedding'):
                result['embedding'] = face.embedding.astype(np.float32).tolist()
            elif return_embedding:
                embedding = self.app.get_embedding(img, face.bbox)
                result['embedding'] = embedding.astype(np.float32).tolist()

            if hasattr(face, 'kps'):
                result['landmarks_5'] = face.kps.astype(int).tolist()
            if hasattr(face, 'pose'):
                result['pose'] = face.pose.tolist()

            results.append(result)

        logger.debug(f"Detected {len(results)} faces in {image_path}")
        return results

    def process_batch(
        self,
        image_paths: List[Union[str, Path]],
        batch_size: int = 16,
        return_embedding: bool = True
    ) -> List[List[Dict[str, Any]]]:
        results = []
        for img_path in image_paths:
            try:
                faces = self.detect_faces(img_path, return_embedding=return_embedding)
                results.append(faces)
            except Exception as e:
                logger.warning(f"Failed to process {img_path}: {e}")
                results.append([])
        return results

    def extract_embedding(
        self,
        image_path: Union[str, Path, np.ndarray],
        bbox: Optional[List[int]] = None
    ) -> Optional[np.ndarray]:
        if isinstance(image_path, (str, Path)):
            img = cv2.imread(str(image_path))
            if img is None:
                return None
        else:
            img = image_path

        if bbox is None:
            faces = self.detect_faces(img, return_embedding=True)
            if faces:
                return np.array(faces[0]['embedding'], dtype=np.float32)
            return None

        try:
            embedding = self.app.get_embedding(img, bbox)
            return embedding.astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to extract embedding: {e}")
            return None

    def compare_faces(
        self,
        embedding1: Union[List[float], np.ndarray],
        embedding2: Union[List[float], np.ndarray],
        threshold: float = 0.5
    ) -> float:
        if isinstance(embedding1, list):
            embedding1 = np.array(embedding1)
        if isinstance(embedding2, list):
            embedding2 = np.array(embedding2)

        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)
        return float(similarity)
