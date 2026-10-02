"""Regression tests for the Google Maps scrape / resolve flow (no browser).

These cover the three failures reported from the deployed build:

1. a Google Maps navigation that exceeds Selenium's page-load timer used to
   abort the whole scrape even though Maps had already rendered usable DOM;
2. ``POST /api/places/resolve`` dropped the Google Maps link the user pasted and
   re-searched by name (or refused to run at all when only a link was given);
3. a Maps failure during discovery was swallowed, so "Google Maps could not be
   read" looked identical to "no such businesses".

Everything here uses a FakeDriver, so no Chrome, no network and no database are
required:

    python backend/test_scraper_resolve_flow.py     # exit 0 = all passed
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importing the scraper must not need Chrome; it is only started on demand.
from selenium.common.exceptions import TimeoutException  # noqa: E402

from scraper import GoogleMapsScraper  # noqa: E402

FAILURES = []

# A real-looking Google Maps listing URL: the ``!1s0x..:0x..`` hex pair is what
# ``place_identity`` turns into a *strong* canonical identity.
PLACE_URL = (
    'https://www.google.com/maps/place/Brev%C3%A9+Bakery/@19.0497086,73.0737312,17z/'
    'data=!3m1!4b1!4m6!3m5!1s0x3be7c34ad8732a15:0x3ca56e67bc533464!8m2!3d19.0497086'
    '!4d73.0737312!16s%2Fg%2F11c5w7v8x9'
)
SEARCH_URL = 'https://www.google.com/maps/search/Starbucks+Kharghar'


def check(label, condition, detail=''):
    if condition:
        print(f'  [ok] {label}')
    else:
        print(f'  [FAIL] {label} {detail}')
        FAILURES.append(label)


class NoSuchElement(Exception):
    pass


class FakeElement:
    def __init__(self, text='', attributes=None, displayed=True):
        self.text = text
        self._attributes = attributes or {}
        self._displayed = displayed

    def get_attribute(self, name):
        return self._attributes.get(name)

    def is_displayed(self):
        return self._displayed


class FakeDriver:
    """Minimal WebDriver stand-in that records navigation and page content."""

    def __init__(self, url='', title='Google Maps', body_text='', headings=(),
                 timeout_on_get=False):
        self.current_url = url
        self.title = title
        self.body_text = body_text
        self.headings = list(headings)
        self.timeout_on_get = timeout_on_get
        self.navigated = []
        self.scripts = []
        self.stopped = 0
        self.quit_called = False
        self.service = None

    def get(self, url):
        self.navigated.append(url)
        if self.timeout_on_get:
            raise TimeoutException('timed out waiting for page load')
        self.current_url = url

    def execute_script(self, script, *args):
        self.scripts.append(script)
        if 'window.stop' in script:
            self.stopped += 1
        return None

    def find_element(self, by, value):
        if value == 'body':
            return FakeElement(self.body_text)
        raise NoSuchElement()

    def find_elements(self, by, value):
        if value == 'h1':
            return [FakeElement(text) for text in self.headings]
        return []

    def implicitly_wait(self, seconds):
        pass

    def set_page_load_timeout(self, seconds):
        pass

    def set_script_timeout(self, seconds):
        pass

    def quit(self):
        self.quit_called = True


class FakeScraper(GoogleMapsScraper):
    """Scraper whose browser is the FakeDriver instead of a real Chromium."""

    def __init__(self, driver):
        super().__init__(headless=True)
        self._fake_driver = driver
        # A helper such as `_navigate_maps` may be exercised on its own, so the
        # fake session is installed immediately as well as via setup_driver().
        self.driver = driver

    def setup_driver(self):
        self.driver = self._fake_driver


def test_validated_maps_url():
    print('\n== _validated_maps_url (arbitrary-navigation guard) ==')
    validate = GoogleMapsScraper._validated_maps_url

    check('accepts a full /maps/place/ URL', validate(PLACE_URL) == PLACE_URL)
    check('accepts a /maps/search/ URL', validate(SEARCH_URL) == SEARCH_URL)
    check('accepts a share link (maps.app.goo.gl)',
          validate('https://maps.app.goo.gl/abc123') == 'https://maps.app.goo.gl/abc123')
    check('accepts a bare host and normalises to https',
          validate('www.google.co.in/maps/place/Foo') == 'https://www.google.co.in/maps/place/Foo')
    check('accepts an http Maps link and upgrades it to https',
          validate('http://google.com/maps/search/x') == 'https://google.com/maps/search/x')

    for bad in ('', 'https://example.com/maps/place/Foo', 'https://evil.com',
                'https://google.com/', 'file:///etc/passwd', 'javascript:alert(1)',
                'https://google.com/url?q=https://evil.com'):
        try:
            validate(bad)
        except ValueError:
            check(f'rejects {bad!r}', True)
        else:
            check(f'rejects {bad!r}', False, '<- it was accepted')


def test_navigate_recovers_from_page_load_timeout():
    print('\n== _navigate_maps: a page-load timeout keeps the rendered DOM ==')
    driver = FakeDriver(timeout_on_get=True)
    scraper = FakeScraper(driver)

    timed_out = scraper._navigate_maps(PLACE_URL)

    check('navigation timeout is reported (not raised)', timed_out is True)
    check('the page load was stopped so the DOM can be read', driver.stopped == 1,
          f'window.stop() calls: {driver.stopped}')
    check('the URL was still requested', driver.navigated == [PLACE_URL])


def test_wait_for_content_returns_as_soon_as_listing_renders():
    print('\n== _wait_for_maps_content: waits for a listing, not just a title ==')
    driver = FakeDriver(url=PLACE_URL, body_text='Brevé Bakery\n4.9\nCafe',
                        headings=('Brevé Bakery',))
    scraper = FakeScraper(driver)

    started = time.monotonic()
    state = scraper._wait_for_maps_content(timeout=10)
    elapsed = time.monotonic() - started

    check('returns without burning the whole timeout', elapsed < 2,
          f'took {elapsed:.2f}s')
    check('reports the single business profile', state['state'] == 'PLACE_PROFILE',
          str(state.get('state')))

    # A blank page that never renders a listing must not loop forever.
    blank = FakeScraper(FakeDriver(url=SEARCH_URL, title='', body_text=''))
    started = time.monotonic()
    blank._wait_for_maps_content(timeout=1)
    check('gives up after the timeout instead of hanging',
          time.monotonic() - started < 4)


def test_resolve_uses_the_supplied_maps_url():
    print('\n== resolve_place_identity(gmap_url=...): link-only resolution ==')
    driver = FakeDriver(url=PLACE_URL, body_text='Brevé Bakery\n4.9\nCafé, Mumbai',
                        headings=('Brevé Bakery',))
    scraper = FakeScraper(driver)

    # No name at all - the pasted link is the whole request.
    result = scraper.resolve_place_identity('', gmap_url=PLACE_URL)

    check('resolves without a typed name', result['found'] is True, str(result)[:200])
    check('opens the supplied listing, not a fresh name search',
          driver.navigated == [PLACE_URL], str(driver.navigated))
    check('returns the canonical place identity',
          bool(result.get('place_key')) and result.get('identity_source') in
          ('hex_id', 'place_id', 'cid'), str(result.get('identity_source')))
    check('returns the listing URL', result.get('google_maps_url') == PLACE_URL)
    check('browser is closed after the lookup', driver.quit_called)

    # An invalid target must never be browsed.
    bad_driver = FakeDriver()
    bad = FakeScraper(bad_driver)
    try:
        bad.resolve_place_identity('Foo', gmap_url='https://example.com/maps/place/Foo')
    except ValueError:
        check('invalid non-Maps URL raises instead of navigating', True)
    else:
        check('invalid non-Maps URL raises instead of navigating', False)
    check('no browser was started for an invalid URL', bad_driver.navigated == [])


def test_search_timeout_is_not_reported_as_no_results():
    print('\n== search_google_maps_places: TIMEOUT != NO_RESULTS ==')

    class DeadlineScraper(FakeScraper):
        """Stands in for the bounded wait expiring on a Maps page that never
        rendered a listing (the real method returns exactly this at deadline)."""

        def _wait_for_maps_content(self, timeout=15):
            return self._detect_google_maps_page_state()

    driver = FakeDriver(timeout_on_get=True, url=SEARCH_URL, title='Google Maps',
                        body_text='Google Maps')
    scraper = DeadlineScraper(driver)

    outcome = scraper.search_google_maps_places('Starbucks', 'Kharghar')

    check('state is TIMEOUT, never NO_RESULTS', outcome['state'] == 'TIMEOUT',
          str(outcome.get('state')))
    check('no bogus empty result set is claimed', outcome['results'] == [])
    check('the message blames the load, not the business',
          'time' in (outcome.get('message') or '').lower(),
          str(outcome.get('message')))
    check('browser is closed after the search', driver.quit_called)


def test_resolve_reports_browser_failure_without_browser():
    print('\n== resolve_place_identity: BROWSER_ERROR is explicit ==')

    class NoBrowserScraper(GoogleMapsScraper):
        def setup_driver(self):
            raise RuntimeError('no usable browser/driver found')

    result = NoBrowserScraper(headless=True).resolve_place_identity('Starbucks')

    check('state is BROWSER_ERROR', result['state'] == 'BROWSER_ERROR',
          str(result.get('state')))
    check('a clear message is returned', bool(result.get('message')))
    check('nothing is reported as found', result['found'] is False)


def main():
    test_validated_maps_url()
    test_navigate_recovers_from_page_load_timeout()
    test_wait_for_content_returns_as_soon_as_listing_renders()
    test_resolve_uses_the_supplied_maps_url()
    test_search_timeout_is_not_reported_as_no_results()
    test_resolve_reports_browser_failure_without_browser()

    print('-' * 72)
    if FAILURES:
        print(f'{len(FAILURES)} check(s) FAILED')
        return 1
    print('ALL SCRAPE / RESOLVE FLOW CHECKS PASSED')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
