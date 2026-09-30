#!/usr/bin/env python3
"""
Zero-config local development server for MapCompete.

Why this exists: opening the frontend with a plain static server
(`python -m http.server 3000`) makes the browser talk to the API cross-origin.
That only works when the local backend can reach MongoDB Atlas, and it is
blocked by CORS when the frontend falls back to the deployed Render API
(Render only allows the Vercel origin).

This server removes both problems:

  * it serves the static frontend from `frontend/`, and
  * it proxies every `/api/*` call to a backend chosen automatically
    (local :10000 -> local :5000 -> deployed Render API),
  * it injects `window.__API_BASE__ = '/api'` into the HTML, so the SPA talks
    to the proxy. Same origin => no CORS, no hard-coded ports.

The backend link can be pinned explicitly, in this order of precedence:
`--api <url>`, then `API_BASE_URL` (also accepts `BACKEND_URL` / `API_URL`)
from the environment, `<repo>/.env` or `<repo>/backend/.env`, then auto-detect.

Usage:
    python serve_local.py                  # http://localhost:3000
    python serve_local.py --port 8000
    python serve_local.py --api http://127.0.0.1:10000/api   # force a backend

Then open http://localhost:3000. Ctrl+C stops it.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

# Backends tried in order when --api is not given. Every candidate must answer
# GET /api/health; a candidate that reports a `database` field is the real
# MapCompete API (the legacy SQLite build does not), and a healthy one (HTTP 200
# + status=="healthy") is preferred over a reachable-but-degraded one.
DEFAULT_CANDIDATES = (
    "http://127.0.0.1:10000/api",
    "http://localhost:10000/api",
    "http://127.0.0.1:5000/api",
    "http://localhost:5000/api",
    "https://map-compete.onrender.com/api",
)

INJECTION_ANCHOR = '<script src="js/app.js"'
INJECTION = "<script>window.__API_BASE__ = '/api';</script>\n    "

# --- backend link configuration ---------------------------------------------
# The frontend is a static SPA, so it cannot read .env at all. serve_local.py
# can: these keys (first one that is set wins) tell the proxy which backend to
# forward /api/* to. They are read from the environment first, then from
# <repo>/.env and <repo>/backend/.env.
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_FILES = (os.path.join(REPO_ROOT, ".env"), os.path.join(REPO_ROOT, "backend", ".env"))
API_BASE_KEYS = ("API_BASE_URL", "BACKEND_URL", "API_URL")


def read_env_file(path):
    """Minimal .env reader (stdlib only): KEY=VALUE, # comments, quoted values."""
    values = {}
    try:
        with open(path, encoding="utf-8-sig") as handle:
            for line in handle:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                values[key.strip()] = value.strip().strip('"').strip("'")
    except OSError:
        return {}
    return values


def env_api_base(env_files=ENV_FILES):
    """Return (backend_link, source) from the environment or the .env files."""
    for key in API_BASE_KEYS:
        if os.environ.get(key):
            return os.environ[key].strip(), f"{key} (environment)"
    for path in env_files:
        values = read_env_file(path)
        for key in API_BASE_KEYS:
            if values.get(key):
                return values[key], f"{key} in {os.path.relpath(path, REPO_ROOT)}"
    return None, None



def probe(base_url, timeout=5):
    """Return ('healthy'|'degraded'|'foreign'|'down', detail) for one backend."""
    try:
        with urllib.request.urlopen(f"{base_url}/health", timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8", "replace"))
        if not isinstance(payload, dict) or not isinstance(payload.get("database"), str):
            return "foreign", "answers but is not the MapCompete API"
        if payload.get("status") == "healthy":
            return "healthy", "database connected"
        return "degraded", f"database {payload.get('database')}"
    except urllib.error.HTTPError as error:  # 503 = right API, database down
        try:
            payload = json.loads(error.read().decode("utf-8", "replace"))
        except (ValueError, TypeError):
            payload = {}
        if isinstance(payload, dict) and isinstance(payload.get("database"), str):
            return "degraded", f"database {payload.get('database')}"
        return "foreign", f"HTTP {error.code}"
    except Exception as error:  # noqa: BLE001 - reported, not raised
        return "down", f"{type(error).__name__}"


def pick_backend(explicit=None):
    """Pick the upstream API: --api wins, then .env's API_BASE_URL, then auto-detect."""
    if explicit:
        state, detail = probe(explicit)
        print(f"API      : {explicit} ({state} - {detail}) [forced with --api]")
        return explicit, state

    env_value, env_source = env_api_base()
    if env_value:
        state, detail = probe(env_value)
        print(f"API      : {env_value} ({state} - {detail}) [{env_source}]")
        return env_value, state

    results = []
    for candidate in DEFAULT_CANDIDATES:
        state, detail = probe(candidate)
        results.append((candidate, state, detail))
        print(f"           {candidate:<45} {state:<9} {detail}")

    healthy = next((c for c, s, _ in results if s == "healthy"), None)
    if healthy:
        print(f"API      : {healthy} (local backend, database connected)")
        return healthy, "healthy"

    degraded = next((c for c, s, _ in results if s == "degraded"), None)
    if degraded:
        print(
            f"API      : {degraded}\n"
            "           WARNING: this backend cannot reach MongoDB, so requests will\n"
            "           return 503. Add this machine's public IP to MongoDB Atlas ->\n"
            "           Network Access, or start a backend whose database works."
        )
        return degraded, "degraded"

    render = DEFAULT_CANDIDATES[-1]
    print(
        f"API      : {render} (deployed fallback - no local backend found)\n"
        "           Start a local API with \"python backend/api.py\" to use local data."
    )
    return render, "foreign"


class DevHandler(SimpleHTTPRequestHandler):
    """Static files + /api/* proxy + window.__API_BASE__ injection."""

    server_version = "MapCompeteDev/1.0"

    # -- helpers ----------------------------------------------------------
    def _html_file(self):
        path = urllib.parse.unquote(urllib.parse.urlparse(self.path).path).lstrip("/")
        candidate = os.path.join(self.directory, path or "index.html")
        if os.path.isdir(candidate):
            candidate = os.path.join(candidate, "index.html")
        if candidate.endswith(".html") and os.path.isfile(candidate):
            return candidate
        return None

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _serve_injected_html(self):
        """Serve index.html with the API base pinned to this proxy."""
        with open(self._html_file(), "rb") as handle:
            html = handle.read().decode("utf-8", "replace")
        if INJECTION_ANCHOR in html:
            html = html.replace(INJECTION_ANCHOR, INJECTION + INJECTION_ANCHOR, 1)
        else:
            html = html.replace("</body>", f"{INJECTION}</body>", 1)
        self._send(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def _proxy(self):
        """Forward /api/* to the chosen backend and return its response as-is."""
        base = self.server.api_base.rstrip("/")
        target = base + self.path[len("/api"):]
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else None

        request = urllib.request.Request(target, data=body, method=self.command)
        content_type = self.headers.get("Content-Type")
        if content_type:
            request.add_header("Content-Type", content_type)

        try:
            with urllib.request.urlopen(request, timeout=self.server.api_timeout) as response:
                status, payload = response.status, response.read()
                content_type = response.headers.get("Content-Type", "application/json")
        except urllib.error.HTTPError as error:  # 4xx/5xx from the backend
            status, payload = error.code, error.read()
            content_type = (error.headers or {}).get("Content-Type", "application/json")
        except Exception as error:  # noqa: BLE001 - network / DNS / timeout
            status = 502
            content_type = "application/json"
            payload = json.dumps({
                "error": f"The backend at {base} is unreachable: {type(error).__name__}: {error}",
                "api_base": base,
            }).encode("utf-8")

        self._send(status, payload, content_type)
        marker = "[proxy -> backend]" if status < 400 else "[backend error]"
        sys.stderr.write(f"{marker} {self.command} {self.path} -> {status}\n")

    # -- HTTP verbs --------------------------------------------------------
    def do_GET(self):  # noqa: N802 - http.server naming
        if self.path.startswith("/api"):
            return self._proxy()
        if self._html_file():
            return self._serve_injected_html()
        return super().do_GET()

    def do_HEAD(self):  # noqa: N802
        if self.path.startswith("/api"):
            return self._proxy()
        if self._html_file():
            return self._serve_injected_html()
        return super().do_HEAD()

    def do_POST(self):  # noqa: N802
        return self._proxy()

    def do_PUT(self):  # noqa: N802
        return self._proxy()

    def do_PATCH(self):  # noqa: N802
        return self._proxy()

    def do_DELETE(self):  # noqa: N802
        return self._proxy()

    def do_OPTIONS(self):  # noqa: N802
        self.send_response(204)
        self.send_header("Allow", "GET, HEAD, POST, PUT, PATCH, DELETE, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, fmt, *args):  # keep the console readable
        sys.stderr.write(f"{time.strftime('%H:%M:%S')} {self.address_string()} {fmt % args}\n")


def main():
    parser = argparse.ArgumentParser(description="MapCompete local dev server (static files + /api proxy).")
    parser.add_argument("--port", type=int, default=3000, help="port to listen on (default 3000)")
    parser.add_argument("--directory", default="frontend", help="static root (default frontend)")
    parser.add_argument("--api", default=None, help="force an upstream API base URL, e.g. http://127.0.0.1:10000/api")
    parser.add_argument("--api-timeout", type=int, default=1800,
                        help="seconds to wait for a backend response (scrapes take minutes)")
    args = parser.parse_args()
    # Keep the startup banner visible even when stdout is redirected to a file.
    sys.stdout.reconfigure(line_buffering=True)

    root = os.path.abspath(args.directory)
    if not os.path.isfile(os.path.join(root, "index.html")):
        print(f"ERROR: {root} does not contain index.html - run this from the repo root.")
        return 2

    print("MapCompete local dev server")
    print("-" * 70)
    print(f"frontend : {root}")
    api_base, _ = pick_backend(args.api)
    print(f"url      : http://localhost:{args.port}")
    print("-" * 70)

    handler = lambda *a, **kw: DevHandler(*a, directory=root, **kw)  # noqa: E731
    server = ThreadingHTTPServer(("0.0.0.0", args.port), handler)
    server.api_base = api_base
    server.api_timeout = args.api_timeout
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
