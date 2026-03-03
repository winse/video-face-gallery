import sys
import os
from pathlib import Path

# Add parent dir (root) to path to be safe
root = Path(__file__).parent.parent
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

print(f"Checking imports from root: {root}")

try:
    print("Checking config...")
    import config
    print(" - OK")
    
    print("Checking utils...")
    import utils
    print(" - OK")

    print("Checking engine.face_detector...")
    from engine.face_detector import FaceDetector
    print(" - OK")

    print("Checking modules.source...")
    from modules.source import VideoSource
    print(" - OK")

    print("All core imports passed.")
except Exception as e:
    import traceback
    print(f"\nIMPORT FAILED!")
    traceback.print_exc()
    sys.exit(1)
