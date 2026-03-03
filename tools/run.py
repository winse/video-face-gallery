#!/usr/bin/env python
"""
Shared runtime entrypoint for local batch scripts and Docker entrypoint.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def run_command(command: list[str], extra_env: dict[str, str] | None = None) -> int:
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)
    return subprocess.call(command, cwd=str(ROOT_DIR), env=env)


def run_pipeline(no_dedupe: bool) -> int:
    env = {"DEDUPLICATION_ENABLED": "0"} if no_dedupe else None
    return run_command([sys.executable, "pipeline.py"], extra_env=env)


def run_dedupe(remove: bool) -> int:
    command = [sys.executable, "engine/video_deduplicator.py"]
    video_dir = os.environ.get("VIDEO_DIR")
    ffmpeg_path = os.environ.get("FFMPEG_PATH")
    if video_dir:
        command.extend(["--video-dir", video_dir])
    if ffmpeg_path:
        command.extend(["--ffmpeg", ffmpeg_path])
    if remove:
        command.append("--remove")
    return run_command(command)


def run_refresh() -> int:
    return run_command([sys.executable, "tools/regenerate_html.py"])


def run_serve(host: str, port: int, directory: str) -> int:
    target_dir = ROOT_DIR / directory
    if not target_dir.exists():
        print(f"WARNING: {target_dir} not found")
    return run_command(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--directory",
            directory,
            "--bind",
            host,
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified runtime command entrypoint")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_pipeline = subparsers.add_parser("pipeline", help="Run full pipeline")
    p_pipeline.add_argument("--no-dedupe", action="store_true", help="Disable deduplication")

    p_dedupe = subparsers.add_parser("dedupe", help="Run deduplication")
    p_dedupe.add_argument("--remove", action="store_true", help="Remove duplicates")

    subparsers.add_parser("refresh", help="Refresh metadata/UI artifacts")

    p_serve = subparsers.add_parser("serve", help="Start static web server")
    p_serve.add_argument("--host", default="0.0.0.0")
    p_serve.add_argument("--port", default=8080, type=int)
    p_serve.add_argument("--directory", default="web")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "pipeline":
        return run_pipeline(no_dedupe=args.no_dedupe)
    if args.command == "dedupe":
        return run_dedupe(remove=args.remove)
    if args.command == "refresh":
        return run_refresh()
    if args.command == "serve":
        return run_serve(host=args.host, port=args.port, directory=args.directory)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
