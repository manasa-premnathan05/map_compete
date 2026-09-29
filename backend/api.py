import os
import json
import re
import logging
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS

# Load environment variables from .env file
load_dotenv()
_root_env = Path(__file__).resolve().parent.parent / '.env'
if _root_env.exists():
    load_dotenv(_root_env)
_backend_env = Path(__file__).resolve().parent / '.env'
if _backend_env.exists():
    load_dotenv(_backend_env)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _scrape_log_file(filename: str):
    """Persistent file logger for scraping runs/errors (requirement 21).

    Error information is written to log files on disk so a failed scrape can be
    diagnosed later without touching any other application data.
    """
    log_dir = Path(__file__).resolve().parent / 'logs'
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except OSError:  # pragma: no cover - read-only filesystem fallback
        return None
    file_logger = logging.getLogger(f'scraping.{filename}')
    if not file_logger.handlers:
        handler = logging.FileHandler(log_dir / filename, encoding='utf-8')
        handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
        file_logger.addHandler(handler)
        file_logger.setLevel(logging.INFO)
        file_logger.propagate = False
    return file_logger


scrape_run_logger = _scrape_log_file('scraping_runs.log')
scrape_error_logger = _scrape_log_file('scraping_errors.log')


def _bool_arg(name: str, default: bool = True) -> bool:
    """Read a query-string flag such as `include_public=false`."""
    value = request.args.get(name)
    if value is None:
        return default
    return str(value).strip().lower() not in ('0', 'false', 'no', 'off')


from database import DatabaseManager, DatabaseUnavailableError
from scraper import GoogleMapsScraper
from ai_service import AIServiceManager
from topic_classifier import classify_sentiment, infer_industry

app = Flask(__name__)
# CORS for the frontend. Default "*" keeps local dev (localhost:3000 -> :5000)
# working out of the box. For production restrict to your Vercel domain:
#   CORS_ORIGINS=https://your-app.vercel.app
# (comma separated for several origins).
_cors_origins = [
    origin.strip()
    for origin in os.environ.get("CORS_ORIGINS", "*").split(",")
    if origin.strip()
]
CORS(app, resources={r"/api/*": {"origins": _cors_origins}})  # Enable CORS for frontend communication

# Initialize components.
# MongoDB Atlas connection: MONGODB_URI (mongodb+srv://...) and optional
# MONGODB_DATABASE (default "competitor_intelligence") come from the
# environment / .env - credentials are never hardcoded or logged.
db = DatabaseManager()
ai_service = AIServiceManager()


@app.errorhandler(DatabaseUnavailableError)
def _handle_database_unavailable(exc):
    """MongoDB missing/unreachable -> clear 503, no credentials exposed."""
    logger.error("Database unavailable: %s", exc)
    return jsonify({"error": str(exc)}), 503


@app.before_request
def _require_database():
    """Central guard: data endpoints fail fast with 503 when MongoDB is not
    configured/connected (routes' broad excepts would otherwise report 500).
    /api/health always answers so orchestrators can see the real state."""
    if request.path == "/api/health" or not request.path.startswith("/api/"):
        return None
    if not db.available():
        message = db._last_error or "MongoDB is not available."
        logger.error("Request rejected, database unavailable: %s", message)
        return jsonify({"error": message}), 503
    return None



def looks_like_place_card(text: str) -> bool:
    """True for Google Maps *place suggestion* cards, never for a review.

    A card contains the rating-and-count summary of a business
    ("Brevé Bakery4.0(826) · ₹400–1,000Cafe · ...") or menu/status labels
    like "Dine-in · Takeaway". They are not customer reviews and must never
    be stored as one.
    """
    if not text:
        return False
    if re.search(r'\d\.\d\(', text):
        return True
    for marker in ('Dine-in', 'Takeaway', 'No-contact delivery', 'Drive-through',
                   'On-site services', 'Temporarily closed', 'Opens ', 'Closes '):
        if marker in text:
            return True
    return False


def persist_scraped_reviews(project_id: int, competitor_id: int, posts: list) -> int:
    """Store scraped public content that is actually a Google Maps review.

    The scraper tags user generated content as ``post_source='public'``; those
    records carry the reviewer name, relative date and star rating. Persisting
    them in the ``reviews`` table is what makes the review-intelligence charts
    (rating distribution, review volume, topic ranking) show real scraped
    values instead of demo data.

    Reviews without a parsed date or that look like a place-suggestion card
    are skipped: those belong to a Google Maps results list, not to this
    competitor.
    """
    saved = 0
    for post in posts or []:
        if (post or {}).get('post_source') != 'public':
            continue
        text = (post.get('text_content') or '').strip()
        if not text:
            continue
        if not post.get('published_date'):
            continue
        if looks_like_place_card(text):
            continue
        raw = post.get('raw_data') or {}
        if not isinstance(raw, dict):
            raw = {}
        rating = post.get('rating')
        if rating is None:
            rating = raw.get('rating')
        try:
            rating = int(rating) if rating is not None else None
        except (TypeError, ValueError):
            rating = None

        sentiment, score = classify_sentiment(text, rating)
        review_id = db.add_review(project_id, competitor_id, {
            'author': raw.get('author'),
            'rating': rating,
            'relative_date': raw.get('relative_date'),
            'review_date': post.get('published_date'),
            'text_content': text,
            'sentiment': sentiment,
            'sentiment_score': score,
            'detected_topic': post.get('detected_topic'),
            'detected_keywords': post.get('detected_keywords'),
            'source_url': post.get('post_url'),
        })
        if review_id:
            saved += 1
    return saved


def persist_competitor_profile(competitor_id: int, profile: dict) -> bool:
    """Save the Google Maps listing statistics captured during a scrape."""
    if not profile:
        return False
    return db.update_competitor_stats(
        competitor_id,
        rating=profile.get('rating'),
        review_count=profile.get('review_count'),
        address=profile.get('address'),
        category=profile.get('category'),
        rating_distribution=profile.get('rating_distribution'),
        last_scraped=datetime.now(),
    )


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint: Flask liveness + MongoDB connectivity.

    Never exposes credentials or the connection string. Returns HTTP 503
    when the database is not configured or unreachable so orchestrators
    (Render) can see the problem.
    """
    db_health = db.health()
    payload = {
        "status": "healthy" if db_health["ok"] else "degraded",
        "database": "connected" if db_health["ok"] else "disconnected",
        "timestamp": datetime.now().isoformat(),
    }
    if not db_health["ok"] and db_health.get("error"):
        payload["database_error"] = db_health["error"]
    return jsonify(payload), (200 if db_health["ok"] else 503)

# Project endpoints
@app.route('/api/projects', methods=['GET'])
def get_projects():
    """Get all projects"""
    try:
        projects = db.get_projects()
        return jsonify({"projects": projects})
    except Exception as e:
        logger.error(f"Error getting projects: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects', methods=['POST'])
def create_project():
    """Create a new project and automatically run competitor checking on Google Maps"""
    try:
        data = request.get_json() or {}
        name = data.get('name')
        our_profile = data.get('our_profile')
        location = data.get('location')
        field = data.get('field')
        is_online = bool(data.get('is_online', False))
        auto_discover = bool(data.get('auto_discover', True))
        gmap_url = data.get('gmap_url') or data.get('google_maps_url')
        place_key = data.get('place_key')
        google_place_id = data.get('google_place_id')
        cid = data.get('cid')

        if not name:
            return jsonify({"error": "Project name is required"}), 400

        project_id = db.create_project(
            name, our_profile, location, field, is_online, gmap_url=gmap_url
        )
        # Register the project's own business under the same canonical identity
        # used for competitors (a shared name/place id resolves to one row).
        own_place = db.link_project_place(
            project_id, name=name, gmap_url=gmap_url,
            address=location or our_profile, place_key=place_key,
            google_place_id=google_place_id, cid=cid,
        )
        project = db.get_project(project_id)
        already_existed = db.project_name_exists(name, exclude_id=project_id)

        # Automatic Competitor Checking on Google Maps upon Project Creation
        auto_competitors = []
        if auto_discover:
            try:
                # Use location and field for discovery if provided, otherwise fall back to our_profile
                loc = location or our_profile or "Local Area"
                disc_res = ai_service.discover_local_competitors(
                    query=name,
                    location=loc,
                    field=field,
                    is_online=is_online
                )
                auto_competitors = disc_res.get('competitors', [])
            except Exception as e:
                logger.warning(f"Auto competitor check warning: {e}")

        return jsonify({
            "project": project,
            "own_place": own_place,
            "auto_discovered_competitors": auto_competitors
        }), 201
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/places/autocomplete', methods=['GET'])
def autocomplete_places():
    """Live Google Maps search suggestions when user types in search box"""
    try:
        q = request.args.get('q', '').strip()
        location = request.args.get('location', '').strip()
        if not q or len(q) < 2:
            return jsonify({"results": []})

        res = ai_service.discover_local_competitors(query=q, location=location)
        suggestions = []
        for comp in res.get('competitors', [])[:5]:
            identity = db.resolve_place_identity(
                name=comp.get('name'),
                gmap_url=comp.get('google_maps_url'),
                address=comp.get('address'),
            )
            suggestions.append({
                "name": comp.get('name'),
                "address": comp.get('address'),
                "category": comp.get('category'),
                "rating": comp.get('rating'),
                "google_maps_url": comp.get('google_maps_url'),
                "place_key": identity['place_key'],
                "identity_source": identity['identity_source'],
                "google_place_id": identity['google_place_id'],
                "hex_id": identity['hex_id'],
                "cid": identity['cid'],
            })

        return jsonify({"query": q, "results": suggestions})
    except Exception as e:
        logger.error(f"Error in places autocomplete: {e}")
        return jsonify({"results": []})

@app.route('/api/places', methods=['GET'])
def list_places():
    """Search the canonical businesses known to the system."""
    try:
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 50) or 50), 200)
        places = db.get_places(query=query, limit=limit)
        return jsonify({"query": query, "count": len(places), "places": places})
    except Exception as e:
        logger.error(f"Error listing places: {e}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------------------------
# Google Maps discovery diagnostics (safe / credential-free)
# ---------------------------------------------------------------------------
# Last observed scraper state per flow, surfaced by /api/places/diagnostics so a
# production failure can be identified without server log access.
_LAST_PLACE_DIAGNOSTICS = {}

# Scraper state -> (HTTP status, error_type, default message). Anything that is
# not RESULTS/NO_RESULTS means "we could not read Google Maps", which must never
# be answered with an empty-but-successful result set.
_STATE_HTTP = {
    'CAPTCHA': (429, 'CAPTCHA',
                'Google Maps presented an anti-automation challenge.'),
    'BLOCKED': (503, 'BLOCKED',
                'Google Maps blocked this automated request.'),
    'CONSENT': (503, 'CONSENT',
                'Google Maps is waiting for a consent decision.'),
    'TIMEOUT': (504, 'TIMEOUT',
                'Google Maps did not finish loading in time.'),
    'BROWSER_ERROR': (503, 'BROWSER_ERROR',
                      'Google Maps could not be loaded by the server.'),
    'SELECTOR_FAILURE': (502, 'SELECTOR_FAILURE',
                         'Google Maps loaded but the result structure could not be '
                         'identified.'),
    'ERROR': (502, 'ERROR',
              'Google Maps could not be read by the server.'),
    'PLACE_PROFILE': (422, 'PLACE_PROFILE',
                      'Google Maps opened a single business profile instead of a '
                      'result list.'),
    'UNKNOWN': (502, 'UNKNOWN',
                'Google Maps served an unrecognised page.'),
}


def _place_failure_response(state, message=None):
    """HTTP status + error_type + message for a failed Google Maps read."""
    status_code, error_type, default = _STATE_HTTP.get(state or 'UNKNOWN',
                                                       _STATE_HTTP['UNKNOWN'])
    return status_code, error_type, message or default


def _safe_search_diagnostics(diagnostics):
    """Trim scraper diagnostics to safe, non-sensitive fields."""
    if not isinstance(diagnostics, dict):
        return {}
    allowed = ('query', 'location', 'current_url', 'title',
               'result_containers_found', 'place_links_found', 'strategies_tried',
               'scrolls', 'driver_started', 'duration_seconds', 'error_type', 'error')
    return {key: diagnostics.get(key) for key in allowed if key in diagnostics}


def _remember_place_diagnostics(flow, state, count, diagnostics=None):
    """Remember the last Google Maps read per flow (used by the diagnostics route)."""
    _LAST_PLACE_DIAGNOSTICS[flow] = {
        'state': state,
        'results': count,
        'at': datetime.now().isoformat(timespec='seconds'),
        'duration_seconds': (diagnostics or {}).get('duration_seconds'),
        'title': (diagnostics or {}).get('title'),
    }


def _google_maps_reachable(timeout=6.0):
    """Cheap reachability probe for Google Maps (no browser, no credentials)."""
    import urllib.error
    import urllib.request

    request = urllib.request.Request(
        'https://www.google.com/maps?hl=en',
        headers={'User-Agent': 'Mozilla/5.0 (compatible; MapCompete diagnostics)'},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return (200 <= response.status < 400), 'HTTP %s' % response.status
    except urllib.error.HTTPError as exc:
        return False, 'HTTP %s' % exc.code
    except Exception as exc:  # network / DNS / TLS problem
        return False, type(exc).__name__


@app.route('/api/places/resolve', methods=['POST'])
def resolve_place():
    """Resolve a typed business name to its real Google Maps listing.

    Pass "live": true to run a real Google Maps lookup (slower, needs Chrome)
    so a hand-typed competitor can be promoted onto its canonical identity.
    """
    try:
        data = request.get_json() or {}
        query = (data.get('name') or data.get('query') or '').strip()
        location = (data.get('location') or '').strip() or None
        if not query:
            return jsonify({"error": "A business name is required"}), 400

        # Fast path: a URL or an id handed over by discovery resolves instantly.
        identity = db.resolve_place_identity(
            name=query,
            gmap_url=data.get('google_maps_url') or data.get('gmap_url'),
            address=data.get('address'),
            google_place_id=data.get('google_place_id'),
            cid=data.get('cid'),
            hex_id=data.get('hex_id'),
            place_key=data.get('place_key'),
        )
        if identity['place_key'] and identity['is_strong']:
            return jsonify({"found": True, "live": False, "identity": identity})

        if not data.get('live'):
            return jsonify({
                "found": bool(identity['place_key']),
                "live": False,
                "identity": identity,
                "message": "Pass live=true to look this name up on Google Maps",
            })

        scraper = GoogleMapsScraper(headless=True)
        live = scraper.resolve_place_identity(query, location=location)
        live_state = (live.get('state') or 'UNKNOWN') if isinstance(live, dict) else 'UNKNOWN'
        _remember_place_diagnostics('resolve', live_state, 1 if live.get('found') else 0)
        if live.get('found'):
            live_identity = db.resolve_place_identity(
                name=live.get('name') or query,
                gmap_url=live.get('google_maps_url'),
                address=live.get('address'),
                google_place_id=live.get('google_place_id'),
                cid=live.get('cid'),
                hex_id=live.get('hex_id'),
                place_key=live.get('place_key'),
            )
            return jsonify({
                "found": True,
                "live": True,
                "identity": live_identity,
                "name": live.get('name'),
                "address": live.get('address'),
                "google_maps_url": live.get('google_maps_url'),
            })
        if live_state == 'NO_RESULTS':
            return jsonify({
                "status": "no_results",
                "state": live_state,
                "error_type": "NO_RESULTS",
                "found": False,
                "live": True,
                "identity": identity,
                "message": live.get('message') or "Google Maps found no matching business.",
            }), 404

        # CAPTCHA / consent / block / timeout / selector failure: the lookup
        # never happened, so this is an error, not a "business not found".
        status_code, error_type, message = _place_failure_response(
            live_state, live.get('message'))
        logger.warning("Place resolve failed (%s) query=%r", error_type, query)
        return jsonify({
            "status": "error",
            "state": live_state,
            "error_type": error_type,
            "error": message,
            "found": False,
            "live": True,
            "identity": identity,
        }), status_code
    except Exception as e:
        logger.error(f"Error resolving place: {e}")
        return jsonify({"status": "error", "error_type": "SERVER_ERROR",
                        "error": "The Google Maps lookup could not be completed on the "
                                 "server.",
                        "found": False, "live": True}), 500


@app.route('/api/places/search', methods=['POST'])
def search_places():
    """Search for businesses by name near a location.
    
    Used when user enters a business name without URL - finds matching
    Google Maps businesses near the project's location.
    """
    try:
        data = request.get_json() or {}
        query = (data.get('name') or data.get('query') or '').strip()
        location = (data.get('location') or '').strip() or None
        try:
            max_results = int(data.get('max_results', 5) or 5)
        except (TypeError, ValueError):
            return jsonify({"error": "max_results must be an integer"}), 400
        max_results = max(1, min(max_results, 20))

        if not query:
            return jsonify({"error": "A business name is required"}), 400
        
        if not location:
            return jsonify({"error": "Location is required for nearby search"}), 400

        scraper = GoogleMapsScraper(headless=True)
        outcome = scraper.search_google_maps_places(
            query=query,
            location=location,
            max_results=max_results
        )
        state = (outcome.get('state') or 'UNKNOWN') if isinstance(outcome, dict) else 'UNKNOWN'
        results = (outcome.get('results') or []) if isinstance(outcome, dict) else list(outcome or [])
        diagnostics = _safe_search_diagnostics(
            (outcome or {}).get('diagnostics') if isinstance(outcome, dict) else {})
        _remember_place_diagnostics('search', state, len(results), diagnostics)

        if state == 'RESULTS' and results:
            return jsonify({
                "status": "success",
                "state": state,
                "query": query,
                "location": location,
                "results": results,
                "count": len(results),
                "diagnostics": diagnostics,
            })

        if state == 'NO_RESULTS':
            # Google Maps loaded successfully and really has nothing to show.
            return jsonify({
                "status": "no_results",
                "state": state,
                "query": query,
                "location": location,
                "results": [],
                "count": 0,
                "message": "No matching businesses were found on Google Maps.",
                "diagnostics": diagnostics,
            })

        # Everything else means "we could not read Google Maps": answer with a
        # non-2xx status and the real reason instead of an empty result set.
        status_code, error_type, message = _place_failure_response(
            state, (outcome or {}).get('message') if isinstance(outcome, dict) else None)
        logger.warning("Google Maps search failed (%s) query=%r location=%r",
                       error_type, query, location)
        return jsonify({
            "status": "error",
            "error_type": error_type,
            "error": message,
            "state": state,
            "query": query,
            "location": location,
            "results": [],
            "count": 0,
            "diagnostics": diagnostics,
        }), status_code
        
    except Exception as e:
        logger.error(f"Error searching places: {e}")
        body = {"status": "error", "error_type": "SERVER_ERROR",
                "error": "The search could not be completed on the server.",
                "results": [], "count": 0}
        if 'query' in locals():
            body['query'] = query
        if 'location' in locals():
            body['location'] = location
        return jsonify(body), 500


@app.route('/api/places/diagnostics', methods=['GET'])
def places_diagnostics():
    """Safe diagnostics for the Google Maps scraping stack.

    Reports availability and the last observed scraper state only - never
    environment variables, credentials, paths or headers.
    """
    import shutil

    chrome_path = os.environ.get('CHROME_BINARY') or os.environ.get('CHROME_PATH')
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH')

    selenium_available = True
    try:
        from selenium import webdriver as _webdriver  # noqa: F401
    except Exception:
        selenium_available = False

    chrome_available = bool(
        (chrome_path and os.path.exists(chrome_path))
        or shutil.which('google-chrome')
        or shutil.which('chromium')
        or shutil.which('chromium-browser')
        or shutil.which('chrome')
        or os.path.exists('C:/Program Files/Google/Chrome/Application/chrome.exe')
    )
    chromedriver_available = bool(
        (chromedriver_path and os.path.exists(chromedriver_path))
        or shutil.which('chromedriver')
    )

    maps_reachable, maps_reason = _google_maps_reachable()
    try:
        database_connected = bool(db.health().get('ok'))
    except Exception:
        database_connected = False

    # Which concrete binaries the driver discovery would use (basenames only -
    # never full paths or environment values).
    browser_binaries = [os.path.basename(path)
                        for path in GoogleMapsScraper._candidate_browser_binaries()]
    driver_binaries = [os.path.basename(path)
                       for path in GoogleMapsScraper._candidate_driver_paths()]

    # Optional ?probe=1: actually start and close a browser. Answers "can this
    # server launch a browser right now?" without touching Google Maps or the DB.
    probe_ok = None
    probe_error = None
    if request.args.get('probe') == '1':
        probe = GoogleMapsScraper(headless=True)
        try:
            probe.setup_driver()
            probe_ok = True
        except Exception as exc:
            probe_ok = False
            probe_error = '%s: %s' % (type(exc).__name__, str(exc)[:300])
        finally:
            try:
                probe.close_driver()
            except Exception:
                pass

    last_search = _LAST_PLACE_DIAGNOSTICS.get('search')
    return jsonify({
        "selenium_available": selenium_available,
        "chrome_available": chrome_available or bool(browser_binaries),
        "chrome_binaries": browser_binaries,
        "chromedriver_available": chromedriver_available or bool(driver_binaries),
        "chromedriver_binaries": driver_binaries,
        "chromedriver_note": (None if (chromedriver_available or driver_binaries) else
                              "Selenium resolves a matching driver automatically "
                              "when no local driver is found"),
        "google_maps_reachable": maps_reachable,
        "google_maps_reason": maps_reason,
        "browser_start_probe": probe_ok,
        "browser_start_error": probe_error,
        "last_test_state": (last_search or {}).get('state'),
        "last_search": last_search,
        "last_resolve": _LAST_PLACE_DIAGNOSTICS.get('resolve'),
        "last_discovery": _LAST_PLACE_DIAGNOSTICS.get('discover'),
        "database_connected": database_connected,
    })


@app.route('/api/places/<int:place_id>', methods=['GET'])
def get_place_detail(place_id):
    """Everything the system knows about one canonical business."""
    try:
        place = db.get_place(place_id)
        if not place:
            return jsonify({"error": "Place not found"}), 404
        return jsonify({
            "place": place,
            "projects": db.get_place_projects(place_id),
            "competitors": db.get_place_competitors(place_id),
        })
    except Exception as e:
        logger.error(f"Error getting place {place_id}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/competitors/verify', methods=['POST'])
def verify_competitor():
    """Verify a custom competitor by resolving it to a Google Maps place.
    
    This endpoint does NOT add the competitor to the project.
    It only resolves and verifies the business identity.
    """
    try:
        data = request.get_json() or {}
        name = data.get('name')
        gmap_url = data.get('gmap_url') or data.get('google_maps_url')
        address = data.get('address')
        project_id = data.get('project_id')
        
        # Optional: full search result data for better verification display
        search_result = data.get('search_result')  # {name, google_maps_url, address, category, rating, review_count, latitude, longitude, google_place_id, hex_id, cid, place_key}
        
        if not name:
            return jsonify({"error": "Business name is required"}), 400

        # Get project context for relevance check
        project = None
        if project_id:
            project = db.get_project(project_id)
        
        # Extract identity fields from search_result if available
        google_place_id = data.get('google_place_id') or (search_result and search_result.get('google_place_id'))
        cid = data.get('cid') or (search_result and search_result.get('cid'))
        hex_id = data.get('hex_id') or (search_result and search_result.get('hex_id'))
        place_key = data.get('place_key') or (search_result and search_result.get('place_key'))
        
        # Resolve the place identity
        identity = db.resolve_place_identity(
            name=name,
            gmap_url=gmap_url,
            address=address,
            google_place_id=google_place_id,
            cid=cid,
            hex_id=hex_id,
            place_key=place_key,
        )
        
        # Check if already tracked in this project
        already_tracked = False
        existing_competitor = None
        if project and identity['place_key'] and identity['is_strong']:
            place = db.get_place_by_key(identity['place_key'])
            if place:
                competitors = db.get_competitors(project['id'])
                existing_competitor = next((c for c in competitors if c.get('place_id') == place['id']), None)
                already_tracked = existing_competitor is not None

        # Use search result data if available for better display
        display_name = search_result.get('name') if search_result else (identity.get('name') or name)
        display_address = search_result.get('address') if search_result else identity.get('address')
        display_category = search_result.get('category') if search_result else identity.get('category')
        display_rating = search_result.get('rating') if search_result else identity.get('rating')
        display_review_count = search_result.get('review_count') if search_result else identity.get('review_count')
        display_google_maps_url = search_result.get('google_maps_url') if search_result else gmap_url
        display_latitude = search_result.get('latitude') if search_result else identity.get('latitude')
        display_longitude = search_result.get('longitude') if search_result else identity.get('longitude')
        display_place_id = search_result.get('google_place_id') if search_result else identity.get('google_place_id')
        
        # Determine relevance
        relevance = "Unknown"
        relevance_details = []
        distance_km = None
        
        if project:
            project_location = project.get('location') or project.get('our_profile') or ''
            project_field = project.get('field') or ''
            project_keywords = project.get('keywords') or []
            
            # Calculate distance if both have coordinates
            if display_latitude and display_longitude:
                # Try to get project coordinates (from its own place if available)
                proj_place = db.get_project_place(project['id'])
                if proj_place and proj_place.get('latitude') and proj_place.get('longitude'):
                    distance_km = haversine_distance(
                        proj_place['latitude'], proj_place['longitude'],
                        display_latitude, display_longitude
                    )
                    relevance_details.append(f"Distance from project: {distance_km:.1f} km")
                elif project_location:
                    relevance_details.append(f"Project location: {project_location}")
            
            # Check category match
            if display_category and project_field:
                cat_lower = display_category.lower()
                field_lower = project_field.lower()
                if cat_lower in field_lower or field_lower in cat_lower:
                    relevance = "Relevant"
                    relevance_details.append(f"Category match: {display_category} ≈ {project_field}")
                else:
                    relevance = "Possibly Relevant"
                    relevance_details.append(f"Category: {display_category} vs Project: {project_field}")
            elif display_category:
                relevance_details.append(f"Category: {display_category}")
            
            # Check keyword overlap if available
            if project_keywords and display_category:
                cat_words = set(display_category.lower().split())
                kw_words = set(k.lower() for k in project_keywords)
                if cat_words & kw_words:
                    relevance_details.append(f"Keyword overlap: {', '.join(cat_words & kw_words)}")
        
        # If identity is not strong, downgrade relevance
        if not identity['is_strong']:
            if relevance == "Relevant":
                relevance = "Possibly Relevant"
            elif relevance == "Unknown":
                relevance = "Unable to Verify"
            relevance_details.append("Identity: Weak (name match only)")
        
        return jsonify({
            "found": bool(identity['place_key']),
            "verified": identity['is_strong'],
            "identity": identity,
            # Full display details from search result
            "display": {
                "name": display_name,
                "address": display_address,
                "category": display_category,
                "rating": display_rating,
                "review_count": display_review_count,
                "google_maps_url": display_google_maps_url,
                "place_id": display_place_id,
                "distance_km": distance_km,
            },
            "already_tracked": already_tracked,
            "existing_competitor": existing_competitor,
            "relevance": relevance,
            "relevance_details": relevance_details,
            "project_context": {
                "name": project.get('name') if project else None,
                "location": project.get('location') if project else None,
                "field": project.get('field') if project else None,
            } if project else None
        })
    except Exception as e:
        logger.error(f"Error verifying competitor: {e}")
        return jsonify({"error": str(e)}), 500


def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points in kilometers."""
    from math import radians, sin, cos, sqrt, atan2
    R = 6371  # Earth radius in km
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c


@app.route('/api/projects/<int:project_id>', methods=['GET'])
def get_project(project_id):
    """Get a specific project"""
    try:
        project = db.get_project(project_id)
        if project:
            return jsonify({"project": project})
        else:
            return jsonify({"error": "Project not found"}), 404
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['PUT'])
def update_project(project_id):
    """Update a project's company name and details.

    Every field is optional: a key that is absent from the payload is left
    untouched, while an empty string clears an optional text field. The project
    name may never be blanked out.
    """
    try:
        if not db.get_project(project_id):
            return jsonify({"error": "Project not found"}), 404

        data = request.get_json() or {}

        def optional_text(key):
            """None = leave as is, '' = clear the field."""
            if key not in data:
                return None
            value = data.get(key)
            return value.strip() if isinstance(value, str) else value

        name = optional_text('name')
        if 'name' in data and not name:
            return jsonify({"error": "Project name cannot be empty"}), 400

        is_online = data.get('is_online') if 'is_online' in data else None
        if is_online is not None:
            is_online = bool(is_online)

        db.update_project(
            project_id,
            name=name,
            our_profile=optional_text('our_profile'),
            location=optional_text('location'),
            field=optional_text('field'),
            is_online=is_online,
            gmap_url=optional_text('gmap_url') or optional_text('google_maps_url'),
        )
        project = db.get_project(project_id)
        return jsonify({"project": project})
    except Exception as e:
        logger.error(f"Error updating project: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>', methods=['DELETE'])
def delete_project(project_id):
    """Delete a project and everything that belongs to it"""
    try:
        if not db.get_project(project_id):
            return jsonify({"error": "Project not found"}), 404
        db.delete_project(project_id)
        return jsonify({"message": "Project deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting project: {e}")
        return jsonify({"error": str(e)}), 500

# Competitor endpoints
@app.route('/api/projects/<int:project_id>/competitors', methods=['GET'])
def get_competitors(project_id):
    """Get competitors for a project"""
    try:
        competitors = db.get_competitors(project_id)
        return jsonify({"competitors": competitors})
    except Exception as e:
        logger.error(f"Error getting competitors: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/competitors', methods=['POST'])
def add_competitor(project_id):
    """Add a competitor and resolve it to its canonical Google Maps business."""
    try:
        data = request.get_json() or {}
        name = data.get('name')
        gmap_url = data.get('gmap_url') or data.get('google_maps_url')
        address = data.get('address')
        category = data.get('category')

        if not name:
            return jsonify({"error": "Competitor name is required"}), 400

        project = db.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # First resolve the place identity to verify it's a real Google Maps business
        identity = db.resolve_place_identity(
            name=name,
            gmap_url=gmap_url,
            address=address,
            google_place_id=data.get('google_place_id'),
            cid=data.get('cid'),
            hex_id=data.get('hex_id'),
            place_key=data.get('place_key'),
        )
        
        # Check if this place is already tracked in the project
        existing = None
        if identity['place_key'] and identity['is_strong']:
            # Check by strong identity
            place = db.get_place_by_key(identity['place_key'])
            if place:
                # Check if this project already tracks this place
                competitors = db.get_competitors(project_id)
                existing = next((c for c in competitors if c.get('place_id') == place['id']), None)
        
        if existing:
            return jsonify({
                "error": f"\"{existing['name']}\" is already tracked in this project.",
                "already_tracked": True,
                "existing_competitor": existing,
                "place": existing.get('place')
            }), 409

        competitor_id = db.add_competitor(
            project_id, name, gmap_url,
            address=address, category=category,
            place_key=data.get('place_key'),
            google_place_id=data.get('google_place_id'),
            cid=data.get('cid'),
            hex_id=data.get('hex_id'),
        )
        competitor = db.get_competitor_with_status(competitor_id) or db.get_competitor(competitor_id)
        place = (competitor or {}).get('place')
        payload = {"competitor": competitor, "place": place}
        if place:
            payload["linked_projects"] = db.get_place_projects(place["id"])
        return jsonify(payload), 201
    except Exception as e:
        logger.error(f"Error adding competitor: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/projects/<project_id>/places', methods=['GET'])
def get_project_places(project_id):
    """The canonical businesses this project tracks."""
    try:
        project_id_int = int(project_id)
        places = db.get_project_places(project_id_int)
        return jsonify({
            "project_id": project_id_int,
            "places": places,
            "own_place": db.get_project_place(project_id_int)
        })
    except Exception as e:
        logger.error(f"Error getting project places: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/discover-competitors', methods=['POST'])
def discover_project_competitors(project_id):
    """Discover competitor businesses via Google Maps based on company name, location, and industry field"""
    try:
        data = request.get_json() or {}
        project = db.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        company_name = data.get('company_name') or project.get('name')
        location = data.get('location')
        field = data.get('field')
        is_online = bool(data.get('is_online', False))

        if not company_name:
            return jsonify({"error": "Company name is required for discovery"}), 400

        # Get existing competitors to flag already tracked ones
        existing = db.get_competitors(project_id)
        existing_names = [c['name'] for c in existing]

        # Canonical identity of what the project already tracks. Two entries
        # are "the same business" when they share a Google identity (or, as a
        # fallback, when the normalised names match).
        tracked_place_keys = {
            (c.get('place_key') or '').lower() for c in existing if c.get('place_key')
        }
        own_place = db.get_project_place(project_id)
        own_place_id = (own_place or {}).get('id')
        own_place_key = (own_place or {}).get('place_key')

        # Check if live Selenium Google Maps scrape should be attempted
        live_places = []
        if not is_online:
            try:
                scraper = GoogleMapsScraper(headless=True)
                search_term = field or company_name
                loc_term = location or ""
                outcome = scraper.search_google_maps_places(
                    search_term, loc_term, max_results=5)
                live_places = (outcome.get('results') or []) if isinstance(outcome, dict) \
                    else list(outcome or [])
                logger.info("Live Google Maps scrape: state=%s places=%s",
                            (outcome or {}).get('state') if isinstance(outcome, dict) else None,
                            len(live_places))
                _remember_place_diagnostics(
                    'discover',
                    (outcome or {}).get('state') if isinstance(outcome, dict) else None,
                    len(live_places),
                    (outcome or {}).get('diagnostics') if isinstance(outcome, dict) else None)
            except Exception as ex:
                logger.warning(f"Live scrape skipped/failed: {ex}")

        # Call Smart AI Discovery as well
        discovery_result = ai_service.discover_local_competitors(
            query=company_name,
            location=location,
            field=field,
            existing_competitors=existing_names,
            is_online=is_online
        )

        # Merge live places with AI discovery
        all_competitors = []
        if live_places:
            all_competitors.extend(live_places)

        for comp in discovery_result.get('competitors', []):
            if not any(c['name'].lower().strip() == comp['name'].lower().strip() for c in all_competitors):
                all_competitors.append(comp)

        # Annotate every candidate with its canonical place identity and whether
        # this project (or any other project) already tracks that business.
        lower_existing = {c['name'].lower().strip(): c['id'] for c in existing}
        for comp in all_competitors:
            comp_name = (comp.get('name') or '').strip()
            identity = db.resolve_place_identity(
                name=comp_name,
                gmap_url=comp.get('google_maps_url') or comp.get('gmap_url'),
                address=comp.get('address'),
                google_place_id=comp.get('google_place_id'),
                cid=comp.get('cid'),
                hex_id=comp.get('hex_id'),
                place_key=comp.get('place_key'),
            )
            comp['place_key'] = identity['place_key']
            comp['identity_source'] = identity['identity_source']
            comp['google_place_id'] = identity['google_place_id']
            comp['hex_id'] = identity['hex_id']
            comp['cid'] = identity['cid']

            # 1. exact canonical match against what this project already tracks
            existing_id = None
            place_key_lower = (identity['place_key'] or '').lower()
            if place_key_lower and place_key_lower in tracked_place_keys:
                existing_id = next(
                    (c['id'] for c in existing
                     if (c.get('place_key') or '').lower() == place_key_lower),
                    None,
                )

            # 2. fuzzy name match (legacy behaviour, kept as a fallback)
            if existing_id is None:
                comp_lower = comp_name.lower()
                for ex_name, ex_id in lower_existing.items():
                    if ex_name == comp_lower or ex_name in comp_lower or comp_lower in ex_name:
                        existing_id = ex_id
                        break

            is_own_business = bool(
                (own_place_key and place_key_lower and place_key_lower == own_place_key.lower())
                or (own_place_id and comp.get('place_id') == own_place_id)
            ) or (comp_name.lower().strip() == (project.get('name') or '').lower().strip())

            comp['already_tracked'] = existing_id is not None or is_own_business
            comp['is_own_business'] = is_own_business
            if existing_id is not None:
                comp['existing_competitor_id'] = existing_id

            # How many *other* projects already track this business?
            other_projects = []
            if identity['place_key']:
                place = db.get_place_by_key(identity['place_key'])
                if place:
                    comp['place_id'] = place['id']
                    other_projects = [
                        p for p in db.get_place_projects(place['id'])
                        if p['id'] != project_id
                    ]
            comp['tracked_in_other_projects'] = [
                {"id": p['id'], "name": p['name']} for p in other_projects
            ]

        return jsonify({
            "project_id": project_id,
            "company_name": company_name,
            "is_online": is_online,
            "inferred_location": discovery_result.get('inferred_location', location or ('Nationwide / Online' if is_online else 'Local Area')),
            "inferred_field": discovery_result.get('inferred_field', field or ('E-commerce & Retail' if is_online else 'Business Services')),
            "competitors": all_competitors
        })
    except Exception as e:
        logger.error(f"Error discovering competitors: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/competitors/<int:competitor_id>', methods=['GET'])
def get_competitor(competitor_id):
    """Get a specific competitor"""
    try:
        competitor = db.get_competitor_with_status(competitor_id) or db.get_competitor(competitor_id)
        if competitor:
            return jsonify({"competitor": competitor})
        else:
            return jsonify({"error": "Competitor not found"}), 404
    except Exception as e:
        logger.error(f"Error getting competitor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/competitors/<int:competitor_id>', methods=['PUT'])
def update_competitor(competitor_id):
    """Update a competitor (re-resolving its canonical business identity)"""
    try:
        data = request.get_json() or {}
        name = data.get('name')
        gmap_url = data.get('gmap_url') or data.get('google_maps_url')
        address = data.get('address')
        category = data.get('category')

        new_id = db.update_competitor(
            competitor_id, name, gmap_url,
            address=address, category=category,
            place_key=data.get('place_key'),
            google_place_id=data.get('google_place_id'),
            cid=data.get('cid'),
            hex_id=data.get('hex_id'),
        )
        if new_id is None:
            return jsonify({"error": "Competitor not found"}), 404

        competitor = db.get_competitor_with_status(new_id) or db.get_competitor(new_id)
        return jsonify({
            "competitor": competitor,
            "place": competitor.get('place') if competitor else None,
            "merged": new_id != competitor_id,
        })
    except Exception as e:
        logger.error(f"Error updating competitor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/competitors/<int:competitor_id>', methods=['DELETE'])
def delete_competitor(competitor_id):
    """Delete a competitor"""
    try:
        db.delete_competitor(competitor_id)
        return jsonify({"message": "Competitor deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting competitor: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/competitors/<int:competitor_id>/scrape', methods=['POST'])
def scrape_single_competitor(competitor_id):
    """Scrape (or re-scrape) one competitor and record the last-scrape status."""
    try:
        competitor = db.get_competitor(competitor_id)
        if not competitor:
            return jsonify({"error": "Competitor not found"}), 404

        gmap_url = (competitor.get('gmap_url') or '').strip()
        if not gmap_url:
            return jsonify({"error": "This competitor has no Google Maps URL to scrape"}), 400

        # Check window_days parameter (default to 180 days for last 6 months)
        window_days = request.args.get('window_days', 180, type=int)
        if request.is_json:
            window_days = (request.get_json(silent=True) or {}).get('window_days', window_days)

        log_id = db.start_scraping_log(competitor['project_id'])
        posts = []
        scrape_error = None
        scrape_status = "SUCCESS"
        scraper = None
        project = db.get_project(competitor['project_id']) or {}
        industry = infer_industry(project.get('field'), project.get('our_profile'))
        try:
            scraper = GoogleMapsScraper(headless=True)
            posts = scraper.scrape_competitor_posts(
                competitor['name'], gmap_url, window_days=window_days,
                industry=industry,
                expected_address=competitor.get('address'),
            )
            try:
                scraper.close_driver()
            except Exception:
                pass
        except Exception as ex:
            error_str = str(ex)
            if "CAPTCHA_REQUIRED" in error_str:
                scrape_error = "CAPTCHA_REQUIRED: Google Maps requires manual verification"
                scrape_status = "CAPTCHA_REQUIRED"
            elif "TIMEOUT" in error_str:
                scrape_error = "TIMEOUT: Google Maps page load timed out"
                scrape_status = "TIMEOUT"
            else:
                scrape_error = f"SCRAPER_ERROR: {error_str}"
                scrape_status = "FAILED"
            logger.warning(f"Single-competitor scrape failed for {competitor['name']}: {ex}")

        # Diagnostics from the scrape run decide what may be persisted: only a
        # page verified as this business contributes posts/reviews/stats.
        diag = (getattr(scraper, 'last_run_diagnostics', {}) or {}).get(competitor['name']) or {}
        business_verified = bool(diag.get('business_verified'))

        new_posts = 0
        duplicates = 0
        cards_skipped = 0
        unverified_skipped = 0
        for post_data in posts or []:
            post_data = dict(post_data)
            post_data['competitor_name'] = competitor['name']
            # Google Maps list-page "place suggestion" cards are not posts.
            if looks_like_place_card(post_data.get('text_content')):
                cards_skipped += 1
                continue
            # Another business's content must never be stored as ours.
            if not business_verified:
                unverified_skipped += 1
                continue
            if db.add_post(competitor_id, post_data):
                new_posts += 1
            else:
                duplicates += 1  # Already collected (possibly via another project)

        # Determine final scrape status
        if scrape_status == "SUCCESS" and not scrape_error:
            if len(posts or []) == 0:
                scrape_status = "NO_POSTS"
            else:
                scrape_status = "SUCCESS"
            try:
                comp_status = db.get_competitor_with_status(competitor_id) or {}
                db.mark_competitor_scraped(competitor_id, comp_status.get('posts_collected', 0))
            except Exception as status_err:
                logger.warning(f"Could not update scrape status: {status_err}")

        images_downloaded = sum(
            len((post or {}).get('image_urls') or []) for post in (posts or [])
        )
        owner_posts = sum(1 for post in (posts or []) if (post or {}).get('post_source') != 'public')
        public_posts = sum(1 for post in (posts or []) if (post or {}).get('post_source') == 'public')

        # Persist the listing statistics + real reviews captured in this run so
        # the review charts show Google Maps values instead of demo data.
        # Reviews are only stored when the opened page was verified as this
        # business; otherwise another listing's reviews would end up here.
        place_profile = (getattr(scraper, 'last_place_profiles', {}) or {}).get(competitor['name'])
        if place_profile:
            persist_competitor_profile(competitor_id, place_profile)
        if business_verified:
            reviews_saved = persist_scraped_reviews(
                competitor['project_id'], competitor_id, posts
            )
        else:
            reviews_saved = 0

        run_detail = {
            'competitor': competitor['name'],
            'competitor_id': competitor_id,
            'gmap_url': gmap_url,
            'status': scrape_status,
            'error': scrape_error,
            'captcha_required': scrape_status == 'CAPTCHA_REQUIRED',
            'posts_found': len(posts or []),
            'new_posts': new_posts,
            'duplicates_skipped': duplicates,
            'images_downloaded': images_downloaded,
            'owner_posts': owner_posts,
            'public_posts': public_posts,
            'window_days': window_days,
            'reviews_saved': reviews_saved,
            'place_profile': place_profile,
            'business_verified': business_verified,
        }
        if cards_skipped:
            run_detail['cards_skipped'] = cards_skipped
        if unverified_skipped:
            run_detail['unverified_skipped'] = unverified_skipped
        if diag.get('place_profile_rejected'):
            run_detail['place_profile_rejected'] = diag['place_profile_rejected']

        db.update_scraping_log(
            log_id,
            end_time=datetime.now(),
            competitors_processed=1,
            posts_found=len(posts or []),
            new_posts=new_posts,
            duplicates_skipped=duplicates,
            failures=1 if scrape_error else 0,
            captcha_encountered=1 if scrape_status == "CAPTCHA_REQUIRED" else 0,
            error_info=scrape_error,
            images_downloaded=images_downloaded,
            competitor_names=json.dumps([competitor['name']]),
            details=json.dumps([run_detail]),
            status=scrape_status.lower(),
        )

        # Error information is archived in the log files (no other file touched).
        if scrape_run_logger:
            scrape_run_logger.info(
                "run_id=%s project=%s competitor=%s status=%s posts_found=%s new_posts=%s "
                "duplicates_skipped=%s images_downloaded=%s failures=%s captcha=%s",
                log_id, competitor['project_id'], competitor['name'], scrape_status,
                len(posts or []), new_posts, duplicates, images_downloaded,
                1 if scrape_error else 0, scrape_status == 'CAPTCHA_REQUIRED',
            )
        if scrape_error and scrape_error_logger:
            scrape_error_logger.error(
                "run_id=%s project=%s competitor=%s status=%s captcha=%s error=%s",
                log_id, competitor['project_id'], competitor['name'], scrape_status,
                scrape_status == 'CAPTCHA_REQUIRED', scrape_error,
            )

        # Update competitor with scrape status
        try:
            db_status = 'active' if scrape_status in ('SUCCESS', 'NO_POSTS') else scrape_status.lower()
            db.update_competitor_scrape_status(competitor_id, db_status)
        except Exception as e:
            logger.warning(f"Could not update competitor status: {e}")

        payload = {
            "competitor": db.get_competitor_with_status(competitor_id) or competitor,
            "log_id": log_id,
            "scrape_status": scrape_status,
            "results": {
                "posts_found": len(posts or []),
                "new_posts": new_posts,
                "duplicates_skipped": duplicates,
                "images_downloaded": images_downloaded,
                "owner_posts": owner_posts,
                "public_posts": public_posts,
                "failures": 1 if scrape_error else 0,
                "captcha_encountered": scrape_status == 'CAPTCHA_REQUIRED',
                "window_days": window_days,
            },
            "details": [run_detail],
        }
        if scrape_error:
            payload["error"] = scrape_error
            payload["warning"] = scrape_error
        return jsonify(payload)
    except Exception as e:
        logger.error(f"Error scraping competitor {competitor_id}: {e}")
        if scrape_error_logger:
            scrape_error_logger.error(f"competitor={competitor_id} scrape failed: {e}")
        return jsonify({"error": str(e)}), 500

# Keyword endpoints
@app.route('/api/projects/<int:project_id>/keywords', methods=['GET'])
def get_keywords(project_id):
    """Get keywords for a project"""
    try:
        keywords = db.get_keywords(project_id)
        return jsonify({"keywords": keywords})
    except Exception as e:
        logger.error(f"Error getting keywords: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/keywords', methods=['POST'])
def add_keyword(project_id):
    """Add a keyword to a project"""
    try:
        data = request.get_json()
        keyword = data.get('keyword')

        if not keyword:
            return jsonify({"error": "Keyword is required"}), 400

        keyword_id = db.add_keyword(project_id, keyword)
        return jsonify({"keyword_id": keyword_id, "keyword": keyword}), 201
    except Exception as e:
        logger.error(f"Error adding keyword: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/keywords/<int:keyword_id>', methods=['DELETE'])
def delete_keyword(keyword_id):
    """Delete a keyword"""
    try:
        db.delete_keyword(keyword_id)
        return jsonify({"message": "Keyword deleted successfully"})
    except Exception as e:
        logger.error(f"Error deleting keyword: {e}")
        return jsonify({"error": str(e)}), 500

# Review & Market Intelligence endpoints (PDF Spec Compliance)
@app.route('/api/projects/<int:project_id>/reviews', methods=['GET'])
def get_project_reviews(project_id):
    """Get scraped Google Maps reviews for a project with optional filters"""
    try:
        competitor_id = request.args.get('competitor_id', type=int)
        sentiment = request.args.get('sentiment')
        topic = request.args.get('topic')
        rating = request.args.get('rating', type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        reviews = db.get_reviews(
            project_id=project_id,
            competitor_id=competitor_id,
            sentiment=sentiment,
            topic=topic,
            rating=rating,
            limit=limit,
            offset=offset
        )
        return jsonify({"reviews": reviews, "count": len(reviews)})
    except Exception as e:
        logger.error(f"Error getting project reviews: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/market-overview', methods=['GET'])
def get_project_market_overview(project_id):
    """Get merged market intelligence metrics across all competitors (PDF spec)"""
    try:
        overview = db.get_market_overview(project_id)
        return jsonify(overview)
    except Exception as e:
        logger.error(f"Error getting market overview: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/reviews/analytics', methods=['GET'])
def get_project_review_analytics(project_id):
    """Get review analytics: sentiment distribution, topic ranking, rating distribution"""
    try:
        analytics = db.get_review_analytics(project_id)
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"Error getting review analytics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/market-gaps', methods=['GET'])
def get_project_market_gaps(project_id):
    """Get strategic market gaps, competitor vulnerabilities, and counter-tactics"""
    try:
        gaps = db.get_market_gaps(project_id)
        return jsonify({"gaps": gaps, "count": len(gaps)})
    except Exception as e:
        logger.error(f"Error getting market gaps: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/trend-analysis', methods=['GET'])
def get_project_trend_analysis(project_id):
    """Get topic and keyword trend analysis across all competitor posts for a project"""
    try:
        trends = db.get_trend_analysis(project_id)
        return jsonify(trends)
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        return jsonify({"error": str(e)}), 500

# Post endpoints
@app.route('/api/posts', methods=['GET'])
def get_all_posts():
    """Get posts filtered by project_id or competitor_id.

    Owner posts always come first; public (user generated) posts can be hidden
    with `include_public=false` or requested alone with `source=public`.
    """
    try:
        project_id = request.args.get('project_id', type=int)
        competitor_id = request.args.get('competitor_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        source = (request.args.get('source') or '').strip().lower() or None
        if source not in ('owner', 'public', 'all'):
            source = None
        if source == 'all':
            source = None
        include_public = _bool_arg('include_public', True)
        posts = db.get_posts(
            project_id=project_id, competitor_id=competitor_id,
            limit=limit, offset=offset,
            source=source, include_public=include_public,
        )
        owner_count = sum(1 for post in posts if not post.get('is_public'))
        return jsonify({
            "posts": posts,
            "count": len(posts),
            "owner_posts": owner_count,
            "public_posts": len(posts) - owner_count,
        })
    except Exception as e:
        logger.error(f"Error getting all posts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/posts', methods=['GET'])
def get_posts(project_id):
    """Get posts for a project (owner posts first, public posts optional)."""
    try:
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        source = (request.args.get('source') or '').strip().lower() or None
        if source not in ('owner', 'public'):
            source = None
        include_public = _bool_arg('include_public', True)
        posts = db.get_posts(
            project_id=project_id, limit=limit, offset=offset,
            source=source, include_public=include_public,
        )
        owner_count = sum(1 for post in posts if not post.get('is_public'))
        return jsonify({
            "posts": posts,
            "count": len(posts),
            "owner_posts": owner_count,
            "public_posts": len(posts) - owner_count,
        })
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/posts/<int:post_id>', methods=['GET'])
def get_post(post_id):
    """Get a specific post"""
    try:
        post = db.get_post(post_id)
        if post:
            return jsonify({"post": post, **post})
        else:
            return jsonify({"error": "Post not found"}), 404
    except Exception as e:
        logger.error(f"Error getting post: {e}")
        return jsonify({"error": str(e)}), 500

# Scraping endpoints
@app.route('/api/projects/<int:project_id>/scrape', methods=['POST'])
def scrape_competitors(project_id):
    """Start scraping for competitors in a project"""
    try:
        # Get project details
        project = db.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Get competitors for this project
        competitors = db.get_competitors(project_id)
        if not competitors:
            return jsonify({"error": "No competitors found for this project"}), 400

        # Start scraping log
        log_id = db.start_scraping_log(project_id)

        # Initialize scraper
        scraper = GoogleMapsScraper(headless=True)

        # Convert competitors to format expected by scraper
        competitor_list = [
            {
                "name": comp["name"],
                "gmap_url": comp["gmap_url"],
                "address": comp.get("address"),
            }
            for comp in competitors
            if comp["gmap_url"]
        ]

        # Perform scraping (owner updates first, public content afterwards).
        # The project field/profile selects the topic profile (cafe / salon /
        # fashion / ecommerce / generic) so topics match this business type.
        industry = infer_industry(project.get('field'), project.get('our_profile'))
        all_posts = scraper.scrape_multiple_competitors(
            competitor_list, include_public=True, industry=industry
        )
        run_diagnostics = dict(getattr(scraper, "last_run_diagnostics", {}) or {})
        place_profiles = dict(getattr(scraper, "last_place_profiles", {}) or {})

        # Process and save posts
        total_posts_found = 0
        total_new_posts = 0
        total_duplicates = 0
        total_images = 0
        failed_competitors = []
        captcha_competitors = []

        for competitor_name, posts in all_posts.items():
            # Find competitor ID
            competitor_obj = next((c for c in competitors if c["name"] == competitor_name), None)
            if not competitor_obj:
                continue

            competitor_id = competitor_obj["id"]
            posts_found = len(posts)
            total_posts_found += posts_found
            images_found = sum(len((post or {}).get("image_urls") or []) for post in posts)
            total_images += images_found
            new_posts_for_competitor = 0
            duplicates_for_competitor = 0
            cards_skipped_for_competitor = 0
            unverified_skipped_for_competitor = 0

            # Per-place diagnostics of this run: reviews/posts are only kept
            # when the opened page was verified as this business.
            detail = dict(run_diagnostics.get(competitor_name) or {})
            business_verified = bool(detail.get("business_verified"))

            for post_data in posts:
                # Add competitor info to post data
                post_data = dict(post_data)
                post_data["competitor_name"] = competitor_name
                # Google Maps list-page "place suggestion" cards are not posts.
                if looks_like_place_card(post_data.get("text_content")):
                    cards_skipped_for_competitor += 1
                    continue
                # Another business's content must never be stored as ours.
                if not business_verified:
                    unverified_skipped_for_competitor += 1
                    continue
                post_id = db.add_post(competitor_id, post_data)
                if post_id:
                    total_new_posts += 1
                    new_posts_for_competitor += 1
                else:
                    total_duplicates += 1  # Duplicate was skipped
                    duplicates_for_competitor += 1

            # Persist the listing statistics + real reviews captured in this
            # run so the review charts show Google Maps values.
            profile = place_profiles.get(competitor_name) or {}
            if profile:
                persist_competitor_profile(competitor_id, profile)
            if business_verified:
                reviews_saved = persist_scraped_reviews(project_id, competitor_id, posts)
            else:
                reviews_saved = 0

            # Requirement 21: persist the per-competitor statistics of this run.
            detail.setdefault("competitor", competitor_name)
            detail.setdefault("gmap_url", competitor_obj.get("gmap_url"))
            detail["posts_found"] = posts_found
            detail["new_posts"] = new_posts_for_competitor
            detail["duplicates_skipped"] = duplicates_for_competitor
            detail["images_downloaded"] = images_found
            detail["owner_posts"] = sum(
                1 for post in posts if (post or {}).get("post_source") != "public"
            )
            detail["public_posts"] = sum(
                1 for post in posts if (post or {}).get("post_source") == "public"
            )
            detail["reviews_saved"] = reviews_saved
            detail["place_profile"] = profile or None
            if cards_skipped_for_competitor:
                detail["cards_skipped"] = cards_skipped_for_competitor
            if unverified_skipped_for_competitor:
                detail["unverified_skipped"] = unverified_skipped_for_competitor
            detail.setdefault("status", "SUCCESS" if posts_found else "NO_POSTS")
            detail.setdefault("error", None)
            detail["captcha_required"] = bool(
                detail.get("captcha_required")
                or str(detail.get("status") or "").upper() == "CAPTCHA_REQUIRED"
            )
            run_diagnostics[competitor_name] = detail

            if detail.get("error"):
                failed_competitors.append(f"{competitor_name}: {detail['error']}")
            if detail["captcha_required"]:
                captcha_competitors.append(competitor_name)

            # Record the (re-)scrape so "Last Scraped" and the post count stay fresh
            try:
                comp_status = db.get_competitor_with_status(competitor_id) or {}
                db.mark_competitor_scraped(competitor_id, comp_status.get("posts_collected", 0))
            except Exception as status_err:
                logger.warning(f"Could not update scrape status for {competitor_name}: {status_err}")

        # Competitors without a Google Maps URL never reach the scraper; they are
        # still logged so the statistics match what was requested.
        for comp in competitors:
            if comp.get("gmap_url"):
                continue
            name = comp.get("name") or f"competitor-{comp.get('id')}"
            if name in run_diagnostics:
                continue
            run_diagnostics[name] = {
                "competitor": name,
                "gmap_url": None,
                "status": "NO_URL",
                "error": "No Google Maps URL configured for this competitor",
                "captcha_required": False,
                "posts_found": 0,
                "new_posts": 0,
                "duplicates_skipped": 0,
                "images_downloaded": 0,
                "owner_posts": 0,
                "public_posts": 0,
            }
            failed_competitors.append(f"{name}: No Google Maps URL configured")

        # Requirement 21: overall run status incl. CAPTCHA/manual intervention.
        total_failures = len(failed_competitors)
        run_status = "completed"
        if run_diagnostics and total_failures >= len(run_diagnostics):
            run_status = "failed"
        elif total_failures:
            run_status = "completed_with_errors"
        if captcha_competitors and not total_new_posts:
            run_status = "manual_intervention_required"

        # Update scraping log
        db.update_scraping_log(
            log_id,
            end_time=datetime.now(),
            competitors_processed=len(run_diagnostics) or len(competitor_list),
            posts_found=total_posts_found,
            new_posts=total_new_posts,
            duplicates_skipped=total_duplicates,
            images_downloaded=total_images,
            failures=total_failures,
            captcha_encountered=1 if captcha_competitors else 0,
            error_info=" | ".join(failed_competitors) if failed_competitors else None,
            competitor_names=json.dumps(list(run_diagnostics.keys())),
            details=json.dumps(list(run_diagnostics.values())),
            status=run_status,
        )

        # Error information is archived in the log files (no other file touched).
        if scrape_run_logger:
            scrape_run_logger.info(
                "run_id=%s project=%s status=%s competitors=%s posts_found=%s new_posts=%s "
                "duplicates_skipped=%s images_downloaded=%s failures=%s captcha=%s",
                log_id, project_id, run_status, len(run_diagnostics), total_posts_found,
                total_new_posts, total_duplicates, total_images, total_failures,
                captcha_competitors or "none",
            )
        if scrape_error_logger:
            for detail in run_diagnostics.values():
                if detail.get("error"):
                    scrape_error_logger.error(
                        "run_id=%s project=%s competitor=%s status=%s captcha=%s error=%s",
                        log_id, project_id, detail.get("competitor"), detail.get("status"),
                        detail.get("captcha_required"), detail.get("error"),
                    )

        return jsonify({
            "message": "Scraping completed successfully",
            "log_id": log_id,
            "scrape_status": run_status,
            "results": {
                "competitors_processed": len(run_diagnostics) or len(competitor_list),
                "posts_found": total_posts_found,
                "new_posts": total_new_posts,
                "duplicates_skipped": total_duplicates,
                "images_downloaded": total_images,
                "failures": total_failures,
                "captcha_encountered": bool(captcha_competitors),
            },
            "errors": failed_competitors,
            "details": list(run_diagnostics.values()),
        })
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        if scrape_error_logger:
            scrape_error_logger.error(f"project={project_id} run failed: {e}")
        return jsonify({"error": str(e)}), 500

# AI Analysis endpoints
@app.route('/api/projects/<int:project_id>/analyze', methods=['POST'])
def analyze_project(project_id):
    """Analyze posts for a project using AI"""
    try:
        # Get project details
        project = db.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Get posts for analysis
        posts = db.get_posts(project_id=project_id, limit=100)
        if not posts:
            return jsonify({"error": "No posts found for analysis"}), 400

        # Perform AI analysis
        analysis = ai_service.analyze_posts(posts)

        return jsonify({
            "project_id": project_id,
            "analysis": analysis,
            "posts_analyzed": len(posts)
        })
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return jsonify({"error": str(e)}), 500

# Content generation endpoints
@app.route('/api/projects/<int:project_id>/ideas', methods=['POST'])
def generate_ideas(project_id):
    """Generate content ideas for a project"""
    try:
        data = request.get_json()
        count = data.get('count', 5)

        # Validate count
        if not isinstance(count, int) or count < 1 or count > 50:
            return jsonify({"error": "Count must be between 1 and 50"}), 400

        # Get project details
        project = db.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Build business context for the AI
        business_name     = project.get('name', 'Our Business')
        business_profile  = project.get('our_profile', '')
        business_location = project.get('location', '')

        # Get competitor names to explicitly block from output
        competitors_raw  = db.get_competitors(project_id)
        competitor_names = [c.get('name', '') for c in competitors_raw if c.get('name')]

        # Get posts for idea generation
        posts = db.get_posts(project_id=project_id, limit=50)
        if not posts:
            return jsonify({"error": "No posts found for idea generation. Add competitors and run scraping first."}), 400

        # Fetch trend analysis — ordered topic+keyword data to guide idea themes naturally
        trend_data = db.get_trend_analysis(project_id)
        trending_topics = [t['topic'] for t in trend_data.get('topic_trends', [])]
        trending_keywords = [k['keyword'] for k in trend_data.get('keyword_trends', [])]

        # Retrieve existing ideas to prevent duplicates
        existing_rows = db.get_generated_ideas(project_id, limit=30)
        existing_texts = []
        for r in existing_rows:
            raw_text = r.get('idea_text', '')
            try:
                parsed = json.loads(raw_text) if isinstance(raw_text, str) else raw_text
                if isinstance(parsed, dict) and 'update_text' in parsed:
                    existing_texts.append(parsed['update_text'])
                else:
                    existing_texts.append(str(raw_text))
            except Exception:
                existing_texts.append(str(raw_text))

        # Generate ideas using AI with business context, trend data, and duplicate prevention
        ideas = ai_service.generate_content_ideas(
            posts, count,
            existing_ideas=existing_texts,
            business_name=business_name,
            business_profile=business_profile,
            business_location=business_location,
            competitor_names=competitor_names,
            trending_topics=trending_topics,
            trending_keywords=trending_keywords
        )

        # Save ideas to database
        idea_ids = []
        for idea in ideas:
            idea_content = json.dumps(idea) if isinstance(idea, dict) else str(idea)
            idea_id = db.add_generated_idea(project_id, idea_content)
            idea_ids.append(idea_id)

        return jsonify({
            "project_id": project_id,
            "ideas": ideas,
            "idea_ids": idea_ids,
            "count": len(ideas)
        })
    except Exception as e:
        logger.error(f"Error generating ideas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/complete-update', methods=['POST'])
def generate_complete_update(project_id):
    """Generate a complete Google Maps update for a project"""
    try:
        # Get project details
        project = db.get_project(project_id)
        if not project:
            return jsonify({"error": "Project not found"}), 404

        # Get posts for analysis
        posts = db.get_posts(project_id=project_id, limit=30)
        if not posts:
            return jsonify({"error": "No posts found for update generation"}), 400

        # Generate complete update using AI
        update = ai_service.generate_complete_update(posts)

        return jsonify({
            "project_id": project_id,
            "update": update,
            "posts_analyzed": len(posts)
        })
    except Exception as e:
        logger.error(f"Error generating complete update: {e}")
        return jsonify({"error": str(e)}), 500

# Generated ideas endpoints
@app.route('/api/projects/<int:project_id>/generated-ideas', methods=['GET'])
def get_generated_ideas(project_id):
    """Get generated ideas for a project"""
    try:
        limit = request.args.get('limit', 50, type=int)
        ideas = db.get_generated_ideas(project_id, limit)
        return jsonify({"ideas": ideas})
    except Exception as e:
        logger.error(f"Error getting generated ideas: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/generated-ideas/<int:idea_id>/use', methods=['POST'])
def mark_idea_used(idea_id):
    """Mark a generated idea as used"""
    try:
        db.mark_idea_used(idea_id)
        return jsonify({"message": "Idea marked as used"})
    except Exception as e:
        logger.error(f"Error marking idea as used: {e}")
        return jsonify({"error": str(e)}), 500

# Analytics endpoints
@app.route('/api/projects/<int:project_id>/analytics/topics', methods=['GET'])
def get_topic_frequency(project_id):
    """Get topic frequency analytics"""
    try:
        topics = db.get_topic_frequency(project_id)
        return jsonify({"topics": topics})
    except Exception as e:
        logger.error(f"Error getting topic frequency: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/analytics/keywords', methods=['GET'])
def get_keyword_frequency(project_id):
    """Get keyword frequency analytics"""
    try:
        keywords = db.get_keyword_frequency(project_id)
        return jsonify({"keywords": keywords})
    except Exception as e:
        logger.error(f"Error getting keyword frequency: {e}")
        return jsonify({"error": str(e)}), 500

# Scraping logs endpoints
@app.route('/api/projects/<int:project_id>/scraping-logs', methods=['GET'])
def get_scraping_logs(project_id):
    """Get persistent scraping logs + dashboard statistics for a project.

    Requirement 21: every run reports the competitor(s) processed, start/end
    time, posts found, new posts added, duplicates skipped, images downloaded,
    failures, CAPTCHA/manual-intervention status and error information.
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        logs = db.get_scraping_logs(project_id, limit)
        return jsonify({
            "logs": logs,
            "count": len(logs),
            "stats": db.get_scraping_stats(project_id),
        })
    except Exception as e:
        logger.error(f"Error getting scraping logs: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/projects/<int:project_id>/scraping-stats', methods=['GET'])
def get_scraping_stats(project_id):
    """Aggregated dashboard statistics (requirement 20)."""
    try:
        return jsonify(db.get_scraping_stats(project_id))
    except Exception as e:
        logger.error(f"Error getting scraping stats: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Render/Heroku-style platforms inject $PORT; local development defaults
    # to 10000 (set PORT=5000 to keep the old local behaviour).
    port = int(os.environ.get('PORT', 10000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)