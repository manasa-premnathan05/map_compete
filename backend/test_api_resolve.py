"""Isolated Flask resolve regressions: no MongoDB, AI calls, or browser.

Run: python backend/test_api_resolve.py
The API is imported with stub service modules so local .env credentials cannot
cause database initialization. Requests use Flask.test_client(), as in the API
integration suite, and unittest.mock supplies all external operations.
"""

import importlib.util
import logging
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from place_identity import extract_place_identity  # noqa: E402


def isolated_api():
    database = types.ModuleType('database')
    database.DatabaseManager = Mock(return_value=Mock())
    database.DatabaseUnavailableError = type('DatabaseUnavailableError', (RuntimeError,), {})
    ai_service = types.ModuleType('ai_service')
    ai_service.AIServiceManager = Mock(return_value=Mock())
    spec = importlib.util.spec_from_file_location('api_resolve_test_app', HERE / 'api.py')
    module = importlib.util.module_from_spec(spec)
    with patch.dict(sys.modules, {'database': database, 'ai_service': ai_service}), \
            patch('dotenv.load_dotenv'), \
            patch('logging.FileHandler', return_value=logging.NullHandler()):
        spec.loader.exec_module(module)
    module.app.config['TESTING'] = True
    return module


api = isolated_api()
URL = 'https://maps.app.goo.gl/example'
PROFILE_URL = 'https://www.google.com/maps/place/Example/?cid=123456'


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.db = Mock()
        self.db.resolve_place_identity.side_effect = extract_place_identity
        self.scraper_class = Mock()
        self.scraper_class._validated_maps_url.side_effect = lambda url: url.strip()
        self.scraper = self.scraper_class.return_value
        self.scraper.resolve_place_identity.return_value = {
            'found': True, 'state': 'PLACE_PROFILE', 'name': 'Example Cafe',
            'address': 'Mumbai', 'google_maps_url': PROFILE_URL,
        }
        self.db_patch = patch.object(api, 'db', self.db)
        self.scraper_patch = patch.object(api, 'GoogleMapsScraper', self.scraper_class)
        self.db_patch.start()
        self.scraper_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.addCleanup(self.scraper_patch.stop)
        self.client = api.app.test_client()

    def resolve(self, **data):
        return self.client.post('/api/places/resolve', json=data)

    def test_supplied_url_reaches_live_lookup_for_both_aliases(self):
        for alias in ('google_maps_url', 'gmap_url'):
            with self.subTest(alias=alias):
                self.scraper_class.reset_mock()
                response = self.resolve(name='Example Cafe', location=' Mumbai ',
                                        live=True, **{alias: ' ' + URL + ' '})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.get_json()['live'])
                self.scraper_class._validated_maps_url.assert_called_once_with(' ' + URL + ' ')
                self.scraper.resolve_place_identity.assert_called_once_with(
                    'Example Cafe', location='Mumbai', gmap_url=URL)
                self.assertEqual(self.db.resolve_place_identity.call_args_list[-2].kwargs['gmap_url'], URL)

    def test_url_only_live_lookup(self):
        response = self.resolve(gmap_url=URL, live=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()['name'], 'Example Cafe')
        self.scraper.resolve_place_identity.assert_called_once_with(
            '', location=None, gmap_url=URL)

    def test_url_only_nonlive_does_not_start_browser(self):
        response = self.resolve(google_maps_url=URL)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()['live'])
        self.scraper_class.assert_not_called()

    def test_invalid_url_rejected_before_identity_or_browser(self):
        for invalid in ('https://evil.example/maps', 'javascript:alert(1)', 123):
            with self.subTest(url=invalid):
                self.scraper_class._validated_maps_url.side_effect = ValueError('Invalid Google Maps URL')
                response = self.resolve(name='Example Cafe', gmap_url=invalid, live=True)
                self.assertEqual(response.status_code, 400)
                self.assertIn('Invalid Google Maps URL', response.get_json()['error'])
                self.db.resolve_place_identity.assert_not_called()
                self.scraper_class.assert_not_called()

    def test_invalid_url_rejected_even_with_strong_identity(self):
        self.scraper_class._validated_maps_url.side_effect = ValueError('Invalid Google Maps URL')
        response = self.resolve(gmap_url='https://evil.example/?cid=123', cid='123', live=True)
        self.assertEqual(response.status_code, 400)
        self.db.resolve_place_identity.assert_not_called()
        self.scraper_class.assert_not_called()

    def test_strong_url_only_identity_keeps_fast_path(self):
        response = self.resolve(gmap_url=PROFILE_URL, live=True)
        self.assertEqual(response.status_code, 200)
        body = response.get_json()
        self.assertTrue(body['found'])
        self.assertFalse(body['live'])
        self.assertTrue(body['identity']['is_strong'])
        self.scraper_class.assert_not_called()

    def test_named_strong_identity_keeps_fast_path(self):
        response = self.resolve(name='Example Cafe', cid='123456', live=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()['live'])
        self.scraper_class.assert_not_called()
        self.scraper_class._validated_maps_url.assert_not_called()

    def test_name_only_lookup_is_unchanged(self):
        response = self.resolve(query=' Example Cafe ', live=True)
        self.assertEqual(response.status_code, 200)
        self.scraper.resolve_place_identity.assert_called_once_with(
            'Example Cafe', location=None, gmap_url=None)
        self.scraper_class._validated_maps_url.assert_not_called()

    def test_missing_name_and_url_returns_400(self):
        response = self.resolve(name='  ', live=True)
        self.assertEqual(response.status_code, 400)
        self.db.resolve_place_identity.assert_not_called()
        self.scraper_class.assert_not_called()

    def test_live_failures_keep_structured_http_states(self):
        for state, status in (('NO_RESULTS', 404), ('CAPTCHA', 429),
                              ('BROWSER_ERROR', 503), ('TIMEOUT', 504)):
            with self.subTest(state=state):
                self.scraper.resolve_place_identity.return_value = {
                    'found': False, 'state': state, 'message': 'Lookup unavailable',
                }
                response = self.resolve(gmap_url=URL, live=True)
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.get_json()['state'], state)
                self.assertFalse(response.get_json()['found'])

    def test_browser_lock_still_rejects_concurrent_lookup(self):
        api._browser_operation_lock.acquire()
        try:
            response = self.resolve(gmap_url=URL, live=True)
            self.assertEqual(response.status_code, 429)
            self.assertEqual(response.get_json()['error_type'], 'SCRAPER_BUSY')
            self.scraper_class.assert_not_called()
        finally:
            api._browser_operation_lock.release()

    def test_validation_failure_releases_browser_lock(self):
        self.scraper_class._validated_maps_url.side_effect = ValueError('Invalid Google Maps URL')
        self.assertEqual(self.resolve(gmap_url=URL, live=True).status_code, 400)
        acquired = api._browser_operation_lock.acquire(blocking=False)
        self.assertTrue(acquired)
        if acquired:
            api._browser_operation_lock.release()


class DiscoveryReportingInspectionTests(unittest.TestCase):
    """Discovery must report each engine's failure instead of hiding it."""

    def setUp(self):
        self.db = Mock()
        self.db.get_project.return_value = {'id': 1, 'name': 'Example Cafe'}
        self.db.get_competitors.return_value = []
        self.db.get_project_place.return_value = None
        # A weak, name-only identity: the live row is a candidate, not a match.
        self.db.resolve_place_identity.return_value = {
            'place_key': None, 'is_strong': False, 'identity_source': 'name',
            'google_place_id': None, 'hex_id': None, 'cid': None,
        }
        self.db.get_place_by_key.return_value = None
        self.scraper_class = Mock()
        self.ai_service = Mock()
        self.ai_service.discover_local_competitors.return_value = {'competitors': []}
        for name, value in (('db', self.db), ('GoogleMapsScraper', self.scraper_class),
                            ('ai_service', self.ai_service)):
            patcher = patch.object(api, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.client = api.app.test_client()

    def test_live_browser_failure_is_reported_in_scrape_state(self):
        self.scraper_class.return_value.search_google_maps_places.return_value = {
            'state': 'BROWSER_ERROR', 'results': [],
            'message': 'Browser could not start', 'diagnostics': {},
        }
        response = self.client.post('/api/projects/1/discover-competitors', json={})
        body = response.get_json()
        # Discovery still degrades gracefully ...
        self.assertEqual(response.status_code, 200)
        self.assertEqual(body['competitors'], [])
        # ... but the Maps failure is named, not silently swallowed.
        self.assertEqual(body['scrape_state'], 'BROWSER_ERROR')
        self.assertEqual(body['scrape_message'], 'Browser could not start')
        self.assertEqual(body['live_places_found'], 0)
        self.assertEqual(api._LAST_PLACE_DIAGNOSTICS['discover']['state'], 'BROWSER_ERROR')

    def test_successful_live_scrape_reports_no_scrape_message(self):
        self.scraper_class.return_value.search_google_maps_places.return_value = {
            'state': 'RESULTS', 'results': [{'name': 'Live Cafe'}], 'diagnostics': {},
        }
        body = self.client.post('/api/projects/1/discover-competitors',
                                json={}).get_json()
        self.assertEqual(body['scrape_state'], 'RESULTS')
        self.assertIsNone(body['scrape_message'])
        self.assertEqual(body['live_places_found'], 1)
        self.assertEqual(body['competitors'][0]['name'], 'Live Cafe')

    def test_ai_failure_keeps_live_maps_results_and_reports_it(self):
        self.scraper_class.return_value.search_google_maps_places.return_value = {
            'state': 'RESULTS', 'results': [{'name': 'Live Cafe'}], 'diagnostics': {},
        }
        self.ai_service.discover_local_competitors.side_effect = RuntimeError('AI unavailable')
        response = self.client.post('/api/projects/1/discover-competitors', json={})
        body = response.get_json()
        # A provider outage is no longer a 500 that throws away scraped rows.
        self.assertEqual(response.status_code, 200)
        self.assertEqual([c['name'] for c in body['competitors']], ['Live Cafe'])
        self.assertEqual(body['ai_message'], 'AI unavailable')


if __name__ == '__main__':
    unittest.main(verbosity=2)