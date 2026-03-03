"""
FFmpeg frame extraction module
"""
import logging
import os
import subprocess
from pathlib import Path
from typing import Union, List
import cv2

# Suppress OpenCV GStreamer warnings
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'
os.environ['OPENCV_VIDEOIO_PRIORITY_GSTREAMER'] = '0'

from utils import ensure_dir, format_timestamp

logger = logging.getLogger("video_face")


class FrameExtractor:
    """Extract frames from videos using FFmpeg"""

    def __init__(
        self,
        ffmpeg_path: Union[str, Path],
        output_dir: Union[str, Path] = "thumbnails",
        quality: int = 90,
        default_size: tuple[int, int] = (640, 480)
    ):
        """
        Initialize frame extractor

        Args:
            ffmpeg_path: Path to FFmpeg executable
            output_dir: Directory for output frames
            quality: JPEG quality (1-100)
            default_size: Default output size (width, height)
        """
        self.ffmpeg_path = Path(ffmpeg_path)
        self.output_dir = ensure_dir(output_dir)
        self.quality = max(1, min(100, quality))
        self.default_size = default_size

        if not self.ffmpeg_path.exists():
            raise FileNotFoundError(f"FFmpeg not found: {self.ffmpeg_path}")

    def extract_frame(
        self,
        video_path: Union[str, Path],
        timestamp: float = 5.0,
        size: tuple[int, int] = None,
        output_filename: str = None
    ) -> Path:
        """
        Extract a single frame from video

        Args:
            video_path: Path to video file
            timestamp: Timestamp in seconds (default: 5.0)
            size: Output size (width, height), or None for default
            output_filename: Custom output filename, or auto-generated

        Returns:
            Path to extracted frame image
        """
        video_path = Path(video_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        # Generate output filename
        if output_filename is None:
            video_hash = video_path.stem[:16]  # Use first 16 chars
            output_filename = f"{video_hash}_t{int(timestamp)}.jpg"

        output_path = self.output_dir / output_filename

        # FFmpeg command
        cmd = [
            str(self.ffmpeg_path),
            '-ss', str(timestamp),  # Seek to timestamp
            '-i', str(video_path),   # Input file
            '-vframes', '1',          # Extract 1 frame
            '-q:v', str(10 - (self.quality // 10)),  # Quality (lower = better for ffmpeg)
            '-y',                     # Overwrite output
        ]

        if size:
            cmd.extend(['-vf', f'scale={size[0]}:{size[1]}'])

        cmd.append(str(output_path))

        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=30)
            logger.debug(f"Extracted frame: {output_path}")
            return output_path
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout extracting frame from {video_path}")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise

    def extract_frames(
        self,
        video_path: Union[str, Path],
        timestamps: List[float],
        size: tuple[int, int] = None
    ) -> List[Path]:
        """
        {Extract multiple frames from video

        Args:
            video_path: Path to video file
            timestamps: List of timestamps in seconds
            size: Output size (width, height), or None for default

        Returns:
            List of paths to extracted frame images
        """
        video_path = Path(video_path)
        frames = []

        for i, ts in enumerate(timestamps):
            try:
                frame_path = self.extract_frame(
                    video_path=video_path,
                    timestamp=ts,
                    size=size,
                    output_filename=f"{video_path.stem}_f{i:03d}_t{int(ts)}.jpg"
                )
                frames.append(frame_path)
            except Exception as e:
                logger.warning(f"Failed to extract frame at {ts}s: {e}")
                continue

        return frames

    def extract_evenly_spaced_frames(
        self,
        video_path: Union[str, Path],
        num_frames: int = 5,
        skip_start: float = 1.0,
        skip_end: float = 1.0
    ) -> List[Path]:
        """
        Extract evenly spaced frames from video

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            skip_start: Seconds to skip from start
            skip_end: Seconds to skip from end

        Returns:
            List of paths to extracted frame images
        """
        video_path = Path(video_path)

        # Get video duration
        duration = self._get_video_duration(video_path)
        if duration <= skip_start + skip_end:
            logger.warning(f"Video too short: {duration}s")
            return []

        # Calculate timestamps
        effective_duration = duration - skip_start - skip_end
        interval = effective_duration / (num_frames + 1)

        timestamps = [skip_start + interval * (i + 1) for i in range(num_frames)]
        return self.extract_frames(video_path, timestamps)

    def _get_video_duration(self, video_path: Path) -> float:
        """
        Get video duration using OpenCV

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()

        if fps <= 0:
            logger.warning(f"Invalid FPS: {fps}, using 30.0")
            fps = 30.0

        return frame_count / fps
