"""API caching-header regressions (no MongoDB, no browser).

A stale API payload - an old project list showing only one company, an old KPI
figure - is indistinguishable from a broken app, so every /api/ response must
forbid browser and proxy caching.

Run: python backend/test_api_cache_headers.py
"""

import unittest
from unittest.mock import Mock, patch

from test_api_resolve import isolated_api


class ApiCacheHeaderTests(unittest.TestCase):
    def setUp(self):
        self.api = isolated_api()
        self.db = Mock()
        # The header is set for every /api/ response, whatever the route answers.
        self.db.health.return_value = {'ok': True, 'database': 'connected'}
        self.db.get_projects.return_value = []
        self.db_patch = patch.object(self.api, 'db', self.db)
        self.db_patch.start()
        self.addCleanup(self.db_patch.stop)
        self.client = self.api.app.test_client()

    def cache_control(self, path):
        response = self.client.get(path)
        return response, response.headers.get('Cache-Control', ''), response.headers.get('Pragma', '')

    def test_data_responses_are_never_cached(self):
        response, cache_control, pragma = self.cache_control('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertIn('no-store', cache_control)
        self.assertEqual(pragma, 'no-cache')

    def test_project_list_is_never_cached(self):
        _, cache_control, _ = self.cache_control('/api/projects')
        self.assertIn('no-store', cache_control)

    def test_error_responses_keep_the_header(self):
        # A stale error page replayed from a cache is just as misleading, so the
        # header is attached to every /api/ response, not only the 200s.
        response, cache_control, _ = self.cache_control('/api/no-such-endpoint')
        self.assertEqual(response.status_code, 404)
        self.assertIn('no-store', cache_control)

    def test_ui_assets_are_untouched(self):
        # Only API payloads are pinned; the static shell keeps its own headers.
        _, cache_control, _ = self.cache_control('/')
        self.assertNotIn('no-store', cache_control)


if __name__ == '__main__':
    unittest.main()
