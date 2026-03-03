import sys
sys.path.insert(0, '.')

# Set environment before importing config
import os
os.environ['DCIM_ROOT'] = r'E:\local\home\xwechat_files\winseliu_f4ec'

from face_storage import FaceStorage
from config import get_config

# Check paths
config = get_config()
print("Config paths:")
print(f"  DCIM_ROOT: {os.environ.get('DCIM_ROOT')}")
print(f"  VIDEO_DIR: {config['paths']['video_dir']}")
print(f"  output_dir: {config['paths']['output_dir']}")
print(f"  data_file: {config['paths']['data_file']}")

from pathlib import Path
data_file = Path(config['paths']['data_file'])
print(f"\nData file: {data_file}")
print(f"Exists: {data_file.exists()}")

if data_file.exists():
    import orjson
    with open(data_file, 'rb') as f:
        data = orjson.loads(f.read())
    print(f"Faces: {len(data.get('faces', {}))}")
    print(f"Persons: {len(data.get('persons', {}))}")


