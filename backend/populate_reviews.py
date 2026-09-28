import json
import sqlite3
import re
from datetime import datetime, timedelta

def migrate_and_populate_reviews():
    conn = sqlite3.connect('competitor_intelligence.db')
    c = conn.cursor()

    # 1. Add columns to competitors if not present
    c.execute("PRAGMA table_info(competitors)")
    cols = [col[1] for col in c.fetchall()]
    if 'rating' not in cols:
        c.execute("ALTER TABLE competitors ADD COLUMN rating REAL")
    if 'review_count' not in cols:
        c.execute("ALTER TABLE competitors ADD COLUMN review_count INTEGER")

    # 2. Add columns to places if not present
    c.execute("PRAGMA table_info(places)")
    pcols = [col[1] for col in c.fetchall()]
    if 'rating' not in pcols:
        c.execute("ALTER TABLE places ADD COLUMN rating REAL")
    if 'review_count' not in pcols:
        c.execute("ALTER TABLE places ADD COLUMN review_count INTEGER")

    # 3. Create reviews table
    c.execute('''
    CREATE TABLE IF NOT EXISTS reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        competitor_id INTEGER NOT NULL,
        author TEXT,
        rating INTEGER,
        relative_date TEXT,
        review_date TEXT,
        text_content TEXT,
        sentiment TEXT,
        sentiment_score REAL,
        detected_topic TEXT,
        detected_keywords TEXT,
        source_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
        FOREIGN KEY (competitor_id) REFERENCES competitors(id) ON DELETE CASCADE
    )
    ''')
    conn.commit()

    # Load scraped profiles
    with open('scraped_competitor_profiles.json', 'r', encoding='utf-8') as f:
        profiles = json.load(f)

    # Topic classification helper
    topic_keywords = {
        "Staff & Service": ["staff", "service", "ram", "ayan", "shankar", "polite", "helpful", "behaviour", "rude", "customer", "sales executive", "knowledge"],
        "Pricing & Discounts": ["price", "prices", "discount", "discounts", "rate", "cost", "cheap", "budget", "affordable", "costly", "expensive", "bill", "rupee", "money"],
        "Collection & Variety": ["collection", "variety", "suits", "blazer", "blazers", "shirt", "shirts", "two-piece", "stock", "stocks", "t-shirt", "clothes", "trendy", "fashion"],
        "Quality & Fit": ["quality", "fit", "fits", "material", "fabric", "defective", "perfect", "neat", "exclusive"],
        "School Uniforms": ["uniform", "uniforms", "school", "dav", "rtps", "supplies", "ties", "belts", "shoes", "socks", "kamothe", "lrt"],
        "Store Experience": ["experience", "store", "shop", "shopping", "layout", "ambience", "atmosphere", "parking"]
    }

    def detect_topic(text):
        lower = text.lower()
        best_topic = "General Experience"
        best_score = 0
        for topic, kws in topic_keywords.items():
            score = sum(1 for kw in kws if kw in lower)
            if score > best_score:
                best_score = score
                best_topic = topic
        return best_topic

    def detect_keywords(text):
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        stopwords = {'the', 'and', 'for', 'was', 'with', 'this', 'that', 'they', 'are', 'not', 'have', 'had', 'from', 'one', 'all', 'you', 'very', 'here', 'out'}
        return [w for w in set(words) if w not in stopwords][:6]

    def parse_relative_date(rel_str):
        # returns approximate ISO date
        now = datetime.now()
        rel_str = rel_str.lower().replace('edited', '').strip()
        m = re.search(r'(\d+)\s*(month|year|week|day|hour)', rel_str)
        if m:
            val = int(m.group(1))
            unit = m.group(2)
            if 'month' in unit:
                return (now - timedelta(days=val * 30)).strftime('%Y-%m-%d')
            elif 'year' in unit:
                return (now - timedelta(days=val * 365)).strftime('%Y-%m-%d')
            elif 'week' in unit:
                return (now - timedelta(days=val * 7)).strftime('%Y-%m-%d')
            elif 'day' in unit:
                return (now - timedelta(days=val)).strftime('%Y-%m-%d')
        elif 'a year ago' in rel_str:
            return (now - timedelta(days=365)).strftime('%Y-%m-%d')
        elif 'a month ago' in rel_str:
            return (now - timedelta(days=30)).strftime('%Y-%m-%d')
        elif 'a week ago' in rel_str:
            return (now - timedelta(days=7)).strftime('%Y-%m-%d')
        return now.strftime('%Y-%m-%d')

    # Clear existing reviews for project 49 competitors
    comp_ids = list(profiles.keys())
    c.execute(f"DELETE FROM reviews WHERE competitor_id IN ({','.join(['?']*len(comp_ids))})", comp_ids)

    inserted_count = 0
    for cid_str, data in profiles.items():
        cid = int(cid_str)
        rating = data.get('rating')
        review_count = data.get('review_count')
        address = data.get('address')
        place_id = data.get('place_id')

        # Update competitor
        c.execute("""
            UPDATE competitors 
            SET rating = ?, review_count = ?, address = COALESCE(?, address)
            WHERE id = ?
        """, (rating, review_count, address, cid))

        if place_id:
            c.execute("""
                UPDATE places 
                SET rating = ?, review_count = ?, address = COALESCE(?, address)
                WHERE id = ?
            """, (rating, review_count, address, place_id))

        # Insert reviews
        reviews = data.get('reviews', [])
        for rev in reviews:
            r_rating = rev.get('rating', 5)
            rel_date = rev.get('relative_date', 'Recent')
            rev_date = parse_relative_date(rel_date)
            text = rev.get('text', '')

            # Sentiment calculation
            if r_rating >= 4:
                sentiment = "Positive"
                sentiment_score = 0.8
            elif r_rating == 3:
                sentiment = "Neutral"
                sentiment_score = 0.0
            else:
                sentiment = "Negative"
                sentiment_score = -0.8

            # If text has strong negative words
            if any(w in text.lower() for w in ['rude', 'worst', 'harresing', 'poor', 'crazy prices', 'terrible']):
                sentiment = "Negative"
                sentiment_score = -0.9

            topic = detect_topic(text)
            kws = detect_keywords(text)

            c.execute("""
                INSERT INTO reviews (
                    project_id, competitor_id, author, rating, relative_date,
                    review_date, text_content, sentiment, sentiment_score,
                    detected_topic, detected_keywords, source_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                49, cid, rev.get('author'), r_rating, rel_date,
                rev_date, text, sentiment, sentiment_score,
                topic, json.dumps(kws), None
            ))
            inserted_count += 1

    conn.commit()
    conn.close()
    print(f"Successfully updated competitors & places, and inserted {inserted_count} real reviews for Project 49.")

if __name__ == '__main__':
    migrate_and_populate_reviews()
