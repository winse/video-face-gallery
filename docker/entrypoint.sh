#!/bin/bash
set -e

COMMAND="${1:-serve}"

WEB_DATA_DIR="/app/web/face_data"

echo "Starting WeChat Video Face Pipeline container..."
echo "WEB_DATA_DIR: $WEB_DATA_DIR"

if [ "$COMMAND" = "pipeline" ]; then
    echo "Running face extraction and clustering pipeline..."
    python tools/run.py pipeline
elif [ "$COMMAND" = "serve" ]; then
    echo "Starting web server at http://0.0.0.0:8080 ..."
    python tools/run.py serve --host 0.0.0.0 --port 8080 --directory web
elif [ "$COMMAND" = "dedupe" ]; then
    echo "Running video deduplicator..."
    python tools/run.py dedupe
elif [ "$COMMAND" = "dupe-remove" ]; then
    echo "Running video deduplicator with auto-remove..."
    python tools/run.py dedupe --remove
elif [ "$COMMAND" = "bash" ]; then
    echo "Starting shell..."
    /bin/bash
else
    # Allow running custom python scripts like test.py etc.
    exec "$@"
fi
