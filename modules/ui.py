"""
UI Module
Handles UI constants, styles, and template management.
"""
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader

from config import get_config

logger = logging.getLogger("video_face.ui")

class UI:
    """Manages UI assets and configurations."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or get_config()
        self.html_config = self.config.get('html', {})
        self.output_dir = Path(self.config['paths']['web_dir'])
        
        # Setup Jinja environment
        template_dir = self.output_dir / "templates"
        if not template_dir.exists():
            # Fallback to current project root templates if not in web
            template_dir = Path(self.config['paths']['output_dir']) / "templates"
            
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=True
        )

    def get_template(self, name: str):
        """Load a template by name."""
        try:
            return self.jinja_env.get_template(name)
        except Exception as e:
            logger.warning(f"Template {name} not found in {self.jinja_env.loader.searchpath}. Using fallback strings.")
            return None

    @property
    def colors(self) -> Dict[str, str]:
        """Common UI colors."""
        return {
            'primary': '#667eea',
            'secondary': '#764ba2',
            'bg_gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'text': '#333333',
            'text_light': '#666666',
            'white': '#ffffff'
        }

    @property
    def labels(self) -> Dict[str, str]:
        """UI Labels (i18n support placeholder)."""
        return {
            'title': self.html_config.get('title', 'Video Face Index'),
            'persons': '人物',
            'faces': '人脸',
            'videos': '视频',
            'generated_at': '生成时间',
            'search_placeholder': '搜索人物 ID...'
        }

    def start_server(self, port: int = 8080):
        """Start a simple HTTP server to view the results."""
        import http.server
        import socketserver
        import threading
        import webbrowser

        class Handler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=str(self.output_dir), **kwargs)

        def run_server():
            with socketserver.TCPServer(("", port), Handler) as httpd:
                logger.info(f"Serving UI at http://localhost:{port}")
                httpd.serve_forever()

        thread = threading.Thread(target=run_server, daemon=True)
        thread.start()
        
        # Open in browser
        webbrowser.open(f"http://localhost:{port}/index.html")
        return thread
