import onnxruntime as ort

print("=" * 50)
print("ONNX Runtime CUDA Test")
print("=" * 50)

providers = ort.get_available_providers()
print("Available providers:", providers)

cuda_available = 'CUDAExecutionProvider' in providers
print("CUDA available:", cuda_available)

if cuda_available:
    print("")
    print("SUCCESS: CUDA is properly configured!")
    print("GPU acceleration will be used for face detection.")
else:
    print("")
    print("WARNING: CUDAExecutionProvider not found!")
    print("Install with: pip install onnxruntime-gpu")
