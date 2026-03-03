#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Administrative script to refresh metadata and rebuild UI."""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from modules.builder import UIBuilder
from config import get_config

def main():
    config = get_config()
    builder = UIBuilder(config=config)

    print("Step 1: Enriching data with video metadata...")
    builder.enrich_metadata()

    print("\nStep 2: Note - HTML views are purely data-driven now, skipped static generation.")
    builder.build_html()

    print("\n✓ Refresh complete.")
    print(f"Access the system at: http://localhost:8080/py/index.html")

if __name__ == "__main__":
    main()
