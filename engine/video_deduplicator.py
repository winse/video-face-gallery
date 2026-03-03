"""
Video deduplication module using file SHA256.
Identifies exact duplicate files by content hash.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Set
from collections import defaultdict
from io import StringIO
import sys

logger = logging.getLogger("video_face")


class VideoDeduplicator:
    """
    Detect duplicate videos by file SHA256 (exact content match).
    """

    def __init__(
        self,
        ffmpeg_path: str,
        similarity_threshold: float = 0.90,
        sample_frames: int = 3,
        hash_size: int = 16,
        temp_dir: str = "temp_dedupe"
    ):
        """Initialize deduplicator (SHA256: only exact duplicates are grouped)."""
        self.ffmpeg_path = Path(ffmpeg_path)
        self.similarity_threshold = similarity_threshold
        self.sample_frames = sample_frames
        self.hash_size = hash_size
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
        self.fingerprints: Dict[Path, str] = {}
        self.duplicate_groups: List[List[Path]] = []

    def compute_video_fingerprint(self, video_path: Path) -> str:
        """Compute SHA256 of file content as fingerprint."""
        return self._compute_file_hash(video_path)

    def _compute_file_hash(self, video_path: Path) -> str:
        """Compute SHA256 of file content."""
        h = hashlib.sha256()
        with open(video_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        return h.hexdigest()

    def find_duplicates(self, video_paths: List[Path]) -> Tuple[List[Path], List[List[Path]]]:
        """
        Find duplicate videos (exact same content via SHA256).

        Returns:
            (unique_videos, duplicate_groups) — one representative per hash, groups with >1 file.
        """
        logger.info(f"Computing SHA256 for {len(video_paths)} videos...")
        fingerprints: Dict[Path, str] = {}
        for video in video_paths:
            try:
                fp = self.compute_video_fingerprint(video)
                fingerprints[video] = fp
                logger.debug(f"{video.name}: {fp[:16]}...")
            except Exception as e:
                logger.error(f"Failed to fingerprint {video.name}: {e}")
                fingerprints[video] = str(video.absolute())

        fp_to_paths: Dict[str, List[Path]] = defaultdict(list)
        for path, fp in fingerprints.items():
            fp_to_paths[fp].append(path)

        duplicate_groups = [paths for paths in fp_to_paths.values() if len(paths) > 1]
        unique_videos = [paths[0] for paths in fp_to_paths.values()]
        return unique_videos, duplicate_groups
    
    def remove_duplicate_info(
        self, 
        face_data_path: Path = Path("face_data.json"),
        video_dir: Path = Path("2026-02")
    ) -> Tuple[Set[str], Dict[str, List[str]]]:
        """
        Remove duplicate video entries from existing face_data.json
        
        Args:
            face_data_path: Path to face_data.json
            video_dir: Directory containing videos
            
        Returns:
            Tuple of (removed_video_names, video_to_duplicates_mapping)
        """
        import orjson
        
        if not face_data_path.exists():
            logger.warning("face_data.json not found")
            return set(), {}
        
        # Load existing data
        with open(face_data_path, 'rb') as f:
            data = orjson.loads(f.read())
        
        # Get all videos mentioned in face_data
        existing_videos = set()
        for face in data.get('faces', {}).values():
            video_name = face.get('video_name', '')
            if video_name:
                existing_videos.add(video_name)
        
        # Get video paths from directory
        video_files = list(video_dir.glob("*.mp4"))
        
        # Find duplicates among existing videos
        unique_videos, duplicate_groups = self.find_duplicates(video_files)
        
        # Build mapping of duplicates
        video_to_duplicates: Dict[str, List[str]] = {}
        removed_videos: Set[str] = set()
        
        for group in duplicate_groups:
            if len(group) <= 1:
                continue
            
            # Sort by path (keep shortest/original)
            sorted_group = sorted(group, key=lambda p: len(str(p)))
            keep = sorted_group[0]
            remove = sorted_group[1:]
            
            video_to_duplicates[keep.name] = [v.name for v in remove]
            removed_videos.update(v.name for v in remove)
        
        logger.info(f"Found {len(duplicate_groups)} duplicate groups")
        logger.info(f"Videos to remove: {len(removed_videos)}")
        
        return removed_videos, video_to_duplicates
    
    def report_duplicates(self, duplicate_groups: List[List[Path]]) -> str:
        """Generate a human-readable report of duplicates"""
        report_lines = ["=" * 60]
        report_lines.append("VIDEO DUPLICATE REPORT")
        report_lines.append("=" * 60)
        
        for i, group in enumerate(duplicate_groups, 1):
            report_lines.append(f"\nDuplicate Group {i}:")
            for j, video in enumerate(group, 1):
                size_mb = video.stat().st_size / (1024 * 1024)
                report_lines.append(f"  {j}. {video.name} ({size_mb:.2f} MB)")
        
        report_lines.append(f"\n{'=' * 60}")
        report_lines.append(f"Total duplicate groups: {len(duplicate_groups)}")
        report_lines.append(f"Total videos to remove: {sum(len(g) - 1 for g in duplicate_groups)}")
        report_lines.append("=" * 60)
        
        return '\n'.join(report_lines)


def deduplicate_videos(
    video_dir: str,
    ffmpeg_path: str,
    similarity_threshold: float = 0.90,
    remove_duplicates: bool = False
) -> Tuple[List[str], List[List[str]]]:
    """
    Convenience function to deduplicate videos in a directory.
    
    Args:
        video_dir: Directory containing videos
        ffmpeg_path: Path to FFmpeg
        similarity_threshold: Similarity threshold for duplicates
        remove_duplicates: Whether to actually remove duplicate files
        
    Returns:
        Tuple of (unique_video_names, duplicate_groups)
    """
    video_path = Path(video_dir)
    videos = list(video_path.glob("*.mp4"))
    
    deduplicator = VideoDeduplicator(
        ffmpeg_path=ffmpeg_path,
        similarity_threshold=similarity_threshold
    )
    
    unique_videos, duplicate_groups = deduplicator.find_duplicates(videos)
    
    # Print report
    print(deduplicator.report_duplicates(duplicate_groups))
    
    if remove_duplicates and duplicate_groups:
        for group in duplicate_groups:
            # Keep first, remove rest
            for video in group[1:]:
                logger.info(f"Removing duplicate: {video.name}")
                video.unlink()
        
        print(f"\nRemoved {sum(len(g) - 1 for g in duplicate_groups)} duplicate videos")
    
    unique_names = [v.name for v in unique_videos]
    group_names = [[v.name for v in g] for g in duplicate_groups]
    
    return unique_names, group_names


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Video Deduplication Tool")
    parser.add_argument('--video-dir', help='Video directory', default="2026-02")
    parser.add_argument('--ffmpeg', help='FFmpeg path', 
                       default=r"E:\local\ffmpeg\bin\ffmpeg.exe")
    parser.add_argument('--threshold', type=float, help='Similarity threshold',
                       default=0.90)
    parser.add_argument('--remove', action='store_true',
                       help='Remove duplicate files')
    
    args = parser.parse_args()
    
    unique, groups = deduplicate_videos(
        args.video_dir,
        args.ffmpeg,
        args.threshold,
        args.remove
    )
    
    print(f"\nUnique videos: {len(unique)}")
    print(f"Duplicate groups: {len(groups)}")
