import sys
sys.path.insert(0, '.')

import os
os.environ['DCIM_ROOT'] = r'E:\local\home\xwechat_files\winseliu_f4ec'

from pipeline import FaceExtractionPipeline

print("Initializing pipeline...")
p = FaceExtractionPipeline()

print("Running clustering...")
result = p.run_clustering()

print(f"\nClustering result: {result}")
print(f"Persons created: {len(result) if result else 0}")


