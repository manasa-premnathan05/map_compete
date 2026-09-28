import time
import re
import json
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

def get_competitors_for_project(project_id=49):
    conn = sqlite3.connect('competitor_intelligence.db')
    c = conn.cursor()
    c.execute('SELECT id, name, gmap_url, place_id FROM competitors WHERE project_id = ?', (project_id,))
    comps = c.fetchall()
    conn.close()
    return comps

def scrape_profiles(project_id=49):
    comps = get_competitors_for_project(project_id)
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(options=chrome_options)
    results = {}
    reviews_data = []

    try:
        for cid, name, url, place_id in comps:
            if not url:
                continue
            print(f'Fetching {name}...')
            driver.get(url)
            time.sleep(4)

            # Rating
            rating = None
            rating_elements = driver.find_elements(By.XPATH, "//*[@class='F7nice ']//span[@aria-hidden='true']")
            if rating_elements:
                try:
                    rating = float(rating_elements[0].text.strip())
                except Exception:
                    pass
            if rating is None:
                # alternative rating element
                alt_ratings = driver.find_elements(By.XPATH, "//span[contains(@aria-label, 'stars') or contains(@aria-label, 'star')]")
                for r in alt_ratings:
                    m = re.search(r'([\d\.]+)\s*star', r.get_attribute('aria-label') or '', re.I)
                    if m:
                        rating = float(m.group(1))
                        break

            # Review count
            rev_count = None
            rev_count_elements = driver.find_elements(By.XPATH, "//*[@class='F7nice ']//span[contains(@aria-label, 'review') or contains(@aria-label, 'Review')]")
            if rev_count_elements:
                aria = rev_count_elements[0].get_attribute('aria-label') or ''
                m = re.search(r'([\d,]+)', aria)
                if m:
                    rev_count = int(m.group(1).replace(',', ''))
            if rev_count is None:
                alt_revs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'reviews') or contains(@aria-label, 'Reviews')]")
                for r in alt_revs:
                    m = re.search(r'([\d,]+)\s*review', r.get_attribute('aria-label') or '', re.I)
                    if m:
                        rev_count = int(m.group(1).replace(',', ''))
                        break

            # Category
            cat_elements = driver.find_elements(By.XPATH, "//button[contains(@jsaction, 'pane.rating.category')]")
            category = cat_elements[0].text.strip() if cat_elements else None

            # Address
            addr_elements = driver.find_elements(By.XPATH, "//button[@data-item-id='address']//div[contains(@class, 'fontBodyMedium')]")
            address = addr_elements[0].text.strip() if addr_elements else None

            print(f'  {name}: Rating={rating}, Reviews={rev_count}, Category={category}, Address={address}')

            # Scrape reviews tab
            comp_reviews = []
            rev_tabs = driver.find_elements(By.XPATH, "//button[contains(@aria-label, 'Reviews') or (@role='tab' and contains(., 'Reviews'))]")
            if rev_tabs:
                try:
                    driver.execute_script('arguments[0].click();', rev_tabs[0])
                    time.sleep(3)
                    cards = driver.find_elements(By.CSS_SELECTOR, "div.jftiEf")
                    for card in cards[:10]:
                        try:
                            author = card.find_element(By.CSS_SELECTOR, ".d4r55").text.strip()
                        except:
                            author = 'Anonymous'
                        try:
                            star_aria = card.find_element(By.CSS_SELECTOR, "span.kvMYJc").get_attribute('aria-label')
                            m_star = re.search(r'(\d+)', star_aria)
                            star_val = int(m_star.group(1)) if m_star else 5
                        except:
                            star_val = 5
                        try:
                            rel_date = card.find_element(By.CSS_SELECTOR, "span.rsqaWe").text.strip()
                        except:
                            rel_date = 'Recent'
                        try:
                            text_el = card.find_elements(By.CSS_SELECTOR, "span.wiI7pd")
                            text_body = text_el[0].text.strip() if text_el else ''
                        except:
                            text_body = ''
                        
                        comp_reviews.append({
                            'competitor_id': cid,
                            'competitor_name': name,
                            'author': author,
                            'rating': star_val,
                            'relative_date': rel_date,
                            'text': text_body
                        })
                    print(f'    Captured {len(comp_reviews)} reviews for {name}')
                except Exception as ex:
                    print(f'    Error clicking reviews for {name}: {ex}')

            results[cid] = {
                'id': cid,
                'name': name,
                'rating': rating,
                'review_count': rev_count,
                'category': category,
                'address': address,
                'place_id': place_id,
                'reviews': comp_reviews
            }
            reviews_data.extend(comp_reviews)

    finally:
        driver.quit()

    with open('scraped_competitor_profiles.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f'Saved profile and review data for {len(results)} competitors')

if __name__ == '__main__':
    scrape_profiles(49)
