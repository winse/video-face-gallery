"""
UI Builder Module
Responsible for generating UI files and metadata enrichment.
"""
import os
import logging
import orjson
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from modules.source import VideoSource
from modules.portrait import PortraitData
from config import get_config

logger = logging.getLogger("video_face.builder")

class UIBuilder:
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.data_file = Path(self.config['storage']['data_file'])
        self.output_dir = Path(self.config['paths']['web_dir'])
        
    def enrich_metadata(self) -> Dict[str, Any]:
        """Load and enrich JSON data with current video metadata."""
        if not self.data_file.exists():
            logger.error(f"Data file {self.data_file} not found.")
            return {}

        with open(self.data_file, 'rb') as f:
            data = orjson.loads(f.read())

        faces = data.get('faces', {})
        source_manager = VideoSource(config=self.config)
        
        unique_videos = set(f['source_video'] for f in faces.values() if f.get('source_video'))

        logger.info(f"Enriching {len(unique_videos)} videos metadata...")
        video_metadata = {}
        for i, v_path in enumerate(unique_videos):
            if i % 50 == 0:
                logger.debug(f"  Progress: {i}/{len(unique_videos)}...")
            video_metadata[v_path] = source_manager.get_metadata(Path(v_path))

        data['video_metadata'] = video_metadata
        
        # Save enriched data
        with open(self.data_file, 'wb') as f:
            f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))

        logger.info(f"Updated {self.data_file} with enriched metadata.")
        return data

    def build_html(self) -> Path:
        """Skip HTML generation because frontend is pure static SPA."""
        logger.info("Skipping HTML generation as frontend is now data-driven.")
        
        # We only need to return the output_dir so the pipeline knows where it is
        return self.output_dir
