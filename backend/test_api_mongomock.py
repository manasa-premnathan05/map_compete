"""Flask API integration tests against the MongoDB layer (no server needed).

Imports the real ``api`` app, swaps its DatabaseManager for an in-memory
mongomock client and exercises the HTTP contracts end to end through
``Flask.test_client()``:

    pip install mongomock          # test-only dependency
    python backend/test_api_mongomock.py

Validates that every API route still speaks the ORIGINAL contract (paths,
JSON shapes, numeric ids) after the SQLite -> MongoDB migration. The one
environment-dependent test (real Atlas) is test_mongodb.py.
"""

import os
import sys

try:
    import mongomock
except ImportError:
    print("mongomock is not installed - run: pip install mongomock")
    sys.exit(2)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import the app WITHOUT a real MongoDB (constructor must not crash).
os.environ.pop("MONGODB_URI", None)
import api  # noqa: E402
from database import DatabaseManager  # noqa: E402

FAILURES = []


def check(label, condition, detail=""):
    if condition:
        print(f"  [ok] {label}")
    else:
        print(f"  [FAIL] {label} {detail}")
        FAILURES.append(label)


def fresh_client():
    """App wired to a brand-new empty in-memory database."""
    api.db = DatabaseManager(uri="mongodb://test", database="api_test",
                             client=mongomock.MongoClient())
    api.app.config["TESTING"] = True
    return api.app.test_client()


def test_health_and_unavailable():
    print("\n== /api/health ==")
    client = fresh_client()
    res = client.get("/api/health")
    body = res.get_json()
    check("healthy with database", res.status_code == 200
          and body["status"] == "healthy" and body["database"] == "connected",
          str(body))
    check("no credentials leaked",
          "mongodb" not in str(body).lower() and "@" not in str(body))

    api.db = DatabaseManager(uri="", client=None)  # unconfigured
    res = client.get("/api/health")
    body = res.get_json()
    check("missing URI -> 503 degraded", res.status_code == 503
          and body["database"] == "disconnected", str(body))
    check("clear configuration message",
          "MONGODB_URI" in body.get("database_error", ""), str(body))

    # Data endpoints must also fail cleanly (503 via the error handler).
    res = client.get("/api/projects")
    check("data endpoint 503 when DB missing", res.status_code == 503,
          str(res.status_code))
    check("error body has no traceback",
          "Traceback" not in res.get_data(as_text=True))


def test_project_crud_routes():
    print("\n== projects routes ==")
    client = fresh_client()

    res = client.get("/api/projects")
    check("GET /api/projects empty", res.status_code == 200
          and res.get_json()["projects"] == [])

    res = client.post("/api/projects", json={"name": "Route Test Co",
                                             "location": "Mumbai",
                                             "field": "Cafe"})
    body = res.get_json()
    # Create endpoints return 201 Created (original contract).
    check("POST /api/projects 201", res.status_code == 201, str(body)[:300])
    project = body.get("project") or {}
    pid = project.get("id") or body.get("project_id")
    check("project id returned as int", isinstance(pid, int), str(body)[:200])

    res = client.get(f"/api/projects/{pid}")
    check("GET project", res.status_code == 200
          and res.get_json()["project"]["name"] == "Route Test Co")

    res = client.put(f"/api/projects/{pid}", json={"name": "Route Test Renamed"})
    check("PUT project", res.status_code == 200, str(res.get_json())[:200])
    check("rename persisted",
          client.get(f"/api/projects/{pid}").get_json()["project"]["name"]
          == "Route Test Renamed")

    res = client.delete(f"/api/projects/{pid}")
    check("DELETE project", res.status_code == 200, str(res.get_json())[:200])
    check("project gone after delete",
          not client.get(f"/api/projects/{pid}").get_json().get("project"))


def test_competitor_post_routes():
    print("\n== competitor / post / analytics routes ==")
    client = fresh_client()
    pid = client.post("/api/projects", json={"name": "Scrape Fake Co"}).get_json()[
        "project"]["id"]

    res = client.post(f"/api/projects/{pid}/competitors",
                      json={"name": "Rival A",
                            "gmap_url": "https://maps.google.com/?cid=4242"})
    body = res.get_json()
    check("POST competitor 201", res.status_code == 201 and body.get("competitor"),
          str(body)[:300])
    cid = body["competitor"]["id"]

    res = client.get(f"/api/projects/{pid}/competitors")
    check("GET competitors list", res.status_code == 200
          and len(res.get_json()["competitors"]) == 1)

    res = client.get(f"/api/competitors/{cid}")
    check("GET single competitor", res.status_code == 200
          and res.get_json()["competitor"]["name"] == "Rival A")

    res = client.put(f"/api/competitors/{cid}", json={"name": "Rival A Updated"})
    check("PUT competitor", res.status_code == 200
          and res.get_json()["competitor"]["name"] == "Rival A Updated")

    # Posts (stored through the db layer to simulate a scrape save)
    api.db.add_post(cid, {"post_url": "https://maps.google.com/p/1",
                          "text_content": "Espresso week at Route Test!",
                          "published_date": "2026-08-01 10:00:00",
                          "detected_topic": "Coffee",
                          "detected_keywords": ["espresso"]})
    res = client.get(f"/api/posts?project_id={pid}")
    body = res.get_json()
    check("GET /api/posts", res.status_code == 200 and body["count"] == 1,
          str(body)[:300])
    check("post contract keys",
          {"posts", "count", "owner_posts", "public_posts"} <= set(body))
    check("post JSON fields intact",
          body["posts"][0]["image_urls"] == []
          and body["posts"][0]["detected_keywords"] == ["espresso"])

    res = client.get(f"/api/projects/{pid}/analytics/topics")
    check("topics route", res.status_code == 200
          and res.get_json()["topics"][0]["detected_topic"] == "Coffee")
    res = client.get(f"/api/projects/{pid}/analytics/keywords")
    check("keywords route", res.status_code == 200)
    res = client.get(f"/api/projects/{pid}/market-overview")
    check("market-overview route", res.status_code == 200
          and res.get_json()["competitor_count"] == 1)
    res = client.get(f"/api/projects/{pid}/trend-analysis")
    check("trend-analysis route", res.status_code == 200
          and res.get_json()["total_posts"] == 1)
    res = client.get(f"/api/projects/{pid}/scraping-stats")
    check("scraping-stats route", res.status_code == 200
          and res.get_json()["competitors_count"] == 1)
    res = client.get(f"/api/projects/{pid}/scraping-logs")
    check("scraping-logs route", res.status_code == 200
          and res.get_json()["logs"] == [] and "stats" in res.get_json())
    original_stats = api.db.get_scraping_stats
    def unexpected_stats(*args, **kwargs):
        raise AssertionError("logs-only reads must not recompute statistics")
    api.db.get_scraping_stats = unexpected_stats
    try:
        res = client.get(f"/api/projects/{pid}/scraping-logs?include_stats=0")
        check("logs-only skips statistics", res.status_code == 200
              and res.get_json()["logs"] == [] and "stats" not in res.get_json())
    finally:
        api.db.get_scraping_stats = original_stats
    res = client.get(f"/api/projects/{pid}/market-gaps")
    check("market-gaps route", res.status_code == 200)
    res = client.get(f"/api/projects/{pid}/reviews")
    check("reviews route", res.status_code == 200)

    res = client.get(f"/api/projects/{pid}/generated-ideas")
    check("generated-ideas route", res.status_code == 200
          and "ideas" in res.get_json())

    res = client.delete(f"/api/competitors/{cid}")
    check("DELETE competitor", res.status_code == 200)
    check("posts removed with competitor",
          client.get(f"/api/posts?project_id={pid}").get_json()["count"] == 0)
    client.delete(f"/api/projects/{pid}")


def test_browser_admission():
    print("\n== browser memory admission ==")
    client = fresh_client()
    api._browser_operation_lock.acquire()
    try:
        for path in ('/api/places/search', '/api/places/resolve',
                     '/api/projects/1/discover-competitors',
                     '/api/projects/1/scrape', '/api/competitors/1/scrape'):
            res = client.post(path, json={})
            check(f"busy browser rejected: {path}", res.status_code == 429
                  and res.get_json()['error_type'] == 'SCRAPER_BUSY')
        res = client.get('/api/places/diagnostics?probe=1')
        check("browser probe respects admission", res.status_code == 429)
        check("reads remain available during scrape", client.get('/api/projects').status_code == 200)
    finally:
        api._browser_operation_lock.release()
    res = client.post('/api/places/search', json={})
    check("validation returns normally after browser released", res.status_code == 400)
    acquired = api._browser_operation_lock.acquire(blocking=False)
    check("request teardown releases browser admission", acquired)
    if acquired:
        api._browser_operation_lock.release()


if __name__ == "__main__":
    test_health_and_unavailable()
    test_project_crud_routes()
    test_competitor_post_routes()
    test_browser_admission()

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"{len(FAILURES)} FAILED: {FAILURES}")
        sys.exit(1)
    print("ALL API INTEGRATION TESTS PASSED")
    sys.exit(0)

