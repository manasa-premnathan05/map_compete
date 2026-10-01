#!/bin/sh
# Production entrypoint for the Flask backend on Render.
# MongoDB Atlas is the only persistent database.
# Selenium/Chromium is started only when a scraping request is made.
#
# One *process*, several threads. The browser needs most of the instance's 512 MB
# (a collection run peaks around 400 MB), so a second process - which costs
# roughly 120 MB of its own before it does any work - is what pushes the service
# over the limit and gets it killed mid-run. Threads are cheap by comparison and
# they keep the service answering: while a collection run holds one thread, the
# health check and the frontend's reads are still served by the others. With
# synchronous workers a single long scrape blocked everything, which looks like an
# outage to both the platform and the interface.

set -e

PORT="${PORT:-10000}"
WORKERS="${GUNICORN_WORKERS:-1}"
THREADS="${GUNICORN_THREADS:-4}"
TIMEOUT="${GUNICORN_TIMEOUT:-1800}"

echo "[entrypoint] Starting gunicorn"
echo "[entrypoint] bind=0.0.0.0:${PORT}"
echo "[entrypoint] workers=${WORKERS} threads=${THREADS} (gthread)"
echo "[entrypoint] timeout=${TIMEOUT}s"

exec gunicorn \
    --bind "0.0.0.0:${PORT}" \
    --worker-class gthread \
    --workers "${WORKERS}" \
    --threads "${THREADS}" \
    --timeout "${TIMEOUT}" \
    --graceful-timeout 30 \
    --access-logfile - \
    --error-logfile - \
    "api:app"