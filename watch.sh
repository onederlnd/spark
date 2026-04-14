#!/bin/bash
# watch.sh — auto-restart run.py on file changes
# requires: inotifywait (sudo apt install inotify-tools)

PID=""

start() {
    echo "▶ Starting server..."
    python run.py &
    PID=$!
    echo "  PID: $PID"
}

stop() {
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "■ Stopping server (PID $PID)..."
        kill "$PID"
        wait "$PID" 2>/dev/null
    fi
}

trap "stop; exit 0" SIGINT SIGTERM

start

while true; do
    inotifywait -r -e modify,create,delete,move \
        --exclude '__pycache__|\.pyc|\.git' \
        app/ run.py 2>/dev/null

    echo "⟳ Change detected — restarting..."
    stop
    sleep 0.5
    start
done