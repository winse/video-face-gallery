"""
Main processing pipeline for video face extraction and classification
Simplified using source, portrait, and builder modules.
"""
import logging
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import get_config
from utils import setup_logging, ProgressTracker, get_video_date_from_path
from engine.frame_extractor import FrameExtractor
from engine.face_detector import FaceDetector

# Import new refactored modules
from modules.source import VideoSource
from modules.portrait import PortraitData
from modules.builder import UIBuilder

logger = logging.getLogger("video_face")

class FaceExtractionPipeline:
    """Complete pipeline for face extraction from videos"""

    def __init__(
        self,
        video_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or get_config()
        paths = self.config['paths']
        
        # Immediate migration of legacy files to 'web' directory
        old_data = Path(paths['project_dir']) / 'face_data.json'
        new_data = Path(paths['data_file'])
        if old_data.exists() and old_data.resolve() != new_data.resolve():
            import shutil
            new_data.parent.mkdir(parents=True, exist_ok=True)
            try:
                shutil.move(str(old_data), str(new_data))
                print(f"Migrated data file to {new_data}")
            except Exception: pass

        old_thumbs = Path(paths['project_dir']) / 'thumbnails'
        new_thumbs = Path(paths['thumbnails_dir'])
        if old_thumbs.exists() and old_thumbs.resolve() != new_thumbs.resolve():
            import shutil
            new_thumbs.parent.mkdir(parents=True, exist_ok=True)
            try:
                if new_thumbs.exists():
                    for item in old_thumbs.iterdir():
                        if not (new_thumbs / item.name).exists():
                            shutil.move(str(item), str(new_thumbs))
                    if not any(old_thumbs.iterdir()): old_thumbs.rmdir()
                else:
                    shutil.move(str(old_thumbs), str(new_thumbs))
                print(f"Migrated thumbnails to {new_thumbs}")
            except Exception: pass

        self.video_dir = Path(video_dir or paths['video_dir'])
        self.output_dir = Path(output_dir or paths['output_dir'])

        # Setup logging
        log_config = self.config['logging']
        self.logger = setup_logging(log_config['log_file'], getattr(logging, log_config['level']))

        # Initialize core components via new modules
        self.source_manager = VideoSource(video_dir=self.video_dir, config=self.config)
        self.portrait_manager = PortraitData(config=self.config)
        self.ui_builder = UIBuilder(config=self.config)
        
        # Detector and Extractor (Core compute components)
        self.frame_extractor = None
        self.face_detector = None

        self.stats = {
            'total_videos': 0,
            'processed_videos': 0,
            'total_faces': 0,
            'failed_videos': []
        }

    def initialize_components(self) -> None:
        """Initialize detection and extraction components"""
        self.logger.info("Initializing pipeline components...")

        ffmpeg_config = self.config['ffmpeg']
        self.frame_extractor = FrameExtractor(
            ffmpeg_path=ffmpeg_config['ffmpeg_path'],
            ffprobe_path=ffmpeg_config.get('ffprobe_path'),
            output_dir=self.output_dir / ffmpeg_config['output_dir'],
            quality=ffmpeg_config['quality']
        )

        face_config = self.config['face_detection']
        self.face_detector = FaceDetector(
            use_gpu=face_config['use_gpu'],
            model_name=face_config['model_name'],
            confidence_threshold=face_config['confidence_threshold']
        )

        self.logger.info("Components initialized")

    def run_processing(self, videos: List[Path]) -> None:
        """Process multiple videos to extract faces"""
        self.logger.info(f"Processing {len(videos)} videos...")

        # Skip already processed
        processed_videos = set()
        for face in self.portrait_manager.get_all_faces().values():
            if face.get('video_name'):
                processed_videos.add(face['video_name'])

        progress = ProgressTracker(len(videos), "Processing videos")
        for video in videos:
            if video.name in processed_videos:
                self.stats['processed_videos'] += 1
                progress.update()
                continue

            faces = self._process_single_video(video)
            self.stats['total_faces'] += len(faces)
            self.stats['processed_videos'] += 1
            progress.update()

        progress.complete()

    def _process_single_video(self, video_path: Path) -> List[Dict[str, Any]]:
        """Process single video: extract frames, detect faces"""
        self.logger.info(f"[START] {video_path.name}")
        video_faces = []
        video_date = get_video_date_from_path(video_path)

        try:
            frames_config = self.config['video_processing']
            adaptive = frames_config.get('adaptive_sampling', {}) or {}
            use_adaptive = bool(adaptive.get('enabled', True))
            skip_start = frames_config['skip_start_seconds']
            skip_end = frames_config['skip_end_seconds']

            if use_adaptive:
                frames = self.frame_extractor.extract_adaptive_frames(
                    video_path=video_path,
                    base_frames=int(frames_config.get('frames_per_video', 3)),
                    skip_start=skip_start,
                    skip_end=skip_end,
                    target_interval_seconds=float(adaptive.get('target_interval_seconds', 8.0)),
                    min_frames=int(adaptive.get('min_frames', 6)),
                    max_frames=int(adaptive.get('max_frames', 48))
                )
            else:
                frames = self.frame_extractor.extract_evenly_spaced_frames(
                    video_path,
                    num_frames=frames_config['frames_per_video'],
                    skip_start=skip_start,
                    skip_end=skip_end
                )

            video_faces.extend(self._detect_faces_from_frames(video_path, video_date, frames))

            # Retry with prime-count staged sampling when first pass detects no face.
            if (not video_faces) and bool(adaptive.get('retry_if_no_face', True)):
                base_count = max(1, len(frames))
                retry_rounds = max(1, int(adaptive.get('retry_max_rounds', 3)))
                configured_primes = adaptive.get('retry_prime_frames', [11, 17, 29]) or [11, 17, 29]
                retry_targets = []
                for n in configured_primes:
                    try:
                        v = int(n)
                        if v > base_count and v > 1:
                            retry_targets.append(v)
                    except Exception:
                        continue
                retry_targets = sorted(set(retry_targets))[:retry_rounds]

                existing_ts = {
                    round(self._extract_frame_meta(f, idx)[1], 2)
                    for idx, f in enumerate(frames)
                }
                for retry_count in retry_targets:
                    self.logger.info(
                        "[RETRY] %s no faces in first pass, retry with %d frames",
                        video_path.name, retry_count
                    )
                    retry_frames = self.frame_extractor.extract_evenly_spaced_frames(
                        video_path=video_path,
                        num_frames=retry_count,
                        skip_start=skip_start,
                        skip_end=skip_end
                    )
                    extra_retry_frames = []
                    for idx, f in enumerate(retry_frames):
                        ts = round(self._extract_frame_meta(f, idx)[1], 2)
                        if ts not in existing_ts:
                            existing_ts.add(ts)
                            extra_retry_frames.append(f)
                    if extra_retry_frames:
                        video_faces.extend(self._detect_faces_from_frames(video_path, video_date, extra_retry_frames))
                    if video_faces:
                        break

            self.logger.info(f"[DONE] {video_path.name}: {len(video_faces)} faces")
        except Exception as e:
            self.logger.error(f"[ERROR] {video_path.name}: {e}")
            self.stats['failed_videos'].append(str(video_path))

        return video_faces

    def _detect_faces_from_frames(
        self,
        video_path: Path,
        video_date: str,
        frames: List[Any]
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for i, frame in enumerate(frames):
            frame_path, frame_timestamp, frame_index = self._extract_frame_meta(frame, i)
            faces = self.face_detector.detect_faces(frame_path, return_embedding=True)
            for face in faces:
                face_id = str(uuid.uuid4())
                face.update({
                    'id': face_id,
                    'face_id': face_id,
                    'source_video': str(video_path),
                    'video_name': video_path.name,
                    'video_date': video_date,
                    'timestamp': frame_timestamp,
                    'frame_index': frame_index,
                    'frame_path': str(frame_path),
                    'thumbnail_path': str(frame_path)
                })
                self.portrait_manager.save_face(face_id, face)
                results.append(face)
        return results

    def _extract_frame_meta(self, frame: Any, default_index: int) -> tuple[Path, float, int]:
        # Backward-compatible frame record handling:
        # - New: {'path': Path, 'timestamp': float, 'frame_index': int}
        # - Old: Path only
        if isinstance(frame, dict):
            frame_path = Path(frame.get('path', ''))
            frame_timestamp = self._to_float(frame.get('timestamp'), 0.0)
            frame_index = int(frame.get('frame_index', default_index))
        else:
            frame_path = Path(frame)
            frame_timestamp = self._infer_timestamp_from_frame_name(frame_path)
            frame_index = default_index
        return frame_path, frame_timestamp, frame_index

    @staticmethod
    def _to_float(value: Any, fallback: float = 0.0) -> float:
        try:
            n = float(value)
            return n if n == n else fallback
        except Exception:
            return fallback

    @staticmethod
    def _infer_timestamp_from_frame_name(frame_path: Path) -> float:
        # Expected names include "..._t12.jpg" or "..._t12.3.jpg"
        match = re.search(r"_t(\d+(?:\.\d+)?)", frame_path.stem)
        if not match:
            return 0.0
        try:
            return float(match.group(1))
        except Exception:
            return 0.0

    def run(self) -> Dict[str, Any]:
        """Run complete pipeline"""
        start_time = time.time()
        self.initialize_components()

        # 1. Source: Scan and Deduplicate
        videos = self.source_manager.scan()
        if not videos:
            return {}
        videos = self.source_manager.deduplicate(videos)

        # 2. Process: Face Extraction
        self.run_processing(videos)

        # 3. Portrait: Clustering
        cluster_to_person = self.portrait_manager.cluster_faces()

        # 4. Builder: Enrich and Build UI
        self.ui_builder.enrich_metadata()
        self.ui_builder.build_html()

        self.stats['elapsed_time'] = time.time() - start_time
        self.stats['persons_count'] = len(cluster_to_person)
        return self.stats

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Video Face Extraction Pipeline")
    parser.add_argument('--video-dir', help='Video directory')
    args = parser.parse_args()

    pipeline = FaceExtractionPipeline(video_dir=args.video_dir)
    stats = pipeline.run()
    
    print(f"\n✓ Pipeline completed. Persons: {stats.get('persons_count', 0)}")

if __name__ == "__main__":
    main()
