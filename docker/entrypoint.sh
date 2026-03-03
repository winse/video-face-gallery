#!/bin/bash
set -e

COMMAND="${1:-serve}"

echo "Starting WeChat Video Face Pipeline container..."

if [ "$COMMAND" = "pipeline" ]; then
    echo "Running face extraction and clustering pipeline..."
    exec python tools/run.py pipeline
elif [ "$COMMAND" = "serve" ]; then
    echo "Starting web server at http://0.0.0.0:8080 ..."
    exec python tools/run.py serve --host 0.0.0.0 --port 8080 --directory web
elif [ "$COMMAND" = "dedupe" ]; then
    echo "Running video deduplicator..."
    exec python tools/run.py dedupe
elif [ "$COMMAND" = "dupe-remove" ]; then
    echo "Running video deduplicator with auto-remove..."
    exec python tools/run.py dedupe --remove
elif [ "$COMMAND" = "bash" ]; then
    echo "Starting shell..."
    exec /bin/bash
else
    # Allow running custom python scripts like test.py etc.
    exec "$@"
fi
