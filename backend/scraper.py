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

    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Container/ARM support: when running inside Docker (Oracle VM) the image
        # ships Debian's chromium + version-matched chromium-driver, so their
        # paths are injected through env vars instead of Selenium Manager
        # (which would try to download an x86-only driver).
        # Locally the env vars are unset and behaviour is unchanged.
        chrome_binary = os.environ.get("CHROME_BINARY") or os.getenv("CHROME_PATH")
        if chrome_binary:
            chrome_options.binary_location = chrome_binary
        driver_path = os.environ.get("CHROMEDRIVER_PATH")

        try:
            if driver_path:
                service = Service(executable_path=driver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.set_page_load_timeout(30)
            logger.info("WebDriver setup successful")
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {e}")
            raise

    def close_driver(self):
        """Close the WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None
            logger.info("WebDriver closed")

    def search_google_maps_places(self, query: str, location: str = None, max_results: int = 6) -> List[Dict]:
        """
        Scrape Google Maps search results to find real business places, addresses, ratings, and URLs.
        """
        import urllib.parse
        import re

        full_query = f"{query} {location}".strip() if location and location.lower() not in query.lower() else query
        url = f"https://www.google.com/maps/search/{urllib.parse.quote(full_query)}"
        logger.info(f"Searching Google Maps for: {full_query}")

        places = []
        try:
            self.setup_driver()
            self.driver.get(url)
            time.sleep(4)

            links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/maps/place/']")
            seen_names = set()

            for link in links:
                name = link.get_attribute("aria-label") or link.text.strip()
                href = link.get_attribute("href")
                if not name or name in seen_names or not href:
                    continue
                seen_names.add(name)

                # Initialize with defaults
                rating = None
                review_count = None
                category = None
                address = None
                opening_hours = None
                status = None

                try:
                    card = link.find_element(By.XPATH, "./ancestor::div[contains(@class, 'Nv2PK')]")
                    
                    # Extract rating
                    try:
                        rating_elements = card.find_elements(By.CSS_SELECTOR, "[role='img'][aria-label*='star']")
                        for el in rating_elements:
                            aria = el.get_attribute("aria-label")
                            if aria:
                                m_rate = re.search(r'([345]\.[0-9])', aria)
                                if m_rate:
                                    rating = float(m_rate.group(1))
                                    break
                    except Exception:
                        pass

                    # Extract review count
                    try:
                        review_elements = card.find_elements(By.XPATH, ".//*[contains(text(), 'review') or contains(text(), 'Review')]")
                        for el in review_elements:
                            text = el.text.strip()
                            m_rev = re.search(r'([\d,]+)\s*(review|Review)', text)
                            if m_rev:
                                review_count = int(m_rev.group(1).replace(',', ''))
                                break
                    except Exception:
                        pass

                    # Extract all text lines from card
                    lines = [l.strip() for l in card.text.split('\n') if l.strip()]
                    
                    # Parse structured data from lines
                    for i, line in enumerate(lines):
                        line_lower = line.lower()
                        
                        # Opening hours / status
                        if 'closes' in line_lower or 'opens' in line_lower or 'open 24' in line_lower:
                            opening_hours = line
                            if 'open' in line_lower:
                                status = 'Open'
                            elif 'closed' in line_lower:
                                status = 'Closed'
                            continue
                        
                        # Address indicators
                        address_indicators = ['road', 'street', 'avenue', 'lane', 'drive', 'boulevard', 'highway',
                                             'sector', 'block', 'phase', 'floor', 'building', 'tower', 'complex',
                                             'mall', 'plaza', 'market', 'colony', 'nagar', 'vihar', 'puram', 'ganj',
                                             'chowk', 'circle', 'square', 'cross', 'main', 'link', 'service',
                                             'plot', 'shop no', 'shop no.', 'unit', 'suite', 'level', 'basement']
                        
                        has_address_indicator = any(ind in line_lower for ind in address_indicators)
                        
                        # Category keywords that appear at START of line
                        category_start_keywords = ['restaurant', 'cafe', 'bakery', 'sweet', 'salon', 'spa', 'clinic', 'hospital', 
                                                    'parlour', 'beauty', 'hair', 'nail', 'massage', 'wellness', 'medical',
                                                    'dental', 'optical', 'veterinary', 'pet', 'automotive', 'car', 'bike',
                                                    'repair', 'laundry', 'dry clean', 'tailor', 'photography',
                                                    'studio', 'gallery', 'art', 'music', 'dance', 'yoga', 'martial arts',
                                                    'gym', 'fitness', 'bank', 'atm', 'pharmacy', 'grocery', 'supermarket',
                                                    'shop', 'store', 'boutique', 'hotel']
                        
                        starts_with_category = any(line_lower.startswith(kw) for kw in category_start_keywords)
                        
                        # COMBINED CASE: Line starts with category keyword AND has address indicators
                        # Split into category (first part) and address (rest)
                        if category is None and address is None and line != name and i > 0 and starts_with_category and has_address_indicator:
                            # Find where the address part starts
                            first_addr_pos = len(line)
                            for ind in address_indicators:
                                pos = line_lower.find(ind)
                                if pos != -1 and pos < first_addr_pos:
                                    first_addr_pos = pos
                            
                            if first_addr_pos < len(line) and first_addr_pos > 2:
                                category = line[:first_addr_pos].strip().rstrip(',').strip()
                                address = line[first_addr_pos:].strip().lstrip(',').strip()
                            else:
                                address = line
                            continue
                        
                        # Address - lines with location indicators (CHECK FIRST)
                        if address is None and has_address_indicator and len(line) > 5:
                            address = line
                            continue
                        
                        # Category - line STARTS with business category keyword
                        category_start_keywords = ['restaurant', 'cafe', 'bakery', 'sweet', 'salon', 'spa', 'clinic', 'hospital', 
                                                    'parlour', 'beauty', 'hair', 'nail', 'massage', 'wellness', 'medical',
                                                    'dental', 'optical', 'veterinary', 'pet', 'automotive', 'car', 'bike',
                                                    'repair', 'laundry', 'dry clean', 'tailor', 'photography',
                                                    'studio', 'gallery', 'art', 'music', 'dance', 'yoga', 'martial arts',
                                                    'gym', 'fitness', 'bank', 'atm', 'pharmacy', 'grocery', 'supermarket',
                                                    'shop', 'store', 'boutique', 'hotel']
                        
                        starts_with_category = any(line_lower.startswith(kw) for kw in category_start_keywords)
                        
                        # If line starts with category keyword AND doesn't have strong address indicators, it's a category
                        if category is None and line != name and i > 0 and starts_with_category and not has_address_indicator and len(line) < 120:
                            category = line
                            continue
                        
                        # Category - line contains business type but doesn't start with it
                        # and doesn't look like an address
                        is_address_like = any(ind in line_lower for ind in ['road', 'street', 'avenue', 'lane', 'drive', 'boulevard', 'highway',
                                             'sector', 'block', 'phase', 'plot', 'shop no', 'shop no.', 'unit', 'suite',
                                             'floor', 'building', 'tower', 'complex', 'mall', 'plaza', 'market',
                                             'colony', 'nagar', 'vihar', 'puram', 'ganj', 'chowk', 'circle', 'square',
                                             'cross', 'main', 'link', 'service', 'basement'])
                        
                        if category is None and line != name and i > 0 and not is_address_like:
                            category_keywords = ['restaurant', 'cafe', 'bakery', 'sweet', 'salon', 'spa', 'clinic', 'hospital', 
                                                'shop', 'store', 'boutique', 'hotel', 'gym', 'fitness', 'bank', 'atm',
                                                'pharmacy', 'grocery', 'supermarket', 'mall', 'office', 'school',
                                                'university', 'college', 'temple', 'mosque', 'church', 'park',
                                                'museum', 'theater', 'cinema', 'library', 'post office', 'police',
                                                'fire station', 'gas station', 'parking', 'taxi', 'bus', 'metro',
                                                'train', 'airport', 'port', 'harbor', 'marina', 'beach', 'zoo',
                                                'aquarium', 'garden', 'stadium', 'arena', 'convention', 'exhibition',
                                                'parlour', 'beauty', 'hair', 'nail', 'massage', 'wellness', 'medical',
                                                'dental', 'optical', 'veterinary', 'pet', 'automotive', 'car', 'bike',
                                                'repair', 'service', 'laundry', 'dry clean', 'tailor', 'photography',
                                                'studio', 'gallery', 'art', 'music', 'dance', 'yoga', 'martial arts']
                            if any(kw in line_lower for kw in category_keywords) and len(line) < 80:
                                category = line
                                continue
                        
                        # Fallback: if line has '·' separator
                        if '·' in line and category is None and address is None:
                            parts = [p.strip() for p in line.split('·')]
                            if len(parts) >= 2:
                                # First part could be category, second could be address
                                if len(parts[0]) < 80 and any(kw in parts[0].lower() for kw in ['restaurant', 'cafe', 'bakery', 'sweet', 'salon', 'shop', 'store', 'clinic', 'hospital', 'hotel', 'gym', 'bank', 'pharmacy', 'grocery', 'school', 'office', 'parlour', 'beauty', 'hair', 'spa', 'wellness']):
                                    category = parts[0]
                                address = parts[1]
                            elif len(parts) == 1:
                                if address is None:
                                    address = parts[0]
                            continue

                    # If still no address, try to get from address button
                    if address is None:
                        try:
                            addr_elements = card.find_elements(By.CSS_SELECTOR, "button[data-item-id='address'], [data-item-id='address']")
                            for el in addr_elements:
                                raw = el.get_attribute('aria-label') or el.text or ''
                                raw = raw.replace('Address:', '').strip()
                                if raw and len(raw) > 5:
                                    address = raw
                                    break
                        except Exception:
                            pass

                    # If still no category, try to get from category button
                    if category is None:
                        try:
                            cat_elements = card.find_elements(By.CSS_SELECTOR, "button[data-item-id='category'], [data-item-id='category']")
                            for el in cat_elements:
                                raw = el.get_attribute('aria-label') or el.text or ''
                                raw = raw.strip()
                                if raw and len(raw) < 80:
                                    category = raw
                                    break
                        except Exception:
                            pass

                except Exception as e:
                    logger.debug(f"Error parsing card for {name}: {e}")

                places.append({
                    "name": name,
                    "google_maps_url": href,
                    "category": category,
                    "address": address,
                    "opening_hours": opening_hours,
                    "status": status,
                    "rating": rating,
                    "review_count": review_count,
                    "distance": "0.8 km",
                    "strengths": ["Verified Google Profile", "Popular in Area"],
                    # Canonical identity: the same listing must resolve to one
                    # business no matter which URL shape Google returned.
                    **self._identity_fields(href, name, address),
                })

                if len(places) >= max_results:
                    break

        except Exception as e:
            logger.error(f"Error scraping Google Maps places: {e}")
        finally:
            self.close_driver()

        return places

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
        result = {
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
            self.setup_driver()
            self.driver.get(search_url)
            time.sleep(4)

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

            result["message"] = (
                "No Google Maps listing matched this name"
                if not no_results else "Google Maps found no place for this name"
            )
            return result
        except Exception as e:
            logger.warning(f"Place resolution failed for {clean_query!r}: {e}")
            result["message"] = str(e)
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