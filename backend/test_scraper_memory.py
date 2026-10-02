"""Browser lifecycle regression tests; no Chrome or network required."""
import unittest
from unittest.mock import Mock, patch

from scraper import GoogleMapsScraper


class ScraperMemoryTests(unittest.TestCase):
    def test_max_branch_alias_is_verified_without_accepting_other_branches(self):
        scraper = GoogleMapsScraper()
        self.assertTrue(scraper._listing_names_match(
            'Max - Nexus Seawoods Mall', 'Max Fashion - Nexus Seawoods'))
        self.assertFalse(scraper._listing_names_match('Zudio', 'Zudio - Nexus Seawoods'))
        for found in ('Max - Nexus Kharghar Mall', 'Other Fashion - Nexus Seawoods',
                      'Max - Nexus Mall', 'The Brew Zone'):
            self.assertFalse(scraper._listing_names_match(found, 'Max Fashion - Nexus Seawoods'))
        self.assertFalse(scraper._listing_names_match('The Brew Zone', 'The Brew'))

    def test_listing_on_search_url_keeps_verified_posts(self):
        scraper = GoogleMapsScraper()
        scraper.driver = Mock()
        scraper.driver.current_url = 'https://www.google.com/maps/search/?api=1&query=Max'
        heading = Mock()
        heading.text = 'Max - Nexus Seawoods Mall'
        scraper.driver.find_elements.side_effect = lambda by, selector: [] if selector.startswith('a[') else [heading]
        post = {'text_content': 'Our new collection is here', 'post_source': 'owner'}
        with patch.object(scraper, '_navigate_maps'), \
                patch.object(scraper, '_wait_for_maps_content', return_value={'state': 'PLACE_PROFILE'}), \
                patch.object(scraper, 'handle_captcha', return_value=False), \
                patch.object(scraper, '_read_current_place_profile', return_value={
                    'name': heading.text, 'review_count': 10}), \
                patch.object(scraper, '_find_posts_section', return_value=object()), \
                patch.object(scraper, '_extract_posts_from_section', return_value=[post]):
            posts = scraper.scrape_competitor_posts(
                'Max Fashion - Nexus Seawoods', scraper.driver.current_url, include_public=False)
        self.assertEqual(posts, [post])
        self.assertTrue(scraper.last_run_diagnostics['Max Fashion - Nexus Seawoods']['business_verified'])
        scraper.close_driver()

    def test_wrong_listing_is_not_extracted(self):
        scraper = GoogleMapsScraper()
        scraper.driver = Mock()
        scraper.driver.current_url = 'https://www.google.com/maps/place/Other'
        heading = Mock()
        heading.text = 'Other Fashion'
        scraper.driver.find_elements.return_value = [heading]
        with patch.object(scraper, '_navigate_maps'), \
                patch.object(scraper, '_wait_for_maps_content', return_value={'state': 'PLACE_PROFILE'}), \
                patch.object(scraper, 'handle_captcha', return_value=False), \
                patch.object(scraper, '_read_current_place_profile', return_value={'review_count': 1}), \
                patch.object(scraper, '_find_posts_section') as extract:
            self.assertEqual(scraper.scrape_competitor_posts(
                'Max Fashion - Nexus Seawoods', scraper.driver.current_url), [])
            extract.assert_not_called()
        self.assertEqual(scraper.last_run_diagnostics['Max Fashion - Nexus Seawoods']['scrape_status'], 'BUSINESS_MISMATCH')
        scraper.close_driver()

    def test_unrendered_listing_retries_once_without_new_browser(self):
        scraper = GoogleMapsScraper()
        scraper.driver = Mock()
        with patch.object(scraper, 'setup_driver') as setup, \
                patch.object(scraper, '_navigate_maps', return_value=True) as navigate, \
                patch.object(scraper, '_wait_for_maps_content', return_value={
                    'state': 'UNKNOWN', 'message': 'not rendered'}) as wait:
            with self.assertRaisesRegex(Exception, 'TIMEOUT'):
                scraper.scrape_competitor_posts('Example', 'https://www.google.com/maps/place/Example')
        self.assertEqual(navigate.call_count, 2)
        self.assertEqual(wait.call_count, 2)
        setup.assert_not_called()
        self.assertEqual(scraper.last_run_diagnostics['Example']['scrape_status'], 'TIMEOUT')
        scraper.close_driver()

    def test_service_stopped_even_when_quit_fails(self):
        scraper = GoogleMapsScraper()
        driver = Mock()
        driver.quit.side_effect = RuntimeError('browser disconnected')
        scraper.driver = driver
        scraper.close_driver()
        driver.service.stop.assert_called_once()
        self.assertIsNone(scraper.driver)
        scraper.close_driver()  # cleanup is idempotent

    def test_browser_closed_between_competitors_and_after_failure(self):
        scraper = GoogleMapsScraper()
        visited = []

        def scrape(name, url, **kwargs):
            self.assertIsNone(scraper.driver)
            scraper.driver = Mock()
            visited.append(scraper.driver)
            if name == 'second':
                raise RuntimeError('page crashed')
            return []

        with patch.object(scraper, 'scrape_competitor_posts', side_effect=scrape), patch('scraper.time.sleep'):
            result = scraper.scrape_multiple_competitors([
                {'name': 'first', 'gmap_url': 'https://maps.google.com/first'},
                {'name': 'second', 'gmap_url': 'https://maps.google.com/second'},
            ])
        self.assertEqual(result, {'first': [], 'second': []})
        for driver in visited:
            driver.quit.assert_called_once()
            driver.service.stop.assert_called_once()
        self.assertIsNone(scraper.driver)
        self.assertEqual(scraper.last_run_diagnostics['second']['status'], 'FAILED')


if __name__ == '__main__':
    unittest.main()