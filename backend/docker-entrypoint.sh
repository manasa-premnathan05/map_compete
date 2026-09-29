#!/bin/sh
# Startup script for the map_competitor backend container.
#
# All application data lives in MongoDB Atlas - there is NO local database
# to seed or preserve. This script only starts Gunicorn (production WSGI
# server for the Flask app), bound to 0.0.0.0:$PORT as Render expects.
set -e

PORT="${PORT:-10000}"
WORKERS="${GUNICORN_WORKERS:-3}"
TIMEOUT="${GUNICORN_TIMEOUT:-1800}"

echo "[entrypoint] Starting gunicorn (workers=$WORKERS, timeout=${TIMEOUT}s) on 0.0.0.0:${PORT}"
exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WORKERS}" \
    --timeout "${TIMEOUT}" \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    "api:app"
