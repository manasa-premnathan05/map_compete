import time
import json
import os
import re
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import logging

try:
    from place_identity import extract_place_identity
except ImportError:  # pragma: no cover - allow running from any cwd
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from place_identity import extract_place_identity

try:
    from topic_classifier import classify_topic, classify_sentiment, infer_industry
except ImportError:  # pragma: no cover - allow running from any cwd
    import sys as _sys

    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from topic_classifier import classify_topic, classify_sentiment, infer_industry

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool = True) -> bool:
    """Read a boolean environment switch, e.g. SCRAPE_BLOCK_IMAGES=false."""
    value = os.environ.get(name)
    if value is None:
        return default
    return str(value).strip().lower() not in ("0", "false", "no", "off")


class GoogleMapsScraper:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.driver = None
        self.wait_time = 10
        # Requirement 21: per-competitor statistics of the latest run, consumed
        # by the API to build the persistent scraping log.
        self.last_run_diagnostics: Dict[str, Dict] = {}
        # Industry profile used for topic classification (cafe / salon /
        # fashion / ecommerce / generic). ``None`` keeps the generic profile.
        self.industry: Optional[str] = None
        # Google Maps profile statistics (rating / review count / address /
        # category) captured while the place page was open during scraping.
        # Consumed by the API so review charts use real scraped values.
        self.last_place_profiles: Dict[str, Dict] = {}

    @staticmethod
    def _candidate_browser_binaries():
        """Browser binaries to try, in order (env first, then known locations)."""
        import shutil

        candidates = [os.environ.get('CHROME_BINARY'), os.environ.get('CHROME_PATH'),
                      '/usr/bin/chromium', '/usr/bin/chromium-browser',
                      '/usr/bin/google-chrome', '/usr/bin/google-chrome-stable']
        for name in ('chromium', 'chromium-browser', 'google-chrome',
                     'google-chrome-stable', 'chrome'):
            candidates.append(shutil.which(name))

        ordered = []
        for candidate in candidates:
            if candidate and candidate not in ordered and os.path.exists(candidate):
                ordered.append(candidate)
        return ordered

    @staticmethod
    def _candidate_driver_paths():
        """ChromeDriver binaries to try, in order (env first, then known paths).

        Debian's chromium-driver package has shipped the driver at more than one
        path across releases, and Render's image pins a single one - so every
        candidate is considered rather than trusting one path.
        """
        import shutil

        candidates = [os.environ.get('CHROMEDRIVER_PATH'),
                      '/usr/bin/chromium-driver', '/usr/bin/chromedriver',
                      '/usr/lib/chromium/chromedriver']
        for name in ('chromedriver', 'chromium-driver'):
            candidates.append(shutil.which(name))

        ordered = []
        for candidate in candidates:
            if candidate and candidate not in ordered and os.path.exists(candidate):
                ordered.append(candidate)
        return ordered

    def setup_driver(self):
        """Start Chrome/Chromium using several discovery strategies.

        Render's image provides the browser and driver through CHROME_BINARY /
        CHROMEDRIVER_PATH, but a single wrong path used to make every Google
        Maps call fail. Each candidate driver (and finally Selenium Manager) is
        tried instead; if none works, a WebDriverException carrying a concise,
        credential-free reason is raised so callers can report BROWSER_ERROR.
        """
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Memory discipline: a Chromium session is by far the largest consumer
        # inside an instance with a 512 MB ceiling, and the scraper only ever
        # reads rendered text and image URLs - never the pixels. Blocking image
        # loading, capping renderer processes and switching off background work
        # keep a run inside the limit instead of the whole service being killed.
        # The image URLs are still present on the elements (they are read from
        # src / style), so collected media is unaffected.
        #   SCRAPE_BLOCK_IMAGES=false   restore image loading
        #   SCRAPE_JS_HEAP_MB=0         leave the JavaScript heap uncapped
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-component-update")
        chrome_options.add_argument("--disable-default-apps")
        chrome_options.add_argument("--disable-sync")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--metrics-recording-only")
        chrome_options.add_argument("--mute-audio")
        chrome_options.add_argument(
            "--disable-features=site-per-process,Translate,BackForwardCache,"
            "MediaRouter,OptimizationHints,InterestFeedContentSuggestions"
        )
        chrome_options.add_argument("--renderer-process-limit=2")
        if _env_flag("SCRAPE_BLOCK_IMAGES", True):
            chrome_options.add_argument("--blink-settings=imagesEnabled=false")
        heap_mb = str(os.environ.get("SCRAPE_JS_HEAP_MB", "384")).strip()
        if heap_mb.isdigit() and int(heap_mb) > 0:
            chrome_options.add_argument(f"--js-flags=--max-old-space-size={int(heap_mb)}")

        binaries = self._candidate_browser_binaries()
        if binaries:
            chrome_options.binary_location = binaries[0]

        attempts = []
        for driver_path in self._candidate_driver_paths():
            try:
                self.driver = webdriver.Chrome(
                    service=Service(executable_path=driver_path),
                    options=chrome_options)
                attempts.append(os.path.basename(driver_path) + ': ok')
                break
            except Exception as exc:
                self.driver = None
                attempts.append('%s: %s' % (os.path.basename(driver_path),
                                            type(exc).__name__))
        if self.driver is None:
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                attempts.append('selenium-manager: ok')
            except Exception as exc:
                self.driver = None
                attempts.append('selenium-manager: ' + type(exc).__name__)

        if self.driver is None:
            reason = ' | '.join(attempts) or 'no browser or driver candidates found'
            logger.error("Could not start a browser: %s", reason)
            raise WebDriverException('no usable browser/driver found (%s)' % reason)

        try:
            page_load_timeout = int(os.environ.get("GOOGLE_MAPS_PAGE_LOAD_TIMEOUT", "18"))
            page_load_timeout = max(8, min(page_load_timeout, 60))
            self.driver.set_page_load_timeout(page_load_timeout)
            self.driver.set_script_timeout(15)
        except Exception:
            pass
        logger.info("WebDriver setup successful")

    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            logger.info("WebDriver closed")

    # ------------------------------------------------------------------
    # Google Maps page-state detection (shared by search + resolve)
    # ------------------------------------------------------------------
    # "Google Maps returned nothing" and "we could not read Google Maps" are
    # completely different answers. These markers let the scraper tell them
    # apart, so an infrastructure/scraping failure is never reported as an
    # empty (but valid) search result.
    _CAPTCHA_MARKERS = (
        'recaptcha',
        'unusual traffic',
        'not a robot',
        'verify you are human',
        "verify you're human",
        'automated queries',
        'automated query',
        'our systems have detected',
        'complete the security check',
        'are you a robot',
    )
    _BLOCKED_MARKERS = (
        'you have been blocked',
        'your request has been blocked',
        'request blocked',
        'access denied',
        '403 forbidden',
        'error 403',
        'this content is not available',
        'not available in your region',
    )
    _CONSENT_MARKERS = (
        'before you continue to google maps',
        'i agree',
        'accept all',
        'your choices regarding cookies',
    )
    _ERROR_MARKERS = (
        'something went wrong',
        'we are sorry',
        "we're sorry",
        'server error',
        'network error',
        'no internet',
        'err_',
        "can't reach",
        'cannot reach',
        'service unavailable',
        'google maps is unavailable',
    )
    _NO_RESULT_MARKERS = (
        "can't find",
        'cannot find',
        'could not find',
        "couldn't find",
        'no results found',
        "didn't match any",
        'did not match any',
        'no matching places',
    )
    _MAPS_READY_MARKERS = ('google maps', 'directions', 'satellite')
    _LIMITED_VIEW_MARKERS = ('limited view of google maps',)
    _BLOCKED_URL_MARKERS = ('/sorry/', 'google.com/sorry')
    _CONSENT_URL_MARKERS = ('consent.google.com', '/consent')

    # Address shape used to split Google's "category, address, hours" row text.
    _ADDRESS_HINTS = (
        'road', 'street', 'avenue', 'lane', 'drive', 'boulevard', 'highway',
        'sector', 'block', 'phase', 'floor', 'building', 'tower', 'complex',
        'mall', 'plaza', 'market', 'colony', 'nagar', 'vihar', 'puram', 'ganj',
        'chowk', 'circle', 'square', 'cross', 'main', 'link', 'service',
        'plot', 'shop no', 'unit', 'suite', 'level', 'basement',
    )

    # Result list selectors. Google rotates its class names, so every strategy
    # is attempted and the first productive one wins.
    RESULT_CARD_SELECTORS = (
        "div[role='feed'] > div[jsaction]",
        "div[role='feed'] > div",
        "div.Nv2PK",
        "div[jsaction*='mouseover:pane']",
        "div[role='feed'] div[role='article']",
    )
    RESULT_LINK_SELECTORS = (
        "a[href*='/maps/place/']",
        "a[href*='google.com/maps/place']",
    )
    RESULT_SCROLL_SELECTORS = (
        "div[role='feed']",
        "div.m6QErb.DxyBCb",
        "div.m6QErb[aria-label]",
    )
    NAME_SELECTORS = (
        "div.qBF1Pd",
        "div.fontHeadlineSmall span",
        "div.fontHeadlineSmall",
        "h3",
    )
    def _page_snapshot(self) -> Dict:
        """URL + title + visible text of the current page.

        Only public page text is captured - never cookies, local storage or
        request headers.
        """
        snapshot = {'current_url': '', 'title': '', 'body_text': ''}
        try:
            snapshot['current_url'] = self.driver.current_url or ''
        except Exception:
            pass
        try:
            snapshot['title'] = self.driver.title or ''
        except Exception:
            pass
        try:
            body = self.driver.find_element(By.TAG_NAME, 'body')
            snapshot['body_text'] = (body.text or '')[:4000]
        except Exception:
            pass
        return snapshot

    def _detect_google_maps_page_state(self, snapshot: Optional[Dict] = None,
                                       result_cards: int = 0,
                                       place_links: int = 0) -> Dict:
        """Classify what Google Maps actually served.

        ``result_cards``/``place_links`` are the extraction counts, so the same
        helper reports RESULTS once rows were read, and SELECTOR_FAILURE when a
        Maps page loaded but nothing could be identified.

        Returns ``{"state", "current_url", "title", "message", "markers"}`` -
        no cookies, credentials or headers.
        """
        if self.driver is None:
            return {'state': 'BROWSER_ERROR', 'current_url': '', 'title': '',
                    'message': 'The browser session is not available.',
                    'markers': []}

        snapshot = snapshot or self._page_snapshot()
        url = snapshot.get('current_url') or ''
        url_lower = url.lower()
        title = snapshot.get('title') or ''
        body = snapshot.get('body_text') or ''
        haystack = (title + '\n' + body).lower()

        def matched(markers):
            return [marker for marker in markers if marker in haystack]

        def response(state, message, markers=()):
            return {'state': state, 'current_url': url, 'title': title,
                    'message': message, 'markers': list(markers)}

        if any(marker in url_lower for marker in self._BLOCKED_URL_MARKERS):
            return response('BLOCKED', 'Google Maps blocked this request.')
        captcha = matched(self._CAPTCHA_MARKERS)
        if captcha:
            return response('CAPTCHA',
                            'Google Maps presented an anti-automation challenge.',
                            captcha)
        consent = matched(self._CONSENT_MARKERS)
        if any(marker in url_lower for marker in self._CONSENT_URL_MARKERS) or consent:
            return response('CONSENT',
                            'Google Maps is waiting for a consent decision.',
                            consent)
        blocked = matched(self._BLOCKED_MARKERS)
        if blocked:
            return response('BLOCKED',
                            'Google Maps refused to serve the results page.',
                            blocked)
        if not body.strip() and not title.strip():
            return response('ERROR', 'Google Maps returned an empty page.')
        if result_cards or place_links:
            return response('RESULTS', None)
        no_results = matched(self._NO_RESULT_MARKERS)
        if no_results:
            return response('NO_RESULTS',
                            'Google Maps reported no matching places.',
                            no_results)
        if '/maps/place/' in url_lower:
            return response('PLACE_PROFILE',
                            'Google Maps opened a single business profile.')
        errors = matched(self._ERROR_MARKERS)
        if errors:
            return response('ERROR', 'Google Maps reported an error page.', errors)
        limited = matched(self._LIMITED_VIEW_MARKERS)
        if matched(self._MAPS_READY_MARKERS):
            message = ('Google Maps served a limited (unauthenticated) view without '
                       'the result list.' if limited else
                       'Google Maps loaded but the result structure could not be '
                       'identified.')
            return response('SELECTOR_FAILURE', message, limited)
        return response('UNKNOWN', 'Google Maps served an unrecognised page.')
    def _count_result_cards(self) -> int:
        """How many result containers the current DOM exposes (best effort)."""
        total = 0
        for selector in self.RESULT_CARD_SELECTORS:
            try:
                total = max(total, len(self.driver.find_elements(By.CSS_SELECTOR, selector)))
            except Exception:
                continue
        return total

    def _scroll_results_pane(self, max_scrolls: int = 3, pause: float = 1.2) -> int:
        """Scroll the results pane so dynamically loaded rows render.

        Google Maps materialises rows while the pane scrolls; without this a
        search can legitimately come back with only the first visible row.
        """
        pane = None
        for selector in self.RESULT_SCROLL_SELECTORS:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                continue
            if elements:
                pane = elements[0]
                break
        if pane is None:
            return 0

        scrolls = 0
        for _ in range(max_scrolls):
            try:
                before = self.driver.execute_script("return arguments[0].scrollTop;", pane)
                self.driver.execute_script(
                    "arguments[0].scrollTop = arguments[0].scrollHeight;", pane)
                time.sleep(pause)
                after = self.driver.execute_script("return arguments[0].scrollTop;", pane)
            except Exception:
                break
            scrolls += 1
            if before == after:
                break
        return scrolls

    @staticmethod
    def _is_glyph_only(text: str) -> bool:
        """True for Material-icon glyphs Google renders as text (U+E000-U+F8FF)."""
        stripped = (text or '').strip()
        return bool(stripped) and all('\ue000' <= char <= '\uf8ff' for char in stripped)

    @staticmethod
    def _clean_text_fragment(value: str) -> Optional[str]:
        """Trim a row fragment and drop Google's '·' separators around it."""
        cleaned = (value or '').strip().strip('\u00b7\u22c5').strip().strip(',').strip()
        return cleaned or None

    @staticmethod
    def _looks_like_address(text: str) -> bool:
        """True when a row fragment looks like a street address."""
        lowered = (text or '').lower()
        if not lowered or len(lowered) > 160:
            return False
        # Require at least one real letter: "(1,428)" beside a rating is a review
        # count, never an address.
        if not re.search(r'[^\W\d_]', lowered):
            return False
        if any(hint in lowered for hint in GoogleMapsScraper._ADDRESS_HINTS):
            return True
        return bool(re.search(r'\d', lowered)) and ',' in lowered

    @staticmethod
    def _name_from_maps_url(url: str) -> Optional[str]:
        """Business name derived from a /maps/place/<name>/ URL (never invented)."""
        import urllib.parse

        match = re.search(r'/maps/place/([^/@?]+)', url or '')
        if not match:
            return None
        name = urllib.parse.unquote(match.group(1)).replace('+', ' ').strip()
        name = name.split(' - ')[0].strip()
        return name or None
    def search_google_maps_places(self, query: str, location: str = None,
                                  max_results: int = 6) -> Dict:
        """Search Google Maps and report **both** the rows and the page state.

        Returns a dict (never a bare list) so callers can distinguish a real
        empty search from a scraping failure::

            {"state": "RESULTS", "results": [...], "count": n,
             "message": None, "diagnostics": {...}}

        ``state`` is one of RESULTS, NO_RESULTS, CAPTCHA, CONSENT, BLOCKED,
        TIMEOUT, BROWSER_ERROR, SELECTOR_FAILURE, ERROR or UNKNOWN.
        """
        import urllib.parse

        started = time.time()
        clean_query = (query or '').strip()
        clean_location = (location or '').strip()
        if clean_location and clean_location.lower() not in clean_query.lower():
            full_query = f"{clean_query} {clean_location}".strip()
        else:
            full_query = clean_query
        search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(full_query)}"

        diagnostics = {
            'query': clean_query,
            'location': clean_location or None,
            'search_url': search_url,
            'current_url': None,
            'redirected_to_profile': False,
            'title': None,
            'result_containers_found': 0,
            'place_links_found': 0,
            'strategies_tried': [],
            'scrolls': 0,
            'driver_started': False,
            'duration_seconds': 0.0,
            'error_type': None,
            'error': None,
        }
        outcome = {'state': 'UNKNOWN', 'results': [], 'count': 0,
                   'message': 'Google Maps search did not complete.',
                   'diagnostics': diagnostics}

        def finish(state, message, results=None):
            outcome['state'] = state
            outcome['message'] = message
            outcome['results'] = list(results or [])
            outcome['count'] = len(outcome['results'])
            diagnostics['duration_seconds'] = round(time.time() - started, 2)
            # Safe structured log: query / location / state / count / duration.
            logger.info(
                "Google Maps search: query=%s location=%s state=%s results=%s duration=%ss",
                clean_query, clean_location or '-', state, outcome['count'],
                diagnostics['duration_seconds'],
            )
            return outcome

        try:
            self.setup_driver()
            diagnostics['driver_started'] = self.driver is not None
        except Exception as exc:
            diagnostics['error_type'] = type(exc).__name__
            diagnostics['error'] = str(exc)[:300]
            return finish('BROWSER_ERROR',
                          'The server could not start a browser to reach Google Maps.')

        try:
            if self.driver is None:
                return finish('BROWSER_ERROR',
                              'The browser session could not be created.')

            navigation_timed_out = False
            try:
                self.driver.get(search_url)
            except TimeoutException as exc:
                # Selenium can time out after useful Maps DOM has already rendered.
                # Keep the session alive and inspect the DOM before declaring failure.
                navigation_timed_out = True
                diagnostics['error_type'] = 'TimeoutException'
                diagnostics['error'] = str(exc)[:300]
                logger.warning("Google Maps navigation timed out; inspecting rendered DOM")
            except WebDriverException as exc:
                diagnostics['error_type'] = type(exc).__name__
                diagnostics['error'] = str(exc)[:300]
                return finish('BROWSER_ERROR',
                              'Google Maps could not be loaded by the server.')
            # Explicit waits: page content first, then the result list. Bounded
            # so a Render Free request never hangs indefinitely.
            deadline = time.time() + 15
            while time.time() < deadline:
                snapshot = self._page_snapshot()
                if (snapshot.get('body_text') or '').strip() or (snapshot.get('title') or '').strip():
                    break
                time.sleep(0.4)

            while time.time() < deadline:
                if self._count_result_cards():
                    break
                if self._detect_google_maps_page_state()['state'] in (
                        'NO_RESULTS', 'CAPTCHA', 'CONSENT', 'BLOCKED'):
                    break
                time.sleep(0.5)

            results, counters = self._collect_results(max_results)
            diagnostics.update(counters)

            # One scroll pass only when the list is short, then re-collect.
            if results and len(results) < max_results:
                diagnostics['scrolls'] = self._scroll_results_pane(max_scrolls=3)
                if diagnostics['scrolls']:
                    more, after = self._collect_results(max_results)
                    if more:
                        results = more
                    diagnostics['result_containers_found'] = max(
                        diagnostics['result_containers_found'],
                        after.get('result_containers_found', 0))
                    diagnostics['place_links_found'] = max(
                        diagnostics['place_links_found'],
                        after.get('place_links_found', 0))
                    diagnostics['strategies_tried'].extend(
                        after.get('strategies_tried', []))

            snapshot = self._page_snapshot()
            diagnostics['current_url'] = snapshot.get('current_url')
            diagnostics['title'] = (snapshot.get('title') or '')[:200]
            # A redirect straight to one business profile outranks the feed rows
            # (those can be just that profile's header or its reviews).
            if '/maps/place/' in (diagnostics.get('current_url') or '').lower():
                profile_result = self._profile_result_from_page()
                if profile_result:
                    diagnostics['redirected_to_profile'] = True
                    return finish('RESULTS', None, [profile_result])

            if results:
                return finish('RESULTS', None, results[:max_results])

            state_info = self._detect_google_maps_page_state(
                snapshot,
                result_cards=diagnostics.get('result_containers_found', 0),
                place_links=diagnostics.get('place_links_found', 0),
            )

            if navigation_timed_out and state_info.get('state') not in (
                    'RESULTS', 'NO_RESULTS', 'CAPTCHA', 'CONSENT', 'BLOCKED',
                    'PLACE_PROFILE'):
                return finish('TIMEOUT', 'Google Maps did not finish loading in time.')

            # Google frequently answers a name+area search by redirecting straight
            # to the single matching business profile. That business IS the
            # result (handled above); if its profile cannot be read, say so
            # instead of reporting "no businesses".
            return finish(state_info['state'], state_info.get('message'))
        except Exception as exc:
            # Never let an unexpected error masquerade as "no results".
            diagnostics['error_type'] = type(exc).__name__
            diagnostics['error'] = str(exc)[:300]
            logger.warning("Google Maps search failed: %s", exc)
            return finish('ERROR',
                          'The Google Maps search could not be completed on the server.')
        finally:
            self.close_driver()
    def _element_text(self, element) -> str:
        """Visible text of an element, with an innerText fallback.

        Some Google Maps containers report an empty ``.text`` to Selenium while
        still rendering content, which would silently drop ratings, review
        counts and addresses.
        """
        try:
            text = element.text or ''
        except Exception:
            text = ''
        if text.strip():
            return text
        try:
            return (self.driver.execute_script(
                "return arguments[0] ? arguments[0].innerText : '';", element) or '')
        except Exception:
            return text

    def _profile_result_from_page(self) -> Optional[Dict]:
        """The currently open Google Maps business profile as one search result.

        Used when a search redirects to a single listing: the user asked for a
        business by name and area, so that listing is the answer.
        """
        profile = self._read_current_place_profile() or {}
        url = None
        try:
            url = self.driver.current_url or None
        except Exception:
            pass

        name = self._clean_text_fragment(profile.get('name'))
        if not name and url:
            name = self._name_from_maps_url(url)
        if not name:
            return None

        address = self._clean_text_fragment(profile.get('address'))
        return {
            'name': name,
            'google_maps_url': url,
            'category': self._clean_text_fragment(profile.get('category')),
            'address': address,
            'opening_hours': None,
            'status': None,
            'rating': profile.get('rating'),
            'review_count': profile.get('review_count'),
            'distance': None,
            **self._identity_fields(url, name, address),
        }

    def _collect_results(self, max_results: int) -> Tuple[List[Dict], Dict]:
        """Try every extraction strategy and return (results, counters)."""
        counters = {'result_containers_found': 0, 'place_links_found': 0,
                    'strategies_tried': []}
        results: List[Dict] = []
        seen_keys = set()

        def add(candidate):
            if not candidate or not candidate.get('name'):
                return
            key = (candidate.get('place_key')
                   or candidate.get('google_maps_url')
                   or '{}|{}'.format((candidate.get('name') or '').lower(),
                                     (candidate.get('address') or '').lower()))
            if key in seen_keys:
                return
            seen_keys.add(key)
            results.append(candidate)

        for selector in self.RESULT_CARD_SELECTORS:
            if len(results) >= max_results:
                break
            counters['strategies_tried'].append('cards:' + selector)
            try:
                cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                continue
            counters['result_containers_found'] = max(
                counters['result_containers_found'], len(cards))
            for card in cards:
                if len(results) >= max_results:
                    break
                try:
                    add(self._parse_result_card(card))
                except Exception as exc:
                    logger.debug("Result card parse failed (%s): %s", selector, exc)

        if len(results) < max_results:
            for selector in self.RESULT_LINK_SELECTORS:
                if len(results) >= max_results:
                    break
                counters['strategies_tried'].append('links:' + selector)
                try:
                    links = self.driver.find_elements(By.CSS_SELECTOR, selector)
                except Exception:
                    continue
                counters['place_links_found'] = max(
                    counters['place_links_found'], len(links))
                for link in links:
                    if len(results) >= max_results:
                        break
                    try:
                        href = link.get_attribute('href')
                        card = link
                        if href:
                            try:
                                card = link.find_element(
                                    By.XPATH,
                                    "./ancestor::div[contains(@class,'Nv2PK')][1]")
                            except Exception:
                                card = link
                        add(self._parse_result_card(card, href_hint=href))
                    except Exception as exc:
                        logger.debug("Result link parse failed (%s): %s", selector, exc)

        return results, counters
    def _parse_result_card(self, card, href_hint: str = None) -> Optional[Dict]:
        """Read one search row (result card or bare place link).

        Missing values stay ``None`` - nothing is invented. Extraction prefers
        Google's structured row markup and falls back to text heuristics when
        that markup is absent.
        """
        name = None
        href = href_hint or None
        rating = None
        review_count = None
        category = None
        address = None
        opening_hours = None
        status = None

        # 1. The place link carries the canonical URL (and often the name).
        if not href:
            for selector in self.RESULT_LINK_SELECTORS:
                try:
                    link = card.find_element(By.CSS_SELECTOR, selector)
                except Exception:
                    continue
                href = link.get_attribute('href') or None
                label = (link.get_attribute('aria-label') or '').strip()
                if label:
                    name = label
                if href:
                    break
        if not href:
            try:
                href = card.get_attribute('href') or None
            except Exception:
                pass

        # 2. Business name: dedicated name element, then link label, then the
        #    first rendered line, then the URL slug.
        if not name:
            for selector in self.NAME_SELECTORS:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                except Exception:
                    continue
                text = (element.text or '').strip()
                if text:
                    name = text
                    break

        card_text = self._element_text(card)
        try:
            lines = [line.strip() for line in card_text.split('\n') if line.strip()]
        except Exception:
            lines = []
        if not name and lines:
            name = lines[0]
        if not name and href:
            name = self._name_from_maps_url(href)
        name = self._clean_text_fragment(name)
        # The feed also renders chrome rows (a "Results" header, separator rows,
        # Material icon glyphs) - those are not businesses.
        if (not name or self._is_glyph_only(name)
                or name.lower() in ('results', 'sponsored', 'ads', 'more results',
                                    'see all', 'filters and topics')
                or re.fullmatch(r'[\d.,]+ reviews?', name, re.IGNORECASE)):
            return None

        # 3. Rating + review count (Google often exposes both in one label).
        for selector in ("span[role='img'][aria-label*='star']",
                         "span[aria-label*='star']", "span.MW4etd"):
            try:
                element = card.find_element(By.CSS_SELECTOR, selector)
            except Exception:
                continue
            raw = (element.get_attribute('aria-label') or element.text or '').strip()
            match = re.search(r'([0-5]\.\d)\s*star', raw) or re.search(r'^([0-5]\.\d)$', raw)
            if match:
                rating = float(match.group(1))
            review_match = re.search(r'([\d.,]+)\s*review', raw, re.IGNORECASE)
            if review_match:
                digits = re.sub(r'[^\d]', '', review_match.group(1))
                if digits:
                    review_count = int(digits)
            if rating is not None:
                break
        if review_count is None:
            for selector in ("span.UY7F9", "span[aria-label*='review']"):
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                except Exception:
                    continue
                raw = (element.get_attribute('aria-label') or element.text or '')
                digits = re.sub(r'[^\d]', '', raw.replace('\u00a0', ' '))
                if digits:
                    review_count = int(digits)
                    break
        if review_count is None:
            # Row form "4.2 (4,000)": a parenthesised count beside the rating.
            match = (re.search(r'([\d,]+)\s*review', card_text, re.IGNORECASE)
                     or re.search(r'\(([\d.,]+)\)', card_text))
            if match:
                digits = re.sub(r'[^\d]', '', match.group(1))
                if digits:
                    review_count = int(digits)

        # 4. Google's structured row: "category · address · opening hours".
        try:
            for span in card.find_elements(By.CSS_SELECTOR, "div.W4Efsd span"):
                text = self._clean_text_fragment(span.text)
                if not text or self._is_glyph_only(text):
                    continue
                if re.fullmatch(r'[0-5](?:\.\d)?', text) or not re.search(r'[^\W\d_]', text):
                    # Google repeats the rating (and its review count) inside the
                    # row - neither is a category.
                    continue
                lowered = text.lower()
                if opening_hours is None and any(
                        token in lowered for token in ('closes', 'opens', 'open 24', 'closed')):
                    opening_hours = text
                    status = ('Closed' if 'closed' in lowered
                              else 'Open' if 'open' in lowered else None)
                    continue
                if category is None and not self._looks_like_address(text) and len(text) < 80:
                    category = text
                    continue
                if address is None and self._looks_like_address(text):
                    address = text
        except Exception:
            pass
        # 5. Fallback: text heuristics over the rendered row (address first).
        if address is None or category is None:
            for index, line in enumerate(lines):
                line_lower = line.lower()
                if line == name:
                    continue
                if opening_hours is None and any(
                        token in line_lower for token in ('closes', 'opens', 'open 24', 'closed')):
                    opening_hours = line
                    status = ('Closed' if 'closed' in line_lower
                              else 'Open' if 'open' in line_lower else None)
                    continue
                if '\u00b7' in line and (address is None or category is None):
                    for part in [p.strip() for p in line.split('\u00b7') if p.strip()]:
                        if (category is None and not self._looks_like_address(part)
                                and len(part) < 80):
                            category = part
                        elif address is None and self._looks_like_address(part):
                            address = part
                    continue
                if address is None and self._looks_like_address(line) and len(line) > 5:
                    address = self._clean_text_fragment(line)
                    continue
                if (category is None and index > 0 and len(line) < 80
                        and not self._looks_like_address(line)
                        and re.search(r'[^\W\d_]', line)):
                    category = line
                    continue

        # 6. Last resort: Google's dedicated address / category elements.
        if address is None:
            try:
                for element in card.find_elements(
                        By.CSS_SELECTOR,
                        "button[data-item-id='address'], [data-item-id='address']"):
                    raw = (element.get_attribute('aria-label') or element.text or '')
                    raw = raw.replace('Address:', '').strip()
                    if raw and len(raw) > 5:
                        address = raw
                        break
            except Exception:
                pass
        if category is None:
            try:
                for element in card.find_elements(
                        By.CSS_SELECTOR,
                        "button[data-item-id='category'], [data-item-id='category']"):
                    raw = (element.get_attribute('aria-label') or element.text or '').strip()
                    if raw and len(raw) < 80:
                        category = raw
                        break
            except Exception:
                pass

        if category and category.strip().lower() in ('local guide', 'local guide.'):
            # Review authors carry this label - it is not a business category.
            category = None
        if category and not re.search(r'[^\W\d_]', category):
            # Rating / review-count echoes are never categories.
            category = None

        if not href and not address:
            # No canonical URL and no location: page chrome (such as a review row
            # on a business profile), not a business result.
            return None

        return {
            'name': name,
            'google_maps_url': href,
            'category': category,
            'address': address,
            'opening_hours': opening_hours,
            'status': status,
            'rating': rating,
            'review_count': review_count,
            # No part of this flow measures distance, so it stays None rather
            # than reporting a made-up number.
            'distance': None,
            **self._identity_fields(href, name, address),
        }

    @staticmethod
    def _identity_fields(gmap_url: str, name: str = None, address: str = None) -> Dict:
        """Place-identity fields to merge into a discovery result."""
        identity = extract_place_identity(gmap_url=gmap_url, name=name, address=address)
        return {
            "place_key": identity["place_key"],
            "identity_source": identity["identity_source"],
            "google_place_id": identity["google_place_id"],
            "hex_id": identity["hex_id"],
            "cid": identity["cid"],
            "kgmid": identity["kgmid"],
            "latitude": identity["latitude"],
            "longitude": identity["longitude"],
        }

    def resolve_place_identity(self, query: str, location: str = None) -> Dict:
        """Live Google Maps lookup: resolve a typed business name to one place.

        Used to promote a manually entered competitor (a name, maybe an
        address) onto its real Google Maps listing, so that the manual entry
        and the discovered entry collapse onto the same canonical business.
        """
        import urllib.parse
        import re

        clean_query = (query or '').strip()
        page_state = None
        result = {
            "state": None,
            "found": False,
            "query": clean_query,
            "location": location,
            "google_maps_url": None,
            "name": None,
            "address": None,
            "category": None,
            "rating": None,
            "review_count": None,
            "opening_hours": None,
            "status": None,
        }
        if not clean_query:
            result["message"] = "A business name is required"
            return result

        full_query = clean_query
        if location and location.lower() not in clean_query.lower():
            full_query = f"{clean_query} {location}".strip()
        search_url = f"https://www.google.com/maps/search/{urllib.parse.quote(full_query)}"

        try:
            try:
                self.setup_driver()
            except Exception as exc:
                result["state"] = "BROWSER_ERROR"
                result["message"] = ("The server could not start a browser to reach "
                                     "Google Maps.")
                logger.warning("Place resolution driver failure: %s", exc)
                return result

            navigation_timed_out = False
            try:
                self.driver.get(search_url)
            except TimeoutException:
                # A useful Maps profile can be rendered even when Selenium's
                # navigation timer expires. Continue and inspect the DOM.
                navigation_timed_out = True
                logger.warning("Place resolution navigation timed out; inspecting rendered DOM")
            except WebDriverException as exc:
                result["state"] = "BROWSER_ERROR"
                result["message"] = "Google Maps could not be loaded by the server."
                logger.warning("Place resolution browser failure: %s", exc)
                return result

            # Bounded readiness wait instead of a blind sleep.
            deadline = time.time() + 15
            while time.time() < deadline:
                snapshot = self._page_snapshot()
                if ((snapshot.get("body_text") or "").strip()
                        or (snapshot.get("title") or "").strip()):
                    break
                time.sleep(0.4)

            # A challenge / consent / block is a scraper problem, never a
            # "this business does not exist" answer.
            page_state = self._detect_google_maps_page_state()
            if page_state["state"] in ("CAPTCHA", "CONSENT", "BLOCKED", "ERROR",
                                       "BROWSER_ERROR"):
                result["state"] = page_state["state"]
                result["message"] = page_state["message"]
                return result

            # Ask Google itself whether the search matched anything.
            try:
                no_results = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(),\"can't find\") or contains(text(),'Google Maps can't find')]",
                )
                no_results = bool(no_results)
            except Exception:
                no_results = False

            current_url = self.driver.current_url or ''
            name = None
            address = None
            category = None
            rating = None
            review_count = None
            opening_hours = None
            status = None

            try:
                headings = self.driver.find_elements(By.TAG_NAME, "h1")
                for heading in headings:
                    text = (heading.text or '').strip()
                    if text:
                        name = text
                        break
            except Exception:
                pass

            # Try to get address from structured element
            try:
                for selector in ("button[data-item-id='address']", "[data-item-id='address']"):
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        raw = (elements[0].get_attribute('aria-label')
                               or elements[0].text or '')
                        address = raw.replace('Address:', '').strip() or None
                        break
            except Exception:
                pass

            # Try to get category from structured element
            try:
                for selector in ("button[data-item-id='category']", "[data-item-id='category']"):
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        raw = (elements[0].get_attribute('aria-label')
                               or elements[0].text or '')
                        category = raw.strip() or None
                        break
            except Exception:
                pass

            # Try to get rating
            try:
                rating_elements = self.driver.find_elements(By.CSS_SELECTOR, "[role='img'][aria-label*='star']")
                for el in rating_elements:
                    aria = el.get_attribute("aria-label")
                    if aria:
                        m_rate = re.search(r'([345]\.[0-9])', aria)
                        if m_rate:
                            rating = float(m_rate.group(1))
                            break
            except Exception:
                pass

            # Try to get review count
            try:
                review_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'review') or contains(text(), 'Review')]")
                for el in review_elements:
                    text = el.text.strip()
                    m_rev = re.search(r'([\d,]+)\s*(review|Review)', text)
                    if m_rev:
                        review_count = int(m_rev.group(1).replace(',', ''))
                        break
            except Exception:
                pass

            # Try to get opening hours / status
            try:
                for selector in ("[data-item-id='oh']", "div[aria-label*='Hours']", "span[aria-label*='Open']"):
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for el in elements:
                        text = (el.get_attribute('aria-label') or el.text or '').strip()
                        if text:
                            opening_hours = text
                            if 'open' in text.lower():
                                status = 'Open'
                            elif 'closed' in text.lower():
                                status = 'Closed'
                            break
            except Exception:
                pass

            href = current_url if '/maps/place/' in current_url else None
            if not href:
                cards = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
                for card in cards:
                    candidate_name = card.get_attribute("aria-label") or card.text.strip()
                    candidate_href = card.get_attribute("href")
                    if candidate_name and candidate_href:
                        name = name or candidate_name
                        href = candidate_href
                        break

            if href:
                identity = extract_place_identity(gmap_url=href, name=name, address=address)
                if identity['place_key'] and (identity['is_strong'] or not no_results):
                    result.update(self._identity_fields(href, name, address))
                    result.update({
                        "found": True,
                        "state": "PLACE_PROFILE",
                        "name": name or clean_query,
                        "address": address,
                        "category": category,
                        "rating": rating,
                        "review_count": review_count,
                        "opening_hours": opening_hours,
                        "status": status,
                        "google_maps_url": href,
                    })
                    return result

            if no_results:
                result["state"] = "NO_RESULTS"
                result["message"] = "Google Maps found no place for this name"
            else:
                # A navigation timeout is distinct from a genuine "no results".
                # If no usable profile/no-results signal was rendered, preserve
                # the timeout so the API can report an infrastructure failure.
                state = (page_state or {}).get("state")
                if navigation_timed_out and state in (None, "UNKNOWN", "RESULTS"):
                    state = "TIMEOUT"
                elif state in (None, "UNKNOWN", "RESULTS"):
                    state = "SELECTOR_FAILURE"
                result["state"] = state
                result["message"] = ((page_state or {}).get("message")
                                     or "Google Maps loaded but no business profile "
                                        "could be identified.")
            return result
        except Exception as e:
            logger.warning(f"Place resolution failed for {clean_query!r}: {e}")
            result["state"] = result.get("state") or "ERROR"
            result["message"] = "The Google Maps lookup could not be completed on the server."
            return result
        finally:
            self.close_driver()
    def _read_current_place_profile(self, fallback_name: str = None) -> Optional[Dict]:
        """Read Google Maps profile statistics from the currently open page.

        Returns ``{'name', 'address', 'category', 'rating', 'review_count'}``
        or ``None`` when nothing usable could be read. Used by the scrape flow
        so the review-volume / rating charts show real scraped values instead
        of empty placeholders.
        """
        if not self.driver:
            return None

        name = None
        address = None
        category = None
        rating = None
        review_count = None

        try:
            for heading in self.driver.find_elements(By.TAG_NAME, "h1"):
                text = (heading.text or '').strip()
                if text:
                    name = text
                    break
        except Exception:
            pass

        try:
            for selector in ("button[data-item-id='address']", "[data-item-id='address']"):
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    raw = (elements[0].get_attribute('aria-label')
                           or elements[0].text or '')
                    address = raw.replace('Address:', '').strip() or None
                    break
        except Exception:
            pass

        try:
            for selector in ("button[data-item-id='category']", "[data-item-id='category']"):
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    raw = (elements[0].get_attribute('aria-label')
                           or elements[0].text or '')
                    category = raw.strip() or None
                    break
        except Exception:
            pass

        # Rating and the *total* review count.
        # Google renders several star labels on the pane:
        #   "4.3 stars"                 -> the overall rating
        #   "848 reviews"               -> the total number of reviews
        #   "5 stars, 548 reviews"      -> one row of the star breakdown
        # The breakdown rows must never be mistaken for the total.
        try:
            for el in self.driver.find_elements(By.CSS_SELECTOR, "[aria-label*='star']"):
                label = (el.get_attribute('aria-label') or '').strip()
                if not label:
                    continue
                # Skip the per-star breakdown rows.
                if re.match(r'^\s*[1-5]\s*stars?\s*,', label, re.I):
                    continue
                if rating is None:
                    rating_match = re.search(r'([1-5](?:\.[0-9])?)\s*stars?', label, re.I)
                    if rating_match:
                        rating = float(rating_match.group(1))
                count_match = re.search(r'([\d,]+)\s*reviews?\s*$', label, re.I)
                if review_count is None and count_match:
                    review_count = int(count_match.group(1).replace(',', ''))
                if rating is not None and review_count is not None:
                    break
        except Exception:
            pass

        # Total review count fallbacks (labels like "848 reviews" carry no
        # digit before "stars", so they are handled separately).
        if review_count is None:
            try:
                candidates = []
                for selector in (
                    "[aria-label*='reviews']",
                    "[aria-label*='Reviews']",
                    "[data-item-id='reviews']",
                ):
                    try:
                        candidates.extend(self.driver.find_elements(By.CSS_SELECTOR, selector))
                    except Exception:
                        continue
                for el in candidates[:60]:
                    label = (el.get_attribute('aria-label') or el.text or '').strip()
                    match = re.match(r'^\s*([\d,]+)\s*reviews?\s*$', label, re.I)
                    if match:
                        review_count = int(match.group(1).replace(',', ''))
                        break
                if review_count is None:
                    # Last resort: any label that mentions reviews with a number.
                    for el in candidates[:60]:
                        label = (el.get_attribute('aria-label') or el.text or '').strip()
                        match = re.search(r'([\d,]+)\s*reviews?', label, re.I)
                        if match and not re.match(r'^\s*[1-5]\s*stars?\s*,', label, re.I):
                            review_count = int(match.group(1).replace(',', ''))
                            break
            except Exception:
                pass

        # Per-star breakdown as shown on the place page
        # ("5 stars, 548 reviews") - real Google Maps aggregates that the
        # rating distribution chart can use before individual reviews exist.
        rating_distribution = None
        try:
            star_rows = self.driver.find_elements(By.CSS_SELECTOR, "[aria-label*='star']")
            distribution = {}
            for el in star_rows[:30]:
                label = (el.get_attribute('aria-label') or '').strip()
                match = re.match(
                    r'\s*([1-5])\s*stars?\s*,?\s+([\d,]+)\s*reviews?', label, re.I
                )
                if match:
                    distribution[match.group(1)] = int(match.group(2).replace(',', ''))
            if distribution:
                rating_distribution = distribution
        except Exception:
            pass

        # The star breakdown always sums to the total number of reviews, so
        # use it when the count label was missing (or matched a smaller
        # unrelated count elsewhere on the pane).
        if rating_distribution:
            distribution_total = sum(rating_distribution.values())
            if review_count is None or review_count < distribution_total:
                review_count = distribution_total

        if not any((name, address, category, rating is not None, review_count is not None)):
            return None

        # Also capture the star breakdown so the review module has real
        # aggregates even before individual reviews are collected.
        return {
            'name': name or fallback_name,
            'address': address,
            'category': category,
            'rating': rating,
            'review_count': review_count,
            'rating_distribution': rating_distribution,
        }



    def scrape_competitor_posts(self, competitor_name: str, gmap_url: str,
                                window_days: int = 180,
                                include_public: bool = True,
                                industry: Optional[str] = None,
                                expected_address: Optional[str] = None) -> List[Dict]:
        """
        Scrape Google Maps posts for a competitor
        Returns list of post dictionaries (owner updates first, then public)
        window_days: number of days to look back (default 180 for 6 months)
        include_public: also collect public (user generated) content
        industry: topic profile (cafe / salon / fashion / ecommerce / generic)
        expected_address: address stored for this competitor; used to confirm
            the opened place page when Google's result carries a longer name
            (e.g. "Zudio" vs "Zudio - Mahavir Astha").
        """
        if industry:
            self.industry = industry
        if not self.driver:
            self.setup_driver()

        diagnostics = {
            'business_url': gmap_url,
            'competitor_name': competitor_name,
            'page_loaded': False,
            'business_verified': False,
            'updates_section_found': False,
            'updates_section_opened': False,
            'post_containers_found': 0,
            'posts_extracted': 0,
            'owner_posts': 0,
            'public_posts': 0,
            'images_found': 0,
            'scrape_status': 'UNKNOWN',
            'error_message': None,
            'window_days': window_days,
        }

        posts = []
        try:
            logger.info(f"Scraping posts for {competitor_name} at {gmap_url} (window: {window_days} days)")
            self.driver.get(gmap_url)

            # Wait for page to load
            time.sleep(3)

            # Check for CAPTCHA
            if self.handle_captcha():
                diagnostics['scrape_status'] = 'CAPTCHA_REQUIRED'
                raise Exception("CAPTCHA_REQUIRED: Manual verification required")

            diagnostics['page_loaded'] = True

            # A maps/search/ URL can leave Google on the result LIST instead of
            # a place page (h1 = "Results"). Open the first matching listing
            # directly by URL (clicking may open a new tab) so the profile,
            # posts and reviews all describe this business.
            try:
                if '/maps/search/' in (self.driver.current_url or ''):
                    place_links = self.driver.find_elements(
                        By.CSS_SELECTOR, "a[href*='/maps/place/']"
                    )[:6]
                    for link in place_links:
                        href = link.get_attribute('href') or ''
                        if '/maps/place/' in href:
                            self.driver.get(href)
                            time.sleep(4)
                            logger.info(f"Opened place page for {competitor_name}")
                            break
            except Exception as nav_error:
                logger.debug(f"Could not open a place page for {competitor_name}: {nav_error}")

            # Still on the result list? Then nothing on screen belongs to this
            # business, so no profile/posts are taken from it.
            still_on_list = '/maps/search/' in (self.driver.current_url or '')

            # Capture the Google Maps profile statistics while the place page
            # is open (rating / review count / star distribution / address).
            # The API persists these so the review-volume charts use real
            # values. Google renders the review summary lazily (and sometimes
            # only after a scroll), so retry briefly.
            profile = None
            try:
                for attempt in range(4):
                    profile = self._read_current_place_profile(competitor_name)
                    if profile and profile.get('review_count') is not None:
                        break
                    try:
                        self.driver.execute_script("window.scrollBy(0, 500);")
                    except Exception:
                        pass
                    time.sleep(2)
            except Exception as profile_error:
                logger.debug(f"Could not read place profile for {competitor_name}: {profile_error}")
                profile = None

            # Verify we're on the correct business
            verified = not still_on_list
            if still_on_list:
                diagnostics['scrape_status'] = 'LIST_PAGE'
                diagnostics['error_message'] = (
                    'Google Maps stayed on the results list; no place page opened'
                )
                logger.warning(f"Result list page for {competitor_name} - no place page opened")
            elif self._verify_business_page(competitor_name):
                diagnostics['business_verified'] = True
            else:
                # Another business (e.g. the top search hit "The Brew Zone"
                # for a competitor named "The Brew") must never contribute a
                # profile, posts or reviews. The stored address is only used
                # as a diagnostic hint, never to override the name check.
                diagnostics['scrape_status'] = 'BUSINESS_MISMATCH'
                if profile:
                    diagnostics['address_matches_found_page'] = self._addresses_match(
                        expected_address, profile.get('address')
                    )
                verified = False
                logger.warning(f"Business verification failed for {competitor_name} - continuing anyway")

            # Keep the profile only when the opened page really is this
            # business: a maps/search/ URL can land on a different listing
            # (e.g. "Cafe Goodluck" -> "Good Luck Restaurant"), and a wrong
            # profile would poison the review charts.
            if profile and verified:
                self.last_place_profiles[competitor_name] = profile
                diagnostics['place_profile'] = profile
            elif profile:
                diagnostics['place_profile_rejected'] = (
                    'result list page' if still_on_list else 'business name mismatch'
                )

            if still_on_list:
                # Nothing below belongs to this business: return empty rather
                # than store other listings' posts/reviews as our data.
                diagnostics['posts_extracted'] = 0
                diagnostics['scrape_status'] = 'NO_POSTS'
                logger.info(f"Skipped scraping {competitor_name}: no place page opened")
                self.last_run_diagnostics[competitor_name] = diagnostics
                return []

            # Try to find the posts section
            posts_section = self._find_posts_section()

            if posts_section:
                diagnostics['updates_section_found'] = True
                diagnostics['updates_section_opened'] = True
                # Owner updates are extracted first and keep their priority.
                posts = self._extract_posts_from_section(
                    posts_section, competitor_name, window_days, post_source='owner'
                )
                diagnostics['post_containers_found'] = len(posts)
            else:
                # Check if the business has an Updates tab at all
                has_updates = self._check_has_updates_tab()
                if has_updates:
                    diagnostics['scrape_status'] = 'UPDATES_SECTION_NOT_FOUND'
                    logger.warning(f"Updates tab exists but could not extract posts for {competitor_name}")
                else:
                    diagnostics['scrape_status'] = 'NO_POSTS'
                    logger.info(f"No Updates/Posts section found for {competitor_name} - business may not have Google Maps posts")

            # Owner updates keep priority: public (user generated) content is
            # appended afterwards and is never mixed into the owner block.
            if include_public:
                try:
                    public_posts = self._extract_public_posts(
                        competitor_name, window_days, industry=industry
                    )
                    if public_posts:
                        posts = list(posts) + public_posts
                except Exception as public_error:
                    diagnostics['public_content_error'] = str(public_error)
                    logger.warning(
                        f"Public content collection failed for {competitor_name}: {public_error}"
                    )

        except Exception as e:
            error_msg = str(e)
            if "CAPTCHA_REQUIRED" in error_msg:
                diagnostics['scrape_status'] = 'CAPTCHA_REQUIRED'
                raise Exception("CAPTCHA_REQUIRED")
            elif "TIMEOUT" in error_msg.lower() or isinstance(e, TimeoutException):
                diagnostics['scrape_status'] = 'TIMEOUT'
                raise Exception("TIMEOUT")
            else:
                diagnostics['scrape_status'] = 'SCRAPER_ERROR'
                diagnostics['error_message'] = error_msg
                logger.error(f"Unexpected error while scraping {competitor_name}: {e}")
                raise Exception(f"SCRAPER_ERROR: {error_msg}")

        diagnostics['posts_extracted'] = len(posts)
        diagnostics['owner_posts'] = sum(
            1 for post in posts if (post or {}).get('post_source') != 'public'
        )
        diagnostics['public_posts'] = sum(
            1 for post in posts if (post or {}).get('post_source') == 'public'
        )
        diagnostics['images_found'] = sum(
            len((post or {}).get('image_urls') or []) for post in posts
        )
        logger.info(f"Scrape diagnostics for {competitor_name}: {diagnostics}")
        self.last_run_diagnostics[competitor_name] = diagnostics

        return posts

    def _generate_content_hash(self, post: Dict) -> str:
        """Generate a hash for duplicate detection"""
        import hashlib
        content = f"{post.get('post_url', '')}{post.get('text_content', '')}{post.get('published_date', '')}{post.get('competitor_name', '')}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:32]

    def _detect_topic_and_keywords(self, text: str,
                                   industry: Optional[str] = None) -> Tuple[str, List[str]]:
        """Detect topic and keywords from post text.

        Delegates to the shared industry-aware classifier so a cafe review is
        never labelled with fashion topics (and vice versa). The industry comes
        from the project field / profile via ``infer_industry``.
        """
        return classify_topic(text, industry=industry or self.industry)

    def _parse_date(self, date_text: str) -> Optional[str]:
        """Parse various date formats from Google Maps to ISO format, or return None if unparseable"""
        if not date_text:
            return None
            
        date_text = date_text.strip()
        now = datetime.now()
        date_text_lower = date_text.lower()
        
        # Relative single-unit patterns
        if 'yesterday' in date_text_lower:
            return (now - timedelta(days=1)).isoformat()
        if re.search(r'\b(a|an)\s+day\s+ago\b', date_text_lower):
            return (now - timedelta(days=1)).isoformat()
        if re.search(r'\b(a|an)\s+week\s+ago\b', date_text_lower):
            return (now - timedelta(weeks=1)).isoformat()
        if re.search(r'\b(a|an)\s+month\s+ago\b', date_text_lower):
            return (now - timedelta(days=30)).isoformat()
        if re.search(r'\b(a|an)\s+hour\s+ago\b', date_text_lower):
            return (now - timedelta(hours=1)).isoformat()
        
        # Handle relative dates like "2 days ago", "3 weeks ago", "1 month ago", "2 hours ago"
        relative_match = re.search(r'(\d+)\s*(day|week|month|hour|minute)s?\s*ago', date_text, re.IGNORECASE)
        if relative_match:
            num = int(relative_match.group(1))
            unit = relative_match.group(2).lower()
            if unit.startswith('hour'):
                delta = timedelta(hours=num)
            elif unit.startswith('minute'):
                delta = timedelta(minutes=num)
            elif unit.startswith('day'):
                delta = timedelta(days=num)
            elif unit.startswith('week'):
                delta = timedelta(weeks=num)
            elif unit.startswith('month'):
                delta = timedelta(days=num * 30)
            else:
                delta = timedelta(days=num)
            return (now - delta).isoformat()
            
        # Search for date pattern like "Sep 12, 2026" or "12 Sep 2026" inside date_text
        date_match = re.search(r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b', date_text, re.I)
        if date_match:
            clean_date_str = date_match.group(0).replace(',', '')
            for fmt in ['%b %d %Y', '%B %d %Y']:
                try:
                    return datetime.strptime(clean_date_str, fmt).isoformat()
                except:
                    continue
        
        # Try absolute date formats directly
        for fmt in ['%b %d, %Y', '%B %d, %Y', '%m/%d/%Y', '%Y-%m-%d', '%d %b %Y', '%d %B %Y', '%b %d', '%B %d']:
            try:
                parsed = datetime.strptime(date_text, fmt)
                if parsed.year == 1900:
                    parsed = parsed.replace(year=now.year)
                return parsed.isoformat()
            except:
                continue
        
        return None

    def _is_within_six_months(self, date_str: Optional[str]) -> bool:
        """Check if a date is within the last 180 days (6 months)"""
        return self._is_within_window(date_str, 180)

    def _is_within_window(self, date_str: Optional[str], days: int = 180) -> bool:
        """Check if a date is within the specified window (default 180 days / 6 months)"""
        if not date_str:
            return True
        try:
            from datetime import datetime, timedelta
            clean_date = date_str.replace('Z', '+00:00')
            if '+' in clean_date:
                post_date = datetime.fromisoformat(clean_date).replace(tzinfo=None)
            else:
                post_date = datetime.fromisoformat(clean_date)
            cutoff = datetime.now() - timedelta(days=days)
            return post_date >= cutoff
        except:
            return True

    def _scroll_to_load_posts(self, posts_section, window_days: int = 180) -> List:
        """Continuously scroll to load more posts until window cutoff or max scrolls reached"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        import time
        
        logger.info(f"Starting continuous scroll to load posts (window: {window_days} days)...")
        
        post_elements = []
        last_count = 0
        no_new_posts_count = 0
        
        for scroll_num in range(30):
            # Find current post elements
            current_elements = []
            selectors = [
                ".//div[contains(@class, 'section-post')]",
                ".//article",
                ".//div[@role='article']",
                ".//div[contains(@class, 'post-item')]",
                ".//div[contains(@data-item-id, 'post')]",
                ".//div[contains(@jsaction, 'post')]",
            ]
            
            for selector in selectors:
                try:
                    current_elements = posts_section.find_elements(By.XPATH, selector)
                    if current_elements:
                        break
                except:
                    continue
            
            # Also try fallback
            if not current_elements:
                try:
                    current_elements = posts_section.find_elements(By.XPATH, ".//div[.//text()[string-length() > 50]]")
                except:
                    pass
            
            # Check if we found new posts
            if len(current_elements) > last_count:
                last_count = len(current_elements)
                no_new_posts_count = 0
            else:
                no_new_posts_count += 1
            
            # Check if we've reached window cutoff by examining the last few posts
            if len(current_elements) > 5:
                recent_posts = current_elements[-5:]
                all_old = True
                for elem in recent_posts:
                    try:
                        # Try to extract date from this element
                        date_text = None
                        for selector in [".//span[contains(@class, 'section-post-date')]", ".//span[contains(@class, 'post-date')]", ".//time", ".//*[contains(@aria-label, 'ago')]", ".//*[contains(text(), 'ago')]", ".//*[@datetime]"]:
                            try:
                                date_elem = elem.find_element(By.XPATH, selector)
                                date_text = date_elem.get_attribute('aria-label') or date_elem.get_attribute('datetime') or date_elem.text
                                if date_text:
                                    date_text = date_text.strip()
                                    break
                            except:
                                continue
                        if date_text:
                            parsed_date = self._parse_date(date_text)
                            if self._is_within_window(parsed_date, window_days):
                                all_old = False
                                break
                    except:
                        continue
                
                if all_old:
                    logger.info(f"Reached posts older than {window_days} days, stopping scroll")
                    break
            
            # If no new posts for 5 consecutive scrolls, we've reached the end
            if no_new_posts_count >= 5:
                logger.info("No new posts found after 5 scrolls, stopping")
                break
            
            # Scroll down
            try:
                self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", posts_section)
            except:
                try:
                    # Alternative: send END key to the section
                    posts_section.send_keys(Keys.END)
                except:
                    pass
            
            time.sleep(1.5)  # Wait for new content to load
        
        # Final collection of all post elements
        final_elements = []
        for selector in [
            ".//div[contains(@class, 'section-post')]",
            ".//article",
            ".//div[@role='article']",
            ".//div[contains(@class, 'post-item')]",
            ".//div[contains(@data-item-id, 'post')]",
            ".//div[contains(@jsaction, 'post')]",
        ]:
            try:
                elements = posts_section.find_elements(By.XPATH, selector)
                if elements:
                    final_elements = elements
                    break
            except:
                continue
        
        if not final_elements:
            try:
                final_elements = posts_section.find_elements(By.XPATH, ".//div[.//text()[string-length() > 50]]")
            except:
                pass
        
        logger.info(f"Total post elements collected after scrolling: {len(final_elements)}")
        return final_elements

    def _check_has_updates_tab(self) -> bool:
        """Check if the business has an Updates/Posts tab"""
        selectors = [
            "//button[@role='tab' and contains(., 'Updates')]",
            "//button[contains(@aria-label, 'Updates')]",
            "//div[@role='tab'][contains(text(), 'Updates')]",
            "//button[contains(text(), 'Updates')]",
            "//button[contains(@aria-label, 'Posts')]",
            "//div[@role='tab'][contains(text(), 'Posts')]",
        ]
        
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for el in elements:
                    if el.is_displayed():
                        return True
            except:
                continue
        return False

    def _verify_business_page(self, expected_name: str) -> bool:
        """Verify that the loaded page matches the expected business"""
        try:
            # Try to find the business name on the page
            name_selectors = [
                "//h1[contains(@class, 'section-hero-header-title')]",
                "//h1[@data-attrid='title']",
                "//h1[contains(@class, 'fontHeadlineLarge')]",
                "//h1",
            ]
            
            for selector in name_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for el in elements:
                        text = (el.text or '').strip()
                        if text and self._names_match(text, expected_name):
                            logger.info(f"Business verified: found '{text}' matches expected '{expected_name}'")
                            return True
                except:
                    continue
            
            # Also check URL for place identity
            current_url = self.driver.current_url
            logger.warning(f"Could not verify business name on page. Current URL: {current_url}")
            return False
        except Exception as e:
            logger.error(f"Error verifying business page: {e}")
            return False

    def _names_match(self, found_name: str, expected_name: str) -> bool:
        """Compare business names with conservative fuzzy matching.

        The two names must be the same business: an exact match, or one name
        with only *qualifier* words added (branch, city, "Cafe", "Store").
        "The Brew" must NOT match "The Brew Zone" (a different cafe) and
        "Cafe Goodluck" must not match "Good Luck Restaurant" — otherwise
        another business' rating/reviews would be stored as ours.
        """
        import re
        QUALIFIERS = {
            'the', 'cafe', 'cafes', 'coffee', 'restaurant', 'rest', 'resto',
            'shop', 'stores', 'store', 'kitchen', 'house', 'co', 'and', 'near',
            'west', 'east', 'north', 'south', 'central', 'bandra', 'mumbai',
            'india', 'in', 'at', 'by', 'of', 'unit', 'road', 'rd', 'st',
            'branch', 'outlet', 'the', 'corner', 'place', 'center', 'centre',
            'city', 'gallery', 'junction', 'pvt', 'ltd', 'limited', 'nearby',
        }

        def tokens(value):
            return [t for t in re.findall(r'[a-z0-9]+', value.lower()) if t]

        found = tokens(found_name)
        expected = tokens(expected_name)
        if not found or not expected:
            return False

        found_joined = ''.join(found)
        expected_joined = ''.join(expected)
        if found_joined == expected_joined:
            return True

        longer, shorter = (found, expected) if len(found_joined) >= len(expected_joined) else (expected, found)
        joined_longer, joined_shorter = ''.join(longer), ''.join(shorter)
        if joined_shorter not in joined_longer:
            return False

        # Only qualifier words may make up the difference between the names.
        extra = [word for word in longer if word not in shorter]
        return all(word in QUALIFIERS for word in extra)

    def _addresses_match(self, expected_address: str, found_address: Optional[str]) -> bool:
        """Conservative address comparison used to confirm an opened listing.

        Two addresses match when one contains the other or they share a
        distinctive token (a building/sector number or a street name). Generic
        words like "road", "west" or "mumbai" never count on their own, so
        "5, S. P. Road, Bandra West" does not match "2, Chapel Rd, Bandra".
        """
        import re
        if not expected_address or not found_address:
            return False

        def normalize(value):
            return re.sub(r'[^a-z0-9]+', ' ', value.lower()).strip()

        norm_expected = normalize(expected_address)
        norm_found = normalize(found_address)
        if not norm_expected or not norm_found:
            return False
        if norm_expected in norm_found or norm_found in norm_expected:
            return True

        generic = {
            'road', 'rd', 'street', 'st', 'west', 'east', 'north', 'south',
            'mumbai', 'maharashtra', 'india', 'near', 'opposite', 'opp',
            'ground', 'floor', 'building', 'colony', 'nagar', 'naka', 'main',
            'first', 'second', 'third', 'bandra', 'sector', 'shop', 'flat',
            'no', 'and', 'the', 'kamothe', 'panvel', 'navi',
        }

        def distinctive(value):
            tokens = set()
            for token in value.split():
                if token.isdigit():
                    # Building / shop / sector numbers count; postal codes do
                    # not (every address in one district shares the pin code).
                    if len(token) <= 3:
                        tokens.add(token)
                elif len(token) >= 4 and token not in generic:
                    tokens.add(token)
            return tokens

        exp_distinct = distinctive(norm_expected)
        found_distinct = distinctive(norm_found)
        if not exp_distinct or not found_distinct:
            return False

        exp_numbers = {t for t in exp_distinct if t.isdigit()}
        found_numbers = {t for t in found_distinct if t.isdigit()}
        # Different door / sector numbers => different places.
        if exp_numbers and found_numbers and exp_numbers.isdisjoint(found_numbers):
            return False

        # Require a shared anchor: street/establishment name or the number.
        shared_words = (exp_distinct - exp_numbers) & (found_distinct - found_numbers)
        shared_numbers = exp_numbers & found_numbers
        return bool(shared_words or shared_numbers)

    def _find_posts_section(self):
        """Find the posts/updates section on Google Maps page"""
        logger.info("Attempting to find Updates/Posts section...")
        
        # First, try to find and click the "Updates" tab/button if present
        updates_tab_selectors = [
            "//button[@role='tab' and contains(., 'Updates')]",
            "//button[contains(@aria-label, 'Updates')]",
            "//div[@role='tab'][contains(text(), 'Updates')]",
            "//a[contains(@href, 'updates')]",
            "//button[contains(text(), 'Updates')]",
            "//div[contains(@class, 'section-tab') and contains(., 'Updates')]",
            "//button[contains(@aria-label, 'Posts')]",
            "//div[@role='tab'][contains(text(), 'Posts')]",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'update')]",
            "//div[@role='tab'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'update')]",
        ]
        
        clicked = False
        for selector in updates_tab_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                for el in elements:
                    if el.is_displayed():
                        logger.info(f"Found Updates tab with selector: {selector}")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", el)
                        clicked = True
                        logger.info("Clicked Updates tab, waiting for posts to load...")
                        time.sleep(3)
                        break
                if clicked:
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} failed: {e}")
                continue
        
        # If no Updates tab, check for "From the owner" / "See local posts" card on Overview
        if not clicked:
            owner_card_selectors = [
                "//*[@aria-label='See local posts']",
                "//div[contains(@class, 'SBD2Rc')]",
                "//div[contains(@jsaction, 'local-post.expand')]",
                "//div[contains(@jsaction, 'localPost')]",
                "//*[contains(text(), 'From the owner')]/ancestor::div[contains(@class, 'S3NLN')]//div[@role='button']",
            ]
            for selector in owner_card_selectors:
                try:
                    elements = self.driver.find_elements(By.XPATH, selector)
                    for el in elements:
                        logger.info(f"Found 'See local posts' card with selector: {selector}")
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", el)
                        time.sleep(0.5)
                        self.driver.execute_script("arguments[0].click();", el)
                        clicked = True
                        logger.info("Clicked 'See local posts' card, waiting for posts to expand...")
                        time.sleep(3)
                        break
                    if clicked:
                        break
                except Exception as e:
                    logger.debug(f"Owner card selector {selector} failed: {e}")
                    continue

        # Now try to find the posts feed / container
        feed_selectors = [
            "//div[contains(@class, 'm6QErb') and contains(@class, 'DxyBCb')]",
            "//div[contains(@class, 'm6QErb') and .//div[contains(@class, 'cKbrCd')]]",
            "//div[contains(@class, 'cKbrCd')]/..",
            "//div[@role='feed']",
            "//div[contains(@aria-label, 'Updates')]",
            "//div[contains(@aria-label, 'Posts')]",
            "//div[contains(@class, 'section-listbox') and .//div[contains(@class, 'section-post')]]",
            "//div[contains(@class, 'posts-container')]",
            "//div[contains(@class, 'section-post-list')]",
            "//div[contains(@class, 'pane-content')]",
            "//div[contains(@class, 'widget-pane-content')]",
        ]
        
        for selector in feed_selectors:
            try:
                elements = self.driver.find_elements(By.XPATH, selector)
                if elements and elements[0].is_displayed():
                    logger.info(f"Found posts section using selector: {selector}")
                    return elements[0]
            except Exception:
                continue

        # Fallback: check if any post elements exist in the page
        if self.driver.find_elements(By.XPATH, "//div[contains(@class, 'cKbrCd')] | //div[contains(@class, 'SBD2Rc')] | //div[contains(@class, 'section-post')]"):
            logger.info("Found post elements directly in DOM")
            try:
                return self.driver.find_element(By.XPATH, "//div[contains(@class, 'm6QErb')] | //body")
            except:
                return self.driver.find_element(By.TAG_NAME, "body")
        
        logger.warning("Could not find posts feed with any selector")
        return None

    def _extract_posts_from_section(self, posts_section, competitor_name: str,
                                    window_days: int = 180,
                                    post_source: str = 'owner') -> List[Dict]:
        """Extract individual posts from the posts section with continuous scrolling.

        Owner updates have priority: the updates feed is always extracted first
        and the returned list is owner-first.
        """
        posts = []

        try:
            # Use continuous scrolling to load all posts within window
            post_elements = self._scroll_to_load_posts(posts_section, window_days)
            
            # If no elements found from section, search driver directly
            if not post_elements:
                post_elements = self.driver.find_elements(
                    By.XPATH,
                    "//div[contains(@class, 'cKbrCd')] | //div[contains(@class, 'SBD2Rc')] | //div[contains(@class, 'section-post')] | //article | //div[@role='article']"
                )
            
            logger.info(f"Total post elements to process: {len(post_elements)}")
            
            seen_hashes = set()
            for i, post_element in enumerate(post_elements[:100]):  # Process up to 100 posts
                try:
                    post_data = self._extract_single_post(post_element, competitor_name, i, post_source)
                    if post_data and post_data.get('text_content'):
                        # Deduplicate in-memory
                        h = post_data.get('content_hash')
                        if h in seen_hashes:
                            continue
                        seen_hashes.add(h)
                        
                        # Filter by window (default 180 days / 6 months)
                        if self._is_within_window(post_data.get('published_date'), window_days):
                            posts.append(post_data)
                            logger.info(f"Extracted post {len(posts)}: [{post_data.get('published_date')}] ({post_data.get('detected_topic')}) {post_data['text_content'][:50]}...")
                        else:
                            logger.info(f"Skipping post older than {window_days} days: {post_data.get('published_date')}")
                except Exception as e:
                    logger.debug(f"Error extracting post {i}: {e}")
                    continue
            
            logger.info(f"Successfully extracted {len(posts)} posts within {window_days}-day window")

        except Exception as e:
            logger.error(f"Error extracting posts: {e}")

        return posts

    def _extract_single_post(self, post_element, competitor_name: str, index: int,
                             post_source: str = 'owner') -> Optional[Dict]:
        """Extract data from a single post element.

        `post_source` is 'owner' for updates published by the profile owner and
        'public' for content published by the public (reviews / community
        posts). Elements that clearly carry user-generated markers are re-tagged
        as public even when they were picked up from the updates feed.
        """
        try:
            if post_source != 'public' and self._looks_like_public_content(post_element):
                post_source = 'public'
            post_data = {
                'competitor_name': competitor_name,
                'post_url': None,
                'text_content': None,
                'published_date': None,
                'image_urls': [],
                'cta': None,
                'detected_topic': None,
                'detected_keywords': [],
                'raw_data': {},
                'post_source': post_source,
            }
            
            # Extract post URL/link (including data-sharing-url from Google Maps share button)
            link_selectors = [
                ".//button[@data-sharing-url]",
                ".//button[contains(@class, 'JYn65')]",
                ".//button[@data-report-post-url]",
                ".//a[contains(@href, '/local/posts')]",
                ".//a[contains(@href, '/maps/place/') and contains(@href, 'post')]",
                ".//a[contains(@href, 'post')]",
                ".//a[contains(@href, 'update')]",
                ".//a[contains(@href, '/maps/')]",
            ]
            for selector in link_selectors:
                try:
                    link_element = post_element.find_element(By.XPATH, selector)
                    url = link_element.get_attribute('data-sharing-url') or link_element.get_attribute('data-report-post-url') or link_element.get_attribute('href')
                    if url:
                        post_data['post_url'] = url.replace('&amp;', '&')
                        break
                except:
                    continue
            
            # Extract post text - support modern Google Maps classes
            text_selectors = [
                ".//div[contains(@class, 'hfJtQe')]",
                ".//div[contains(@class, 'VpMB0')]",
                ".//div[contains(@class, 'Rfb4Xc')]",
                ".//div[contains(@class, 'section-post-text')]",
                ".//div[contains(@class, 'post-text')]",
                ".//div[contains(@class, 'section-post-content')]",
                ".//span[contains(@class, 'section-post-text')]",
                ".//div[contains(@class, 'text')]",
                ".//p",
            ]
            for selector in text_selectors:
                try:
                    text_element = post_element.find_element(By.XPATH, selector)
                    text = (text_element.get_attribute('textContent') or text_element.text or '').strip()
                    if text and len(text) > 5:
                        post_data['text_content'] = text[:5000]
                        break
                except:
                    continue
            
            # Fallback to all text if no specific selector matched
            if not post_data['text_content']:
                try:
                    all_text = (post_element.get_attribute('textContent') or post_element.text or '').strip()
                    if all_text and len(all_text) > 5:
                        post_data['text_content'] = all_text[:5000]
                except:
                    pass
            
            # Extract published date - support modern Google Maps classes
            date_selectors = [
                ".//div[contains(@class, 'mgX1W')]",
                ".//div[contains(@class, 'lqMB')]",
                ".//span[contains(@class, 'section-post-date')]",
                ".//span[contains(@class, 'post-date')]",
                ".//time",
                ".//*[contains(@aria-label, 'ago')]",
                ".//*[contains(text(), 'ago')]",
                ".//*[@datetime]",
            ]
            for selector in date_selectors:
                try:
                    date_element = post_element.find_element(By.XPATH, selector)
                    date_text = (
                        date_element.get_attribute('aria-label')
                        or date_element.get_attribute('datetime')
                        or date_element.get_attribute('textContent')
                        or date_element.text
                        or ''
                    ).strip()
                    if date_text:
                        parsed = self._parse_date(date_text)
                        if parsed:
                            post_data['published_date'] = parsed
                            break
                except:
                    continue
            
            # Regex fallback for date from element textContent
            if not post_data['published_date']:
                try:
                    raw_text = post_element.get_attribute('textContent') or ''
                    date_m = re.search(r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{4}\b', raw_text, re.I)
                    if date_m:
                        post_data['published_date'] = self._parse_date(date_m.group(0))
                except:
                    pass

            if not post_data['published_date']:
                # Authentic posts always have a publication date on Google Maps.
                # Skip preview/snippet elements without dates to prevent duplicate entries.
                return None
            
            # Extract images (exclude avatar icons)
            try:
                img_elements = post_element.find_elements(By.XPATH, ".//img[contains(@class, 'tTCrvf')] | .//div[contains(@class, 'oHJe9')]//img | .//img")
                for img in img_elements:
                    src = img.get_attribute('src')
                    if src and 'http' in src and ('google' in src or 'maps' in src or 'lh3' in src):
                        if 's40-c-k-mo' not in src and 'photo.jpg' not in src:
                            if src not in post_data['image_urls']:
                                post_data['image_urls'].append(src)
                
                # Check background-image styles
                divs = post_element.find_elements(By.XPATH, ".//div[contains(@class, 'EvLOsc')] | .//div[contains(@style, 'background-image')]")
                for div in divs:
                    style = div.get_attribute('style') or ''
                    m = re.search(r'url\(["\']?(https://[^"\'\)]+)["\']?\)', style)
                    if m and m.group(1) not in post_data['image_urls']:
                        post_data['image_urls'].append(m.group(1))
            except:
                pass
            
            # Extract CTA (Call to Action) buttons and links
            cta_selectors = [
                ".//a[contains(@class, 'ABZ6xb')]",
                ".//div[contains(@class, 'sGOmPe')]",
                ".//a[contains(@data-tel, 'tel:')]",
                ".//button[contains(@class, 'cta')]",
                ".//button[contains(@class, 'action-button')]",
                ".//a[contains(@class, 'cta')]",
                ".//button[contains(text(), 'Book') or contains(text(), 'Call') or contains(text(), 'Order') or contains(text(), 'Learn')]",
            ]
            cta_texts = []
            for selector in cta_selectors:
                try:
                    cta_elements = post_element.find_elements(By.XPATH, selector)
                    for elem in cta_elements:
                        text = elem.text.strip()
                        if text and text not in cta_texts:
                            cta_texts.append(text)
                except:
                    continue
            if cta_texts:
                post_data['cta'] = " | ".join(cta_texts)
            
            # Detect topic and keywords
            if post_data['text_content']:
                topic, keywords = self._detect_topic_and_keywords(post_data['text_content'])
                post_data['detected_topic'] = topic
                post_data['detected_keywords'] = keywords

            # Generate content hash for deduplication
            post_data['content_hash'] = self._generate_content_hash(post_data)
            
            # Return post if we got meaningful text content
            if post_data['text_content'] and len(post_data['text_content']) > 5:
                return post_data

        except Exception as e:
            logger.error(f"Error extracting single post: {e}")

        return None

    # Markers that identify user generated (public) content instead of an
    # update published by the business owner.
    PUBLIC_CONTENT_MARKERS = (
        'local guide', 'localguide', 'review', 'reviews', 'rated ', 'stars',
        'google user', 'people found this review', 'was this review',
    )
    OWNER_CONTENT_MARKERS = (
        'from the owner', 'local post', 'learn more', 'book now', 'order online',
        'shop now', 'call now', 'sign up', 'updates',
    )

    def _looks_like_public_content(self, post_element) -> bool:
        """True when a post element is user generated (public) content."""
        try:
            text = (post_element.get_attribute('textContent') or post_element.text or '').lower()
            classes = (post_element.get_attribute('class') or '').lower()
            aria_labels = []
            for el in post_element.find_elements(By.XPATH, ".//*[@aria-label]")[:12]:
                try:
                    aria_labels.append((el.get_attribute('aria-label') or '').lower())
                except Exception:
                    continue
            haystack = f"{classes} {' '.join(aria_labels)} {text}"
        except Exception:
            return False

        if any(marker in haystack for marker in self.OWNER_CONTENT_MARKERS):
            return False
        return any(marker in haystack for marker in self.PUBLIC_CONTENT_MARKERS)

    def _extract_public_posts(self, competitor_name: str, window_days: int = 180,
                              limit: int = 20,
                              industry: Optional[str] = None) -> List[Dict]:
        """Collect *public* (user generated) content for one business.

        Google Maps listings mix updates published by the owner with content
        published by the public (reviews, community posts). Public posts are
        collected separately, tagged `post_source='public'` and stay hidden in
        the UI until the user asks to see them.

        Review ratings (``aria-label="5 stars"``) are captured so the API can
        persist them as real review rows for the review-intelligence module.
        """
        if not self.driver:
            return []

        posts: List[Dict] = []
        selectors = [
            "//div[@data-review-id]",
            "//div[contains(@class, 'jftiEf')]",
            "//div[@role='article'][.//*[contains(@aria-label, 'stars')]]",
            "//div[@role='article'][.//*[contains(@aria-label, 'star')]]",
        ]
        seen_hashes = set()
        try:
            elements = []
            for selector in selectors:
                try:
                    found = self.driver.find_elements(By.XPATH, selector)
                except Exception:
                    continue
                if found:
                    elements = found
                    break

            for element in elements[:limit]:
                try:
                    text = (element.get_attribute('textContent') or element.text or '').strip()
                    if not text or len(text) < 20:
                        continue

                    author = None
                    for author_selector in (".//*[contains(@class, 'd4r55')]",
                                            ".//*[contains(@class, 'TSUbDb')]",
                                            ".//button[@aria-label]"):
                        try:
                            author_el = element.find_element(By.XPATH, author_selector)
                            author = (
                                author_el.get_attribute('aria-label') or author_el.text or ''
                            ).strip() or None
                            if author:
                                break
                        except Exception:
                            continue

                    relative_date = ''
                    try:
                        date_el = element.find_element(
                            By.XPATH,
                            ".//*[contains(@class, 'rsqaWe')] | .//span[contains(text(), 'ago')]",
                        )
                        relative_date = (
                            date_el.get_attribute('textContent') or date_el.text or ''
                        ).strip()
                    except Exception:
                        relative_date = ''

                    # Star rating of the review card ("aria-label=5 stars").
                    rating = None
                    try:
                        star_el = element.find_element(
                            By.XPATH, ".//*[@role='img'][contains(@aria-label, 'star')]"
                        )
                        star_label = star_el.get_attribute('aria-label') or ''
                        star_match = re.search(r'(\d(?:\.\d)?)', star_label)
                        if star_match:
                            rating = int(float(star_match.group(1)))
                    except Exception:
                        rating = None

                    published_date = self._parse_date(relative_date) if relative_date else None
                    # Reviews without a parseable date cannot be placed on the
                    # timeline and are usually Google Maps place-suggestion
                    # cards from a results list - never store those.
                    if not published_date or not self._is_within_window(published_date, window_days):
                        continue

                    payload = {
                        'competitor_name': competitor_name,
                        'post_url': None,
                        'text_content': text[:5000],
                        'published_date': published_date,
                        'image_urls': [],
                        'cta': None,
                        'detected_topic': None,
                        'detected_keywords': [],
                        'post_source': 'public',
                        'rating': rating,
                        'raw_data': {
                            'post_source': 'public',
                            'content_type': 'public_content',
                            'author': author,
                            'relative_date': relative_date or None,
                            'rating': rating,
                        },
                    }
                    topic, keywords = self._detect_topic_and_keywords(
                        payload['text_content'], industry=industry
                    )
                    payload['detected_topic'] = topic
                    payload['detected_keywords'] = keywords
                    content_hash = self._generate_content_hash(payload)
                    if content_hash in seen_hashes:
                        continue
                    seen_hashes.add(content_hash)
                    payload['content_hash'] = content_hash
                    posts.append(payload)
                except Exception as element_error:
                    logger.debug(
                        f"Skipping public content element for {competitor_name}: {element_error}"
                    )
                    continue
        except Exception as e:
            logger.warning(f"Could not collect public content for {competitor_name}: {e}")

        if posts:
            logger.info(f"Collected {len(posts)} public posts for {competitor_name}")
        return posts


    def handle_captcha(self) -> bool:
        """
        Detect and handle CAPTCHA/challenge screens
        Returns True if CAPTCHA was detected and handled, False otherwise
        """
        try:
            # Common CAPTCHA indicators
            captcha_indicators = [
                "//div[contains(text(), 'verify')]",
                "//div[contains(text(), 'Verify')]",
                "//div[contains(text(), 'CAPTCHA')]",
                "//div[contains(@class, 'captcha')]",
                "//iframe[contains(@src, 'recaptcha')]"
            ]

            for indicator in captcha_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        logger.warning("CAPTCHA detected - manual intervention required")
                        # In a real implementation, we might pause and notify user
                        # For now, we'll just log and continue
                        return True
                except:
                    continue

            return False
        except Exception as e:
            logger.error(f"Error checking for CAPTCHA: {e}")
            return False

    def scrape_multiple_competitors(self, competitors: List[Dict],
                                    include_public: bool = True,
                                    window_days: int = 180,
                                    industry: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Scrape posts for multiple competitors
        Returns dictionary mapping competitor name to list of posts

        Every competitor's run statistics (start/end time, posts found, new
        posts, duplicates, images, failures and CAPTCHA status) are recorded in
        `self.last_run_diagnostics` for the persistent scraping log.
        """
        all_posts = {}
        self.last_run_diagnostics = {}
        if industry:
            self.industry = industry

        try:
            self.setup_driver()

            for competitor in competitors:
                name = competitor['name']
                gmap_url = competitor['gmap_url']
                started_at = datetime.now()
                detail = {
                    'competitor': name,
                    'gmap_url': gmap_url,
                    'start_time': started_at.isoformat(),
                    'status': 'SUCCESS',
                    'error': None,
                    'captcha_required': False,
                    'posts_found': 0,
                    'owner_posts': 0,
                    'public_posts': 0,
                    'images_downloaded': 0,
                }

                if not gmap_url:
                    logger.warning(f"No Google Maps URL for competitor {name}, skipping")
                    detail['status'] = 'NO_URL'
                    detail['error'] = 'No Google Maps URL configured for this competitor'
                    detail['end_time'] = datetime.now().isoformat()
                    self.last_run_diagnostics[name] = detail
                    all_posts[name] = []
                    continue

                try:
                    posts = self.scrape_competitor_posts(
                        name, gmap_url, window_days=window_days,
                        include_public=include_public, industry=industry,
                        expected_address=competitor.get('address'),
                    )
                    # Per-place diagnostics recorded inside the run: did the
                    # opened page really belong to this business, and was the
                    # profile kept or rejected? Needed by the API before it
                    # persists reviews.
                    inner = dict(self.last_run_diagnostics.get(name) or {})
                    if 'business_verified' in inner:
                        detail['business_verified'] = inner['business_verified']
                    if inner.get('place_profile_rejected'):
                        detail['place_profile_rejected'] = inner['place_profile_rejected']
                    all_posts[name] = posts
                    detail['posts_found'] = len(posts)
                    detail['owner_posts'] = sum(
                        1 for post in posts if (post or {}).get('post_source') != 'public'
                    )
                    detail['public_posts'] = sum(
                        1 for post in posts if (post or {}).get('post_source') == 'public'
                    )
                    detail['images_downloaded'] = sum(
                        len((post or {}).get('image_urls') or []) for post in posts
                    )
                    profile = self.last_place_profiles.get(name)
                    if profile:
                        detail['place_profile'] = profile
                    detail['status'] = 'SUCCESS' if posts else 'NO_POSTS'
                    logger.info(f"Scraped {len(posts)} posts for {name}")

                    # Add delay between competitors to avoid rate limiting
                    time.sleep(2)

                except Exception as e:
                    error_str = str(e)
                    all_posts[name] = []
                    if "CAPTCHA_REQUIRED" in error_str:
                        detail['status'] = 'CAPTCHA_REQUIRED'
                        detail['captcha_required'] = True
                        detail['error'] = 'CAPTCHA_REQUIRED: manual verification required'
                        logger.error(f"CAPTCHA required for {name}")
                    elif "TIMEOUT" in error_str:
                        detail['status'] = 'TIMEOUT'
                        detail['error'] = 'TIMEOUT: Google Maps page load timed out'
                        logger.error(f"Timeout scraping {name}")
                    else:
                        detail['status'] = 'FAILED'
                        detail['error'] = f"SCRAPER_ERROR: {error_str}"
                        logger.error(f"Failed to scrape competitor {name}: {e}")
                finally:
                    detail['end_time'] = datetime.now().isoformat()
                    detail['duration_seconds'] = max(
                        0, int((datetime.now() - started_at).total_seconds())
                    )
                    self.last_run_diagnostics[name] = detail

        finally:
            self.close_driver()

        return all_posts