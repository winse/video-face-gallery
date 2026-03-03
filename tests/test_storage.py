import sys
sys.path.insert(0, '.')

from face_storage import FaceStorage
from config import get_config

# Check paths
config = get_config()
print("Config paths:")
print(f"  output_dir: {config['paths']['output_dir']}")
print(f"  data_file: {config['paths']['data_file']}")

# Initialize FaceStorage with the correct path
from pathlib import Path
data_file = Path(config['paths']['data_file'])
print(f"\nData file: {data_file}")
print(f"Exists: {data_file.exists()}")

storage = FaceStorage(data_file=data_file)
print(f"\nStorage faces: {len(storage.data.get('faces', {}))}")
print(f"Storage persons: {len(storage.data.get('persons', {}))}")
