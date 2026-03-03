from face_detector import FaceDetector
from gpu_config import check_gpu_status

print("=" * 50)
print("Face Detector GPU Test")
print("=" * 50)

# Check GPU status
status = check_gpu_status()
print("GPU Status:", status)

# Create detector with GPU
print("\nInitializing FaceDetector with GPU...")
detector = FaceDetector(use_gpu=True)
print("GPU available:", detector.gpu_available)
print("Use GPU setting:", detector.use_gpu)

if detector.gpu_available:
    print("\nSUCCESS: Face detection will use GPU!")
else:
    print("\nWARNING: Face detection will use CPU!")
