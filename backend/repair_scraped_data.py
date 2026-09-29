#!/usr/bin/env python3
"""Repair data captured before the industry-aware topic fix.

Three problems are fixed in one pass:

1. **Junk "place card" posts** — an older scraper version stored Google Maps
   *related-place cards* ("Blue's Kitchen ... 4.5(951) Thai ... Dine-in") as
   posts. They have no publication date and belong to other businesses, so
   they polluted trending topics with wrong entries. They are deleted.
2. **Wrong topics** — every project used the fashion/salon keyword lists, so a
   cafe review could be labelled "New Collection" (matched "drop by") or
   "Casual & Streetwear" (matched "Casual Asian eatery"). Posts and reviews
   are re-classified with the industry profile of their project.
3. **Review sentiment/topics** — reviews without a rating get their sentiment
   recomputed from text.

Usage (from the ``backend`` directory or the repository root)::

    python backend/repair_scraped_data.py            # dry run (safe)
    python backend/repair_scraped_data.py --apply    # write the changes
"""

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from topic_classifier import (  # noqa: E402
    classify_sentiment,
    classify_topic,
    extract_keywords,
    infer_industry,
)

DEFAULT_DB = str(Path(__file__).resolve().parent / 'competitor_intelligence.db')

# Markers that only appear on Google Maps place-suggestion cards, never in a
# review or an owner update.
PLACE_CARD_MARKERS = (
    'Dine-in', 'Takeaway', 'No-contact delivery', 'Drive-through',
    'On-site services', 'Temporarily closed', 'Closes ', 'Opens ',
)
RATING_PATTERN = re.compile(r'\d\.\d\(')


def looks_like_place_card(text: str) -> bool:
    if not text:
        return False
    if RATING_PATTERN.search(text):
        return True
    return any(marker in text for marker in PLACE_CARD_MARKERS)


def load_projects(cursor):
    cursor.execute('SELECT id, name, field, our_profile FROM projects')
    projects = {}
    for row in cursor.fetchall():
        projects[row['id']] = {
            'name': row['name'],
            'industry': infer_industry(row['field'], row['our_profile']),
        }
    return projects


def project_industry_for_competitor(cursor, projects, competitor_id):
    cursor.execute(
        'SELECT project_id FROM competitors WHERE id = ?', (competitor_id,)
    )
    row = cursor.fetchone()
    if not row:
        return 'generic'
    project = projects.get(row['project_id']) or {}
    return project.get('industry') or 'generic'


def repair(db_path: str, apply_changes: bool = False):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    projects = load_projects(cursor)
    print(f'projects: {len(projects)}')

    # ------------------------------------------------------------------
    # 1. Delete junk place-card posts (undated + card markers only)
    # ------------------------------------------------------------------
    cursor.execute("""
        SELECT p.id, p.text_content, c.project_id
        FROM posts p
        JOIN competitors c ON c.id = p.competitor_id
        WHERE p.published_date IS NULL
    """)
    junk_ids = [
        row['id'] for row in cursor.fetchall()
        if looks_like_place_card(row['text_content'])
    ]
    print(f'junk place-card posts to delete: {len(junk_ids)}')

    # ------------------------------------------------------------------
    # 2. Re-classify posts with the project's industry profile
    # ------------------------------------------------------------------
    cursor.execute("""
        SELECT p.id, p.text_content, p.detected_topic, p.detected_keywords,
               c.project_id
        FROM posts p
        JOIN competitors c ON c.id = p.competitor_id
    """)
    post_updates = []
    for row in cursor.fetchall():
        text = row['text_content'] or ''
        if not text:
            continue
        project = projects.get(row['project_id']) or {}
        industry = project.get('industry') or 'generic'
        topic, matches = classify_topic(text, industry)
        keywords = matches or extract_keywords(text)
        if topic != row['detected_topic'] or not row['detected_keywords']:
            post_updates.append((topic, json.dumps(keywords), row['id']))
    print(f'posts to re-classify: {len(post_updates)}')

    # ------------------------------------------------------------------
    # 3. Re-classify reviews (topics + sentiment)
    # ------------------------------------------------------------------
    cursor.execute("""
        SELECT id, competitor_id, text_content, rating
        FROM reviews
    """)
    review_updates = []
    for row in cursor.fetchall():
        text = row['text_content'] or ''
        if not text:
            continue
        industry = project_industry_for_competitor(cursor, projects, row['competitor_id'])
        topic, matches = classify_topic(text, industry)
        keywords = matches or extract_keywords(text)
        sentiment, score = classify_sentiment(text, row['rating'])
        review_updates.append(
            (topic, json.dumps(keywords), sentiment, score, row['id'])
        )
    print(f'reviews to re-classify: {len(review_updates)}')

    if not apply_changes:
        print()
        print('DRY RUN - nothing written. Re-run with --apply to persist.')
        conn.close()
        return

    # Ensure the reviews.content_hash column exists (schema migration).
    cursor.execute('PRAGMA table_info(reviews)')
    review_cols = {row['name'] for row in cursor.fetchall()}
    if review_cols and 'content_hash' not in review_cols:
        cursor.execute('ALTER TABLE reviews ADD COLUMN content_hash TEXT')
        print('migrated: added reviews.content_hash')

    if junk_ids:
        cursor.executemany('DELETE FROM posts WHERE id = ?', [(i,) for i in junk_ids])
    if post_updates:
        cursor.executemany(
            'UPDATE posts SET detected_topic = ?, detected_keywords = ? WHERE id = ?',
            post_updates,
        )
    if review_updates:
        cursor.executemany(
            'UPDATE reviews SET detected_topic = ?, detected_keywords = ?, '
            'sentiment = ?, sentiment_score = ? WHERE id = ?',
            review_updates,
        )
    conn.commit()

    # Report the fresh topic distribution so the result is verifiable.
    for project_id, project in projects.items():
        cursor.execute("""
            SELECT p.detected_topic, COUNT(*) AS n
            FROM posts p JOIN competitors c ON c.id = p.competitor_id
            WHERE c.project_id = ?
            GROUP BY p.detected_topic ORDER BY n DESC LIMIT 6
        """, (project_id,))
        distribution = ', '.join(
            f"{row['detected_topic']}({row['n']})" for row in cursor.fetchall()
        )
        print(f"project {project_id} [{project['name']} / {project['industry']}]: "
              f"{distribution or 'no posts'}")

    conn.close()
    print()
    print(f'applied: {len(junk_ids)} junk posts deleted, '
          f'{len(post_updates)} posts and {len(review_updates)} reviews re-classified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default=DEFAULT_DB, help='path to the SQLite database')
    parser.add_argument('--apply', action='store_true',
                        help='write changes (default is a dry run)')
    args = parser.parse_args()
    repair(args.db, apply_changes=args.apply)

