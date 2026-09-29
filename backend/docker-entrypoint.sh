#!/bin/sh
# Production entrypoint for the Flask backend on Render.
# MongoDB Atlas is the only persistent database.
# Selenium/Chromium is started only when a scraping request is made.

set -e

PORT="${PORT:-10000}"
WORKERS="${GUNICORN_WORKERS:-1}"
TIMEOUT="${GUNICORN_TIMEOUT:-1800}"

echo "[entrypoint] Starting gunicorn"
echo "[entrypoint] bind=0.0.0.0:${PORT}"
echo "[entrypoint] workers=${WORKERS}"
echo "[entrypoint] timeout=${TIMEOUT}s"

exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --workers "${WORKERS}" \
    --timeout "${TIMEOUT}" \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    "api:app"