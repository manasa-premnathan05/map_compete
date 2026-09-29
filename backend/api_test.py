import json
import os
import sys
import urllib.error
import urllib.request

sys.stdout.reconfigure(encoding="utf-8")

API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "http://127.0.0.1:10000",
).rstrip("/")


def request_json(method, path, payload=None, timeout=30):
    url = f"{API_BASE_URL}{path}"

    data = None
    headers = {
        "Accept": "application/json",
    }

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            try:
                body = json.loads(raw)
            except json.JSONDecodeError:
                body = raw

            return response.status, body

    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")

        try:
            body = json.loads(raw)
        except json.JSONDecodeError:
            body = raw

        return exc.code, body


def test_health():
    status, body = request_json("GET", "/api/health")

    assert status == 200, (
        f"Health check failed: HTTP {status}: {body}"
    )

    assert isinstance(body, dict), (
        f"Health response is not JSON object: {body}"
    )

    assert body.get("status") == "healthy", (
        f"Unexpected health status: {body}"
    )

    print("PASS: GET /api/health")


def test_diagnostics():
    status, body = request_json(
        "GET",
        "/api/places/diagnostics",
    )

    assert status == 200, (
        f"Diagnostics failed: HTTP {status}: {body}"
    )

    assert isinstance(body, dict), (
        f"Diagnostics response is not JSON object: {body}"
    )

    required_fields = [
        "selenium_available",
        "chrome_available",
        "chromedriver_available",
        "google_maps_reachable",
        "database_connected",
    ]

    for field in required_fields:
        assert field in body, (
            f"Diagnostics missing field '{field}': {body}"
        )

    print("PASS: GET /api/places/diagnostics")


def test_empty_search_validation():
    status, body = request_json(
        "POST",
        "/api/places/search",
        {
            "name": "",
            "location": "Navi Mumbai",
        },
    )

    assert status == 400, (
        f"Expected HTTP 400 for empty name, got {status}: {body}"
    )

    print("PASS: POST /api/places/search validation")


def test_missing_location_validation():
    status, body = request_json(
        "POST",
        "/api/places/search",
        {
            "name": "McDonald's",
        },
    )

    assert status == 400, (
        f"Expected HTTP 400 for missing location, got {status}: {body}"
    )

    print("PASS: POST /api/places/search location validation")


def test_live_search():
    """
    Optional live Google Maps test.

    Run explicitly with:

        RUN_LIVE_MAPS_TEST=1 python backend/api_test.py

    This test launches Selenium and contacts Google Maps.
    It is intentionally disabled by default.
    """

    if os.environ.get("RUN_LIVE_MAPS_TEST") != "1":
        print(
            "SKIP: live Google Maps search "
            "(set RUN_LIVE_MAPS_TEST=1 to enable)"
        )
        return

    status, body = request_json(
        "POST",
        "/api/places/search",
        {
            "name": "McDonald's",
            "location": "Navi Mumbai",
            "max_results": 5,
        },
        timeout=120,
    )

    print(
        "LIVE SEARCH RESPONSE:",
        json.dumps(body, indent=2, ensure_ascii=False),
    )

    assert status in {
    200,
    422,
    429,
    502,
    503,
    504,
}, (
        f"Unexpected live-search HTTP status {status}: {body}"
    )

    if status == 200:
        assert isinstance(body, dict)
        assert body.get("state") in {
            "RESULTS",
            "NO_RESULTS",
        }, (
            f"Unexpected successful search state: {body}"
        )

        if body.get("state") == "RESULTS":
            assert isinstance(body.get("results"), list)
            assert body.get("count") == len(body["results"])

    else:
        assert isinstance(body, dict), (
            f"Error response should be JSON: {body}"
        )

        assert (
            body.get("error_type")
            or body.get("state")
            or body.get("error")
        ), (
            f"Search failure contains no diagnostic information: {body}"
        )

    print("PASS: live Google Maps search contract")


def main():
    print("=" * 60)
    print("MAP COMPETE API CONTRACT TESTS")
    print("=" * 60)
    print(f"API_BASE_URL = {API_BASE_URL}")
    print()

    tests = [
        test_health,
        test_diagnostics,
        test_empty_search_validation,
        test_missing_location_validation,
        test_live_search,
    ]

    failures = []

    for test in tests:
        try:
            test()
        except Exception as exc:
            failures.append((test.__name__, exc))
            print(f"FAIL: {test.__name__}: {exc}")

    print()
    print("=" * 60)

    if failures:
        print(f"FAILED: {len(failures)} test(s)")
        for name, error in failures:
            print(f" - {name}: {error}")
        print("=" * 60)
        sys.exit(1)

    print("ALL API CONTRACT TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()