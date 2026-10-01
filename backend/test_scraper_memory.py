"""Browser lifecycle regression tests; no Chrome or network required."""
import unittest
from unittest.mock import Mock, patch

from scraper import GoogleMapsScraper


class ScraperMemoryTests(unittest.TestCase):
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