"""Offline scrape persistence and reporting regressions."""
import unittest
from unittest.mock import Mock, patch

from test_api_resolve import isolated_api
from test_database_mongo import fresh_db


class PostPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.api = isolated_api()
        self.db = fresh_db()
        self.project = self.db.create_project('test', field='fashion')
        self.competitor = self.db.add_competitor(
            self.project, 'Max Fashion - Nexus Seawoods',
            gmap_url='https://www.google.com/maps/search/?api=1&query=Max')
        self.scraper = Mock()
        self.scraper.last_place_profiles = {}
        self.scraper.last_run_diagnostics = {'Max Fashion - Nexus Seawoods': {'business_verified': True}}
        self.posts = [{'text_content': 'New season collection', 'post_source': 'owner'},
                      {'text_content': 'Weekend offers', 'post_source': 'owner'}]
        self.scraper.scrape_competitor_posts.return_value = self.posts
        self.scraper.scrape_multiple_competitors.return_value = {'Max Fashion - Nexus Seawoods': self.posts}
        self.client = self.api.app.test_client()
        self.patches = [patch.object(self.api, 'db', self.db),
                        patch.object(self.api, 'GoogleMapsScraper', return_value=self.scraper)]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_single_scrape_saves_posts_and_dashboard_counts(self):
        url = f'/api/competitors/{self.competitor}/scrape'
        body = self.client.post(url).get_json()
        self.assertEqual(body['results']['new_posts'], 2)
        self.assertEqual(len(self.client.get(f'/api/projects/{self.project}/posts').get_json()['posts']), 2)
        self.assertEqual(self.db.get_scraping_stats(self.project)['total_posts'], 2)
        self.assertEqual(self.client.post(url).get_json()['results']['duplicates_skipped'], 2)
        self.assertEqual(self.db.get_scraping_stats(self.project)['total_posts'], 2)
        self.scraper.close_driver.assert_called()

    def test_unverified_single_and_batch_cannot_report_success_or_captured_posts(self):
        self.scraper.last_run_diagnostics = {'Max Fashion - Nexus Seawoods': {
            'business_verified': False, 'scrape_status': 'BUSINESS_MISMATCH'}}
        for url in (f'/api/competitors/{self.competitor}/scrape',
                    f'/api/projects/{self.project}/scrape'):
            body = self.client.post(url).get_json()
            self.assertEqual(body['results']['posts_found'], 0)
            self.assertEqual(body['results']['new_posts'], 0)
            self.assertEqual(body['results']['failures'], 1)
        self.assertEqual(self.db.get_scraping_stats(self.project)['total_posts'], 0)


if __name__ == '__main__':
    unittest.main()