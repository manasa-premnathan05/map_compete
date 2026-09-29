"""Real Google Maps diagnostic for competitor discovery.

Runs the exact scraper path used by ``POST /api/places/search`` against live
Google Maps using the production Selenium/Chromium configuration, and prints the
structured page state plus extraction counters. It never touches the database
and never creates a competitor - its only purpose is to answer "can this server
actually read Google Maps right now?".

Usage:
    python backend/test_places_diagnostics.py
    python backend/test_places_diagnostics.py "Starbucks" "Kharghar"
    python backend/test_places_diagnostics.py --resolve "McDonald's" "nexus seawoods"

Exit code 0 = Google Maps was read successfully (RESULTS or a confirmed
NO_RESULTS); 1 = the page could not be read (CAPTCHA / BLOCKED / TIMEOUT /
BROWSER_ERROR / SELECTOR_FAILURE ...).
"""

import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

# Business names and addresses are frequently non-Latin; make the console output
# safe on Windows (cp1252) the same way Linux/Render logs already are.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):  # pragma: no cover - older interpreters
        pass

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency at runtime
    load_dotenv = None

if load_dotenv:
    load_dotenv()
    for candidate in (os.path.join(_HERE, '..', '.env'), os.path.join(_HERE, '.env')):
        if os.path.exists(candidate):
            load_dotenv(candidate)

from scraper import GoogleMapsScraper  # noqa: E402


def print_search_outcome(outcome: dict) -> int:
    diagnostics = outcome.get('diagnostics') or {}
    state = outcome.get('state')
    print('state:', state)
    print('results:', outcome.get('count'))
    print('message:', outcome.get('message'))
    print('duration:', diagnostics.get('duration_seconds'), 's')
    print('current_url:', diagnostics.get('current_url'))
    print('title:', diagnostics.get('title'))
    print('result_containers_found:', diagnostics.get('result_containers_found'))
    print('place_links_found:', diagnostics.get('place_links_found'))
    print('redirected_to_profile:', diagnostics.get('redirected_to_profile'))
    print('strategies_tried:', json.dumps(diagnostics.get('strategies_tried')))
    print('driver_started:', diagnostics.get('driver_started'))
    print('error:', diagnostics.get('error'))
    for index, result in enumerate(outcome.get('results') or [], start=1):
        print(f'  [{index}] {result.get("name")!r} rating={result.get("rating")} '
              f'reviews={result.get("review_count")} category={result.get("category")!r}')
        print(f'      address={result.get("address")!r}')
        print(f'      url={result.get("google_maps_url")}')
        print(f'      place_id={result.get("google_place_id")} cid={result.get("cid")} '
              f'hex={result.get("hex_id")} source={result.get("identity_source")}')

    if state == 'RESULTS':
        print('\nDIAGNOSTIC: PASS (Google Maps loaded and results were extracted)')
        return 0
    if state == 'NO_RESULTS':
        print('\nDIAGNOSTIC: PASS (Google Maps loaded; it genuinely has no matches)')
        return 0
    print(f'\nDIAGNOSTIC: FAIL (state={state} - Google Maps could not be read)')
    return 1


def main() -> int:
    arguments = sys.argv[1:]
    mode = 'search'
    if arguments and arguments[0] == '--resolve':
        mode = 'resolve'
        arguments = arguments[1:]
    query = arguments[0] if arguments else "McDonald's"
    location = arguments[1] if len(arguments) > 1 else 'nexus seawoods'

    print(f'Google Maps diagnostic: mode={mode} query={query!r} location={location!r}')
    scraper = GoogleMapsScraper(headless=True)

    if mode == 'resolve':
        outcome = scraper.resolve_place_identity(query, location=location)
        print('found:', outcome.get('found'))
        print('state:', outcome.get('state'))
        print('message:', outcome.get('message'))
        print('name:', outcome.get('name'))
        print('address:', outcome.get('address'))
        print('google_maps_url:', outcome.get('google_maps_url'))
        print('place_key:', outcome.get('place_key'))
        if outcome.get('found'):
            print('\nDIAGNOSTIC: PASS (business profile resolved)')
            return 0
        if outcome.get('state') == 'NO_RESULTS':
            print('\nDIAGNOSTIC: PASS (Google Maps has no such business)')
            return 0
        print(f"\nDIAGNOSTIC: FAIL (state={outcome.get('state')})")
        return 1

    return print_search_outcome(scraper.search_google_maps_places(query, location))


if __name__ == '__main__':
    raise SystemExit(main())
