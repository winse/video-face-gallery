"""
HTML index and detail pages generator for face classification
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import orjson
from datetime import datetime
import shutil

from config import get_config
from utils import format_timestamp
from jinja2 import Template

logger = logging.getLogger("video_face.html")

class HTMLGenerator:
    """Generate HTML index and detail pages from face clustering results"""

    def __init__(
        self,
        output_file: Optional[Path] = None,
        template_file: Optional[Path] = None,
        detail_dir: str = "person_details",
        config: Optional[Dict[str, Any]] = None
    ):
        self.config = config or get_config()
        html_config = self.config['html']

        output_dir = Path(self.config['paths']['output_dir'])
        self.output_file = Path(output_file or output_dir / html_config['output_file'])
        self.template_file = Path(template_file or html_config['template_file'])
        
        # Detail pages go into a folder relative to the project root
        paths_output_dir = self.config['paths']['output_dir']
        self.detail_dir = Path(paths_output_dir) / detail_dir
        self.detail_dir.mkdir(exist_ok=True)

    def generate(
        self,
        persons: Dict[str, Dict[str, Any]],
        faces: Dict[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate HTML index page and person detail pages"""
        logger.info("Generating HTML pages...")

        # Prepare data
        data = self._prepare_data(persons, faces, metadata)

        # Generate person detail pages
        self._generate_detail_pages(persons, faces)

        # Render index page
        if self.template_file.exists():
            html = self._render_from_template(data)
        else:
            html = self._render_embedded(data)

        # Write output
        self.output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.output_file, 'w', encoding='utf-8') as f:
            f.write(html)

        logger.info(f"HTML generated: {self.output_file}")
        return self.output_file

    def _prepare_data(
        self,
        persons: Dict[str, Dict[str, Any]],
        faces: Dict[str, Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Prepare data for template rendering"""

        def get_thumbnail(person_id: str, person_data: Dict[str, Any]) -> Optional[str]:
            face_ids = person_data.get('faces', [])
            if not face_ids: return None
            face_id = face_ids[0]
            face = faces.get(face_id, {})
            thumb_path = face.get('thumbnail_path') or face.get('frame_path')
            if thumb_path:
                thumb_str = str(thumb_path).replace('\\', '/')
                if 'thumbnails/' in thumb_str:
                    return thumb_str.split('thumbnails/')[-1]
                return Path(thumb_str).name
            return None

        sorted_persons = sorted(
            persons.items(),
            key=lambda x: x[1].get('face_count', 0),
            reverse=True
        )

        persons_list = []
        for pid, pdata in sorted_persons:
            persons_list.append({
                'id': pid,
                'cluster_id': pdata.get('cluster_id'),
                'face_count': pdata.get('face_count', 0),
                'video_count': pdata.get('video_count', 0),
                'first_seen': pdata.get('first_seen'),
                'last_seen': pdata.get('last_seen'),
                'thumbnail': get_thumbnail(pid, pdata),
                'first_seen_str': format_timestamp(pdata.get('first_seen')),
                'last_seen_str': format_timestamp(pdata.get('last_seen')),
                'detail_page': f"person_details/{pid}.html"
            })

        result = {
            'persons': persons_list,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_persons': len(persons),
                'total_faces': sum(p.get('face_count', 0) for p in persons.values()),
                'title': self.config['html'].get('title', 'Video Face Index')
            }
        }
        if metadata: result['metadata'].update(metadata)
        return result

    def _generate_detail_pages(self, persons: Dict[str, Dict[str, Any]], faces: Dict[str, Dict[str, Any]]) -> None:
        """Generate individual person detail pages"""
        for person_id, person_data in persons.items():
            face_ids = person_data.get('faces', [])
            face_list = []
            for face_id in face_ids[:100]: # Show up to 100 faces
                face = faces.get(face_id, {})
                finfo = {
                    'id': face_id,
                    'video_name': face.get('video_name', ''),
                    'timestamp_str': format_timestamp(face.get('timestamp')),
                    'confidence': face.get('confidence', 0),
                }
                thumb_path = face.get('thumbnail_path') or face.get('frame_path')
                if thumb_path:
                    thumb_str = str(thumb_path).replace('\\', '/')
                    finfo['thumbnail'] = thumb_str.split('thumbnails/')[-1] if 'thumbnails/' in thumb_str else Path(thumb_str).name
                
                face_list.append(finfo)

            html = self._render_detail_page({
                'person': {
                    'id': person_id,
                    'cluster_id': person_data.get('cluster_id'),
                    'face_count': person_data.get('face_count', 0),
                    'video_count': person_data.get('video_count', 0),
                },
                'faces': face_list,
                'title': f"Person #{person_data.get('cluster_id')} - Details"
            })

            with open(self.detail_dir / f"{person_id}.html", 'w', encoding='utf-8') as f:
                f.write(html)
        logger.info(f"Generated {len(persons)} detail pages")

    def _render_from_template(self, data: Dict[str, Any]) -> str:
        with open(self.template_file, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        return template.render(**data)

    def _render_embedded(self, data: Dict[str, Any]) -> str:
        template_str = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8"><title>{{ metadata["title"] }}</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
        .person-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 5px rgba(0,0,0,0.1); cursor: pointer; }
        .avatar { width: 100%; height: 200px; object-fit: cover; background: #ddd; }
        .info { padding: 15px; }
        .name { font-weight: bold; font-size: 16px; margin-bottom: 5px; }
        .stats { font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <h1>{{ metadata["title"] }}</h1>
    <div class="person-grid">
        {% for person in persons %}
        <div class="card" onclick="location.href='{{ person.detail_page }}'">
            <img class="avatar" src="thumbnails/{{ person.thumbnail }}" onerror="this.src='data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22><rect width=%22100%22 height=%22100%22 fill=%22%23ccc%22/><text x=%2250%%22 y=%2250%%22 dominant-baseline=%22middle%22 text-anchor=%22middle%22 font-size=%2240%22>👤</text></svg>'">
            <div class="info">
                <div class="name">Person #{{ person.cluster_id }}</div>
                <div class="stats">{{ person.face_count }} faces | {{ person.video_count }} videos</div>
                <div class="stats" style="margin-top:5px; font-size:10px;">ID: {{ person.id }}</div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>"""
        return Template(template_str).render(**data)

    def _render_detail_page(self, data: Dict[str, Any]) -> str:
        template_str = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8"><title>{{ title }}</title>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
        .back { margin-bottom: 20px; display: inline-block; color: #667eea; text-decoration: none; }
        .face-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px; }
        .face-card { background: white; border-radius: 5px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
        .face-img { width: 100%; height: 150px; object-fit: cover; }
        .face-info { padding: 10px; font-size: 11px; }
    </style>
</head>
<body>
    <a href="../index.html" class="back">&larr; 返回列表</a>
    <h1>{{ title }}</h1>
    <p>ID: {{ person.id }} | Faces: {{ person.face_count }} | Videos: {{ person.video_count }}</p>
    <div class="face-grid">
        {% for face in faces %}
        <div class="face-card">
            <img class="face-img" src="../thumbnails/{{ face.thumbnail }}">
            <div class="face-info">
                <div><b>{{ face.video_name }}</b></div>
                <div>Time: {{ face.timestamp_str }}</div>
                <div>Conf: {{ "%.2f"|format(face.confidence * 100) }}%</div>
            </div>
        </div>
        {% endfor %}
    </div>
</body>
</html>"""
        return Template(template_str).render(**data)
