#!/usr/bin/env python3
"""
Verify that the frontend and the backend are actually connected.

The app has three entry points that must all reach the same Flask API:

  * localhost:3000      -> python -m http.server, talks to a local backend
  * Vercel (frontend)   -> https://map-compete.vercel.app, forwards /api/* to it
  * Render (backend)    -> https://map-compete.onrender.com

This script checks the wiring end to end:

  1. Backend health + data (`GET /api/health`, `GET /api/projects`).
  2. CORS: the deployed API must answer the Vercel origin with a matching
     `Access-Control-Allow-Origin` header (needed for any direct call).
  3. Vercel rewrite: `https://<vercel>/api/*` must reach the Render API.
  4. Vercel static assets: index.html and every ES module must return 200 -
     one missing module silently breaks the whole UI ("Loading projects...").
  5. Optional live browser check (--ui) that the project dropdown really
     populates and no JavaScript error is thrown. Local runs also report which
     backend the frontend auto-detected.

Usage:
    python verify_deployment.py                     # deployed stack only
    python verify_deployment.py --local             # + http://localhost:3000
    python verify_deployment.py --ui                # + headless Chrome checks
    python verify_deployment.py --render-url https://other.onrender.com

Exit code 0 = every check passed, 1 = at least one failure.
"""

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

REPO_ROOT = Path(__file__).resolve().parent

DEFAULT_RENDER_URL = "https://map-compete.onrender.com"
DEFAULT_VERCEL_URL = "https://map-compete.vercel.app"
DEFAULT_LOCAL_URL = "http://localhost:3000"
# Origin the deployed API must allow (Render -> CORS_ORIGINS).
DEFAULT_CORS_ORIGIN = DEFAULT_VERCEL_URL

# Static files the SPA cannot boot without (index.html + app.js + every module).
STATIC_ASSETS = (
    "index.html",
    "js/app.js",
    "js/components/api.js",
    "js/components/dashboard.js",
    "js/components/competitors.js",
    "js/components/posts.js",
    "js/components/analytics.js",
    "js/components/ideas.js",
    "css/style.css",
)

IGNORED_CONSOLE_FRAGMENTS = (
    "favicon",
    "cdn.tailwindcss.com should not be used in production",
    "Download the React DevTools",
)

# Free Render instances sleep; the first request can take ~60s to wake them.
COLD_START_ATTEMPTS = 6
COLD_START_DELAY = 10


class Reporter:
    """Tiny PASS/FAIL reporter: collects results and prints them as they run."""

    def __init__(self):
        self.failures = []

    def check(self, name, ok, detail=""):
        print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" - {detail}" if detail else ""))
        if not ok:
            self.failures.append(name)
        return ok

    def skip(self, name, detail=""):
        print(f"[SKIP] {name}" + (f" - {detail}" if detail else ""))


def http_get(url, headers=None, timeout=60, attempts=3):
    """GET a URL. Returns (status, body_text, headers) and never raises for 4xx/5xx.

    Connection-level errors (DNS/TLS reset) are retried: a single transient
    failure must not look like a wiring problem.
    """
    last = (None, "no response", {})
    for attempt in range(1, attempts + 1):
        request = urllib.request.Request(url, headers=headers or {})
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.status, response.read().decode("utf-8", "replace"), dict(response.headers)
        except urllib.error.HTTPError as error:
            return error.code, error.read().decode("utf-8", "replace"), dict(error.headers or {})
        except Exception as error:  # noqa: BLE001 - reported, not raised
            last = (None, f"{type(error).__name__}: {error}", {})
            if attempt < attempts:
                print(f"       ... transient error on {url} ({last[1]}), retrying")
                time.sleep(1.5)
    return last


def get_json(url, headers=None, timeout=60):
    status, body, response_headers = http_get(url, headers=headers, timeout=timeout)
    try:
        return status, json.loads(body), response_headers
    except (TypeError, ValueError):
        return status, None, response_headers


def get_health_with_wakeup(base_url, reporter):
    """Retry the health endpoint so a sleeping Render instance is not a failure."""
    last = "no response"
    for attempt in range(1, COLD_START_ATTEMPTS + 1):
        status, payload = get_json(f"{base_url}/api/health", timeout=45)[:2]
        if status == 200 and isinstance(payload, dict):
            return status, payload, attempt
        last = f"HTTP {status}: {str(payload)[:160]}"
        if status is None or status >= 500:
            print(f"       ... attempt {attempt}/{COLD_START_ATTEMPTS} failed ({last}), retrying in {COLD_START_DELAY}s")
            time.sleep(COLD_START_DELAY)
            continue
        break
    reporter.check(f"health endpoint reachable ({base_url})", False, last)
    return None, None, COLD_START_ATTEMPTS


# ---------------------------------------------------------------------------
# 1 + 2: the deployed backend itself
# ---------------------------------------------------------------------------

def check_backend(render_url, cors_origin, reporter):
    status, health, attempts = get_health_with_wakeup(render_url, reporter)
    if status is None:
        return False

    summary = ", ".join(f"{k}={v}" for k, v in health.items() if k != "database_error")
    if health.get("database_error"):
        summary += f" database_error={health['database_error'][:120]}"
    reporter.check(
        "Render /api/health is healthy",
        health.get("status") == "healthy" and health.get("database") == "connected",
        f"woke after {attempts} attempt(s): {{{summary}}}",
    )

    status, projects, _ = get_json(f"{render_url}/api/projects", timeout=45)
    names = [p.get("name") for p in (projects or {}).get("projects", [])][:8]
    reporter.check(
        "Render /api/projects returns data",
        status == 200 and isinstance(projects, dict) and "projects" in projects,
        f"HTTP {status}, {len(names)} project(s): {', '.join(str(n) for n in names) or '(none stored yet)'}",
    )

    # CORS for the deployed frontend origin: a direct cross-origin call must be
    # allowed for this origin (the one set in CORS_ORIGINS on Render).
    status, _, headers = http_get(
        f"{render_url}/api/projects",
        headers={"Origin": cors_origin},
        timeout=45,
    )
    allowed = headers.get("Access-Control-Allow-Origin") or headers.get("access-control-allow-origin")
    reporter.check(
        f"Render allows the {cors_origin} origin (CORS)",
        status == 200 and allowed in (cors_origin, "*"),
        f"Access-Control-Allow-Origin: {allowed or '(missing)'} - set CORS_ORIGINS on Render to include {cors_origin}",
    )

    # Informational: whether a page served from localhost may call Render
    # directly. It is not required (serve_local.py proxies /api/* same-origin),
    # so this never fails the run.
    status, _, local_headers = http_get(
        f"{render_url}/api/projects",
        headers={"Origin": "http://localhost:3000"},
        timeout=45,
    )
    local_allowed = local_headers.get("Access-Control-Allow-Origin") or local_headers.get("access-control-allow-origin")
    print(
        "       info: Origin http://localhost:3000 -> Access-Control-Allow-Origin: "
        f"{local_allowed or '(not allowed)'} - add it to CORS_ORIGINS on Render if a\n"
        "             locally served page must call this API directly (serve_local.py does not need it)"
    )
    return True


# ---------------------------------------------------------------------------
# 3 + 4: the deployed frontend and its proxy to the backend
# ---------------------------------------------------------------------------

def check_frontend(vercel_url, render_url, reporter):
    status, payload = get_json(f"{vercel_url}/api/health", timeout=45)[:2]
    reporter.check(
        "Vercel /api/* rewrite reaches the backend",
        status == 200 and isinstance(payload, dict) and payload.get("status") == "healthy",
        f"HTTP {status} - rewrite target should be {render_url}/api/:path*",
    )

    status, projects, _ = get_json(f"{vercel_url}/api/projects", timeout=45)
    count = len((projects or {}).get("projects", [])) if isinstance(projects, dict) else None
    reporter.check(
        "Vercel proxies /api/projects",
        status == 200 and count is not None,
        f"HTTP {status}, {count} project(s) through the Vercel proxy",
    )

    for asset in STATIC_ASSETS:
        status, body, _ = http_get(f"{vercel_url}/{asset}", timeout=30)
        ok = status == 200 and len(body) > 0
        if asset == "index.html":
            ok = ok and "js/app.js" in body and 'type="module"' in body
        reporter.check(f"Vercel serves {asset}", ok, f"HTTP {status}")


# ---------------------------------------------------------------------------
# 5: live browser checks
# ---------------------------------------------------------------------------

def build_driver():
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.set_capability("goog:loggingPrefs", {"browser": "ALL"})
    return webdriver.Chrome(options=options)


def wait_for(driver, script, timeout=60, interval=0.25, message="condition"):
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            last = driver.execute_script(script)
        except Exception:  # noqa: BLE001 - page may still be navigating
            last = None
        if last:
            return last
        time.sleep(interval)
    raise AssertionError(f"timed out waiting for {message} (last: {last!r})")


def ui_check(driver, page_url, reporter, label):
    """Load the SPA and prove the project switcher + KPIs were really filled."""
    try:
        driver.get(page_url)
        filled = wait_for(
            driver,
            "const s = document.getElementById('project-select');"
            "if (!s || !s.options.length) return null;"
            "const o = s.options[s.selectedIndex] || s.options[0];"
            "if (!o || !o.value) return null;"
            "return { name: o.textContent.trim(),"
            " options: Array.from(s.options).map(x => x.textContent.trim()),"
            " competitors: (document.getElementById('competitors-count')||{}).textContent,"
            " posts: (document.getElementById('total-posts-count')||{}).textContent,"
            " title: (document.getElementById('dashboard-project-title')||{}).textContent };",
            timeout=60,
            message=f"{label} project dropdown to populate",
        )
        reporter.check(
            f"{label}: project dropdown populated",
            bool(filled.get("name")),
            f"selected '{filled.get('name')}' of {len(filled.get('options') or [])} project(s)",
        )

        # The dashboard fills in *after* the project list. Wait until the title
        # matches the selected project and the KPIs left their "—" placeholder,
        # so a stale/hard-coded value can never pass this check.
        try:
            values = wait_for(
                driver,
                "const s = document.getElementById('project-select');"
                "const o = s && (s.options[s.selectedIndex] || s.options[0]);"
                "const t = document.getElementById('dashboard-project-title');"
                "const name = o ? o.textContent.trim() : '';"
                "if (!name || !t) return null;"
                "if (t.textContent.trim() !== name) return null;"
                "const read = id => (document.getElementById(id)||{}).textContent.trim();"
                "return { competitors: read('competitors-count'), posts: read('total-posts-count'),"
                " sync: read('dashboard-last-sync') };",
                timeout=45,
                message=f"{label} dashboard to show the selected project",
            )
            loaded = values["competitors"] not in ("", "\u2014", "&mdash;") and values["posts"] not in ("", "\u2014", "&mdash;")
            reporter.check(
                f"{label}: dashboard shows the selected project's values",
                loaded,
                f"'{filled.get('name')}': competitors={values['competitors']} posts={values['posts']} sync={values['sync'][:40]!r}",
            )
        except AssertionError as error:
            reporter.check(f"{label}: dashboard shows the selected project's values", False, str(error))

        logs = driver.get_log("browser")
        relevant = [
            entry for entry in logs
            if not any(fragment in entry.get("message", "") for fragment in IGNORED_CONSOLE_FRAGMENTS)
        ]
        severe = [entry for entry in relevant if entry.get("level") == "SEVERE"]
        api_notes = [
            entry["message"].split("[MapCompete] API:", 1)[-1].strip()
            for entry in relevant
            if "[MapCompete] API:" in entry.get("message", "")
        ]
        reporter.check(
            f"{label}: no JavaScript errors",
            not severe,
            "; ".join(entry.get("message", "")[:200] for entry in severe[:3]) or "clean console",
        )
        if api_notes:
            print(f"       {label} auto-detected API:{api_notes[0]}")
        return True
    except Exception as error:  # noqa: BLE001 - reported as a failure
        reporter.check(f"{label}: live UI check", False, f"{type(error).__name__}: {error}")
        return False


def check_configured_links(repo_root, render_url, reporter):
    """Report/verify the backend link stored in the repo configuration.

    Nothing in .env reaches the browser (the SPA is static and has no build
    step), so the links that actually matter are:
      * frontend/vercel.json  -> production rewrite target (must match Render)
      * serve_local.py + .env -> local proxy target
    """
    vercel_json = Path(repo_root) / "frontend" / "vercel.json"
    try:
        config = json.loads(vercel_json.read_text(encoding="utf-8"))
        destination = config["rewrites"][0]["destination"]
    except Exception as error:  # noqa: BLE001
        reporter.check("frontend/vercel.json has a rewrite target", False, f"{type(error).__name__}: {error}")
        return
    expected_host = urlparse(render_url).netloc
    actual_host = urlparse(destination.replace(":path*", "")).netloc
    reporter.check(
        "frontend/vercel.json rewrite points at the deployed backend",
        actual_host == expected_host,
        f"destination {destination} (expected host {expected_host})",
    )

    env_link = os.environ.get("API_BASE_URL")
    env_files = [Path(repo_root) / ".env", Path(repo_root) / ".env.example"]
    file_links = []
    for path in env_files:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line.startswith("API_BASE_URL=") and line.split("=", 1)[1].strip():
                file_links.append(f"{path.name}: {line.split('=', 1)[1].strip()}")
    print(
        "       info: backend link sources - vercel.json rewrite (production), "
        "serve_local.py --api / API_BASE_URL (local proxy)\n"
        f"             environment API_BASE_URL: {env_link or '(not set)'}"
        + (f" | {', '.join(file_links)}" if file_links else "")
    )


def main():
    parser = argparse.ArgumentParser(
        description="Verify frontend <-> backend wiring (Vercel + Render + localhost).")
    parser.add_argument("--render-url", default=DEFAULT_RENDER_URL, help="Backend base URL")
    parser.add_argument("--vercel-url", default=DEFAULT_VERCEL_URL, help="Frontend base URL to test")
    parser.add_argument("--cors-origin", default=DEFAULT_CORS_ORIGIN,
                        help="Origin that Render must allow in CORS_ORIGINS (default: the Vercel app)")
    parser.add_argument("--local-url", default=DEFAULT_LOCAL_URL, help="Local frontend URL")
    parser.add_argument("--repo-root", default=str(REPO_ROOT),
                        help="Repository root holding frontend/vercel.json and .env")
    parser.add_argument("--local", action="store_true",
                        help="Also verify the local frontend (implies --ui)")
    parser.add_argument("--ui", action="store_true", help="Run the headless Chrome checks")
    args = parser.parse_args()
    # Keep output flowing when stdout is redirected to a file (CI logs).
    sys.stdout.reconfigure(line_buffering=True)

    render_url = args.render_url.rstrip("/")
    vercel_url = args.vercel_url.rstrip("/")
    local_url = args.local_url.rstrip("/")
    run_ui = args.ui or args.local

    reporter = Reporter()
    print(f"Backend : {render_url}")
    print(f"Frontend: {vercel_url}")
    if args.local:
        print(f"Local   : {local_url}")
    print("-" * 72)

    backend_ok = check_backend(render_url, args.cors_origin, reporter)
    check_configured_links(args.repo_root, render_url, reporter)
    if backend_ok:
        check_frontend(vercel_url, render_url, reporter)
    else:
        reporter.skip("Vercel rewrite + static asset checks", "backend unreachable")

    if run_ui:
        try:
            driver = build_driver()
        except Exception as error:  # noqa: BLE001
            reporter.check("headless Chrome available", False, f"{type(error).__name__}: {error}")
            driver = None
        if driver:
            try:
                ui_check(driver, vercel_url, reporter, "Vercel")
                if args.local:
                    ui_check(driver, local_url, reporter, "localhost")
            finally:
                driver.quit()

    print("-" * 72)
    if reporter.failures:
        print(f"{len(reporter.failures)} check(s) FAILED: " + ", ".join(reporter.failures))
        return 1
    print("ALL DEPLOYMENT WIRING CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())

