"""
Pytest fixtures and test configuration
"""
import pytest
import tempfile
import shutil
from pathlib import Path

# ==========================================
# Paths and Directories
# ==========================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Project root directory"""
    return Path(r"E:\local\home\xwechat_files\winseliu_f4ec\msg\video")


@pytest.fixture(scope="session")
def video_dir(project_root: Path) -> Path:
    """2026-02 video directory for testing"""
    return project_root / "2026-02"


@pytest.fixture(scope="session")
def ffmpeg_path() -> Path:
    """FFmpeg executable path"""
    return Path(r"E:\local\ffmpeg\bin\ffmpeg.exe")


# ==========================================
# Temporary Directories
# ==========================================

@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """Temporary directory for test outputs"""
    return tmp_path / "test_output"


@pytest.fixture
def thumbnail_dir(tmp_path: Path) -> Path:
    """Thumbnail output directory"""
    dir = tmp_path / "thumbnails"
    dir.mkdir(exist_ok=True)
    return dir


@pytest.fixture
def face_data_dir(tmp_path: Path) -> Path:
    """Face data output directory"""
    dir = tmp_path / "face_data"
    dir.mkdir(exist_ok=True)
    return dir


# ==========================================
# Video Files
# ==========================================

@pytest.fixture(scope="session")
def all_videos(video_dir: Path) -> list[Path]:
    """All MP4 videos in 2026-02 directory"""
    return sorted(list(video_dir.glob("*.mp4")))


@pytest.fixture
def sample_videos(all_videos: list[Path]) -> list[Path]:
    """Sample videos for testing (max 5)"""
    return all_videos[:min(5, len(all_videos))]


@pytest.fixture
def sample_video_path(all_videos: list[Path]) -> Path:
    """Single sample video for testing"""
    if not all_videos:
        pytest.skip("No MP4 files found in 2026-02 directory")
    return all_videos[0]


# ==========================================
# Mock Data
# ==========================================

@pytest.fixture
def mock_face_embedding():
    """Mock face embedding vector (512-dim for ArcFace)"""
    import numpy as np
    return np.random.rand(512).astype(np.float32)


@pytest.fixture
def mock_face_embeddings_batch(mock_face_embedding):
    """Mock batch of face embeddings"""
    import numpy as np
    return [mock_face_embedding + np.random.normal(0, 0.1, 512).astype(np.float32)
            for _ in range(10)]


# ==========================================
# GPU Configuration
# ==========================================

@pytest.fixture(scope="session")
def gpu_available():
    """Check if GPU is available"""
    try:
        import onnxruntime as ort
        return "CUDAExecutionProvider" in ort.get_available_providers()
    except ImportError:
        return False


# ==========================================
# Cleanup
# ==========================================

@pytest.fixture(autouse=True)
def cleanup_temp_dirs(temp_dir):
    """Auto-cleanup temporary directories after each test"""
    yield
    if temp_dir.exists():
        shutil.rmtree(temp_dir, ignore_errors=True)
