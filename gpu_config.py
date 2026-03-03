"""
GPU Configuration for InsightFace with CUDA support
"""
import logging
import os
import warnings
from typing import Dict, Any

logger = logging.getLogger("video_face")

# Suppress ONNX Runtime CUDA loading warnings
os.environ['ORT_CUDA_UNAVAILABLE_ERROR'] = '0'

# Suppress specific onnxruntime warnings
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', message='.*CUDA.*')


def get_face_detector_config(use_gpu: bool = True, device_id: int = 0) -> Dict[str, Any]:
    """
    Get face detector configuration with GPU/CUDA support

    Args:
        use_gpu: Enable GPU acceleration
        device_id: GPU device ID (default: 0)

    Returns:
        Configuration dictionary for InsightFace
    """
    import onnxruntime as ort

    config = {
        'model_name': 'buffalo_l',
        'det_size': (640, 640),
    }

    # Configure execution providers
    providers = ['CPUExecutionProvider']

    if use_gpu:
        available_providers = ort.get_available_providers()
        logger.info("Available providers: %s", available_providers)

        # Check if CUDA provider is available
        cuda_available = 'CUDAExecutionProvider' in available_providers

        if cuda_available:
            providers = [
                ('CUDAExecutionProvider', {
                    'device_id': device_id,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'gpu_mem_limit': 2 * 1024 * 1024 * 1024,
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }),
                'CPUExecutionProvider'
            ]
            logger.info("[OK] Using CUDA GPU (device %d)", device_id)
        else:
            # CUDA not available, try to detect GPU anyway
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode == 0:
                    gpu_info = result.stdout.strip()
                    logger.warning("NVIDIA GPU detected but CUDAExecutionProvider not available!")
                    logger.warning("GPU: %s", gpu_info)
                    logger.warning("This means CUDA runtime libraries are missing.")
                    logger.warning("Please install CUDA Toolkit and cuDNN:")
                    logger.warning("  1. Install CUDA Toolkit 12.x from NVIDIA")
                    logger.warning("  2. Install cuDNN 8.x")
                    logger.warning("  3. Or reinstall: pip install onnxruntime-gpu --force-reinstall")
                else:
                    logger.info("[WARN] No GPU detected by nvidia-smi")
            except FileNotFoundError:
                logger.info("[WARN] nvidia-smi not found")
            except Exception as e:
                logger.info("[WARN] nvidia-smi error: %s", e)

            logger.info("[INFO] Falling back to CPU execution")
            providers = ['CPUExecutionProvider']

    config['providers'] = providers
    return config


def check_gpu_status() -> Dict[str, Any]:
    """
    Check GPU availability and status

    Returns:
        Dictionary with GPU status information
    """
    status = {
        'available': False,
        'device': None,
        'memory_gb': 0,
        'compute_capability': None
    }

    try:
        import onnxruntime as ort
        available = ort.get_available_providers()

        if 'CUDAExecutionProvider' in available:
            status['available'] = True

            # Try to get GPU info via nvidia-smi or CUDA
            try:
                import subprocess
                result = subprocess.run(
                    ['nvidia-smi', '--query-gpu=name,memory.total,compute_cap', '--format=csv,noheader'],
                    capture_output=True, text=True, timeout=5
                )
                if result.returncode == 0:
                    parts = result.stdout.strip().split(',')
                    if len(parts) >= 3:
                        status['device'] = parts[0].strip()
                        mem_str = parts[1].strip()
                        if 'MiB' in mem_str:
                            status['memory_gb'] = float(mem_str.replace('MiB', '').strip()) / 1024
                        status['compute_capability'] = parts[2].strip()
            except Exception:
                status['device'] = 'NVIDIA GPU (details unavailable)'

    except ImportError as e:
        logger.warning(f"onnxruntime not available: {e}")

    return status


def get_optimal_batch_size(gpu_status: Dict[str, Any]) -> int:
    """
    Get optimal batch size based on GPU memory

    Args:
        gpu_status: GPU status from check_gpu_status()

    Returns:
        Optimal batch size
    """
    if not gpu_status['available']:
        return 1  # CPU: process one at a time

    memory_gb = gpu_status['memory_gb']

    if memory_gb >= 8:
        return 32
    elif memory_gb >= 4:
        return 16
    elif memory_gb >= 2:
        return 8
    else:
        return 4
