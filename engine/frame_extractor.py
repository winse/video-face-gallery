"""
FFmpeg frame extraction module
"""
import logging
import hashlib
import math
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Union, List, Dict, Any
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
        ffprobe_path: Union[str, Path, None] = None,
        output_dir: Union[str, Path] = "thumbnails",
        quality: int = 90,
        default_size: tuple[int, int] = (640, 480)
    ):
        """
        Initialize frame extractor

        Args:
            ffmpeg_path: Path to FFmpeg executable
            ffprobe_path: Path to FFprobe executable (optional)
            output_dir: Directory for output frames
            quality: JPEG quality (1-100)
            default_size: Default output size (width, height)
        """
        self.ffmpeg_path = self._resolve_executable(ffmpeg_path, "FFmpeg")
        self.ffprobe_path = self._resolve_executable(ffprobe_path or "ffprobe", "FFprobe")

        self.output_dir = ensure_dir(output_dir)
        self.quality = max(1, min(100, quality))
        self.default_size = default_size

    @staticmethod
    def _resolve_executable(executable: Union[str, Path], label: str) -> Path:
        exe_value = str(executable)
        exe_file = Path(exe_value)
        if exe_file.exists():
            return exe_file
        resolved = shutil.which(exe_value)
        if not resolved:
            raise FileNotFoundError(f"{label} not found: {exe_value}")
        return Path(resolved)

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
            output_filename = self._build_safe_frame_filename(video_path, frame_index=0, timestamp=timestamp)

        output_path = self.output_dir / output_filename

        qv = str(10 - (self.quality // 10))
        scale_args: List[str] = ['-vf', f'scale={size[0]}:{size[1]}'] if size else []

        # Strategy A: fast seek (faster for most videos)
        cmd_fast = [
            str(self.ffmpeg_path),
            '-ss', str(timestamp),
            '-i', str(video_path),
            '-an', '-sn', '-dn',
            '-vframes', '1',
            '-q:v', qv,
            '-y',
            *scale_args,
            str(output_path)
        ]

        # Strategy B: accurate seek fallback (more robust on some long/edge timestamps)
        cmd_accurate = [
            str(self.ffmpeg_path),
            '-i', str(video_path),
            '-ss', str(timestamp),
            '-an', '-sn', '-dn',
            '-vframes', '1',
            '-q:v', qv,
            '-y',
            *scale_args,
            str(output_path)
        ]

        ok, err = self._run_ffmpeg_extract(cmd_fast, output_path, timeout=45)
        if not ok:
            ok, err2 = self._run_ffmpeg_extract(cmd_accurate, output_path, timeout=90)
            err = (err or "") + ("\n" + err2 if err2 else "")

        if not ok:
            logger.error("FFmpeg error: %s", err.strip() if err else "Unknown extraction failure")
            raise RuntimeError(f"Failed to extract frame at {timestamp}s for {video_path.name}")

        logger.debug(f"Extracted frame: {output_path}")
        return output_path

    def _run_ffmpeg_extract(self, cmd: List[str], output_path: Path, timeout: int) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                cmd,
                check=False,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            return False, f"Timeout after {timeout}s"

        stderr = result.stderr or ""
        # Treat as success only if command exited 0 and image file is non-empty.
        if result.returncode == 0 and output_path.exists() and output_path.stat().st_size > 0:
            return True, ""
        return False, stderr

    def extract_frames(
        self,
        video_path: Union[str, Path],
        timestamps: List[float],
        size: tuple[int, int] = None
    ) -> List[Dict[str, Any]]:
        """
        {Extract multiple frames from video

        Args:
            video_path: Path to video file
            timestamps: List of timestamps in seconds
            size: Output size (width, height), or None for default

        Returns:
            List of frame records:
            - path: extracted frame image path
            - timestamp: source timestamp in seconds
            - frame_index: index in requested timestamps
        """
        video_path = Path(video_path)
        frames = []

        for i, ts in enumerate(timestamps):
            try:
                frame_path = self.extract_frame(
                    video_path=video_path,
                    timestamp=ts,
                    size=size,
                    output_filename=self._build_safe_frame_filename(video_path, frame_index=i, timestamp=ts)
                )
                frames.append({
                    'path': frame_path,
                    'timestamp': float(ts),
                    'frame_index': i
                })
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
    ) -> List[Dict[str, Any]]:
        """
        Extract evenly spaced frames from video

        Args:
            video_path: Path to video file
            num_frames: Number of frames to extract
            skip_start: Seconds to skip from start
            skip_end: Seconds to skip from end

        Returns:
            List of frame records (path/timestamp/frame_index)
        """
        video_path = Path(video_path)
        num_frames = max(1, int(num_frames))

        # Get video duration
        duration = self._get_video_duration(video_path)
        if duration <= 0:
            logger.warning(
                "Duration probe failed for %s, using fallback timestamps for %d frames",
                video_path, num_frames
            )
            timestamps = self._fallback_timestamps(num_frames=num_frames, skip_start=skip_start)
            return self.extract_frames(video_path, timestamps)

        if duration <= skip_start + skip_end:
            logger.warning(f"Video too short: {duration}s")
            # For very short videos, still try sampling inside available duration.
            start = max(0.0, min(float(skip_start), max(0.0, duration * 0.1)))
            end = max(start, duration - 0.1)
            if end <= start:
                timestamps = [max(0.0, duration / 2.0)] * num_frames
            else:
                interval = (end - start) / (num_frames + 1)
                timestamps = [start + interval * (i + 1) for i in range(num_frames)]
            return self.extract_frames(video_path, timestamps)

        # Calculate timestamps
        effective_duration = duration - skip_start - skip_end
        interval = effective_duration / (num_frames + 1)

        timestamps = [skip_start + interval * (i + 1) for i in range(num_frames)]
        return self.extract_frames(video_path, timestamps)

    def extract_adaptive_frames(
        self,
        video_path: Union[str, Path],
        base_frames: int = 3,
        skip_start: float = 1.0,
        skip_end: float = 1.0,
        target_interval_seconds: float = 8.0,
        min_frames: int = 6,
        max_frames: int = 48
    ) -> List[Dict[str, Any]]:
        """
        Extract frames with duration-aware planning.

        Frame count grows with video length and is bounded by min/max.
        """
        video_path = Path(video_path)
        duration = self._get_video_duration(video_path)
        if duration <= 0:
            planned = max(int(base_frames), int(min_frames))
            planned = min(planned, int(max_frames))
            logger.warning(
                "Duration probe failed for %s, fallback to %d-frame fixed sampling",
                video_path, planned
            )
            return self.extract_evenly_spaced_frames(
                video_path=video_path,
                num_frames=planned,
                skip_start=skip_start,
                skip_end=skip_end
            )
        if duration <= skip_start + skip_end:
            logger.warning(f"Video too short: {duration}s")
            return self.extract_evenly_spaced_frames(
                video_path=video_path,
                num_frames=max(1, int(base_frames)),
                skip_start=0.0,
                skip_end=0.0
            )

        effective_duration = max(0.0, duration - skip_start - skip_end)
        interval = max(1.0, float(target_interval_seconds or 8.0))
        interval_count = int(math.ceil(effective_duration / interval))

        planned = max(int(base_frames), interval_count, int(min_frames))
        planned = min(planned, int(max_frames))
        planned = max(1, planned)

        logger.info(
            "Adaptive sampling for %s: duration=%.1fs, frames=%d (interval=%.1fs)",
            video_path.name, duration, planned, interval
        )
        return self.extract_evenly_spaced_frames(
            video_path=video_path,
            num_frames=planned,
            skip_start=skip_start,
            skip_end=skip_end
        )

    def _get_video_duration(self, video_path: Path) -> float:
        """
        Get video duration (prefer ffprobe, fallback to OpenCV)

        Args:
            video_path: Path to video file

        Returns:
            Duration in seconds
        """
        # Prefer ffprobe for robustness with unicode/special-character paths.
        try:
            cmd = [
                str(self.ffprobe_path),
                "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20
            )
            text = (result.stdout or "").strip()
            m = re.search(r"\d+(?:\.\d+)?", text)
            if m:
                duration = float(m.group(0))
                if duration > 0:
                    return duration
        except Exception as e:
            logger.warning("FFprobe duration read failed for %s: %s", video_path, e)

        # Fallback to OpenCV
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            logger.warning("OpenCV cannot open video for duration probe: %s", video_path)
            return 0.0

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        cap.release()

        if fps <= 0:
            logger.warning(f"Invalid FPS: {fps}, using 30.0")
            fps = 30.0

        return frame_count / fps

    @staticmethod
    def _fallback_timestamps(num_frames: int, skip_start: float = 1.0, step: float = 2.0) -> List[float]:
        start = max(0.0, float(skip_start))
        gap = max(0.5, float(step))
        return [start + gap * i for i in range(num_frames)]

    @staticmethod
    def _build_safe_frame_filename(video_path: Path, frame_index: int, timestamp: float) -> str:
        # Use a stable ASCII-only filename to avoid Windows/unicode path decode issues.
        key = str(video_path).encode("utf-8", errors="replace")
        digest = hashlib.md5(key).hexdigest()[:16]
        ts_ms = int(max(0.0, float(timestamp)) * 1000)
        return f"{digest}_f{int(frame_index):03d}_t{ts_ms}.jpg"
