import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'backend')
from ai_service import GeminiAIService

svc = GeminiAIService()
comp_names = ['Zudio', 'Park Avenue', 'Crazy world', 'M&Z Fashion']
trending_topics = ['New Collection', 'Casual & Streetwear', 'Occasion & Party Wear']

for count in [3, 10, 50]:
    ideas = svc._fallback_ideas([], count, business_name='neusta', competitor_names=comp_names, trending_topics=trending_topics)
    print(f'Requested {count}, Generated {len(ideas)} ideas')
    first = ideas[0]
    last = ideas[-1]
    print(f"  First #1 [{first.get('detected_topic')}]: {first.get('update_text')[:80]}...")
    print(f"  Last #{len(ideas)} [{last.get('detected_topic')}]: {last.get('update_text')[:80]}...")

    violations = [c for idea in ideas for c in comp_names if c.lower() in (idea.get('update_text') or '').lower()]
    assert len(violations) == 0, f'Found competitor violations: {violations}'

print('\nALL FALLBACK COUNTS (3, 10, 50) PASS WITH ZERO COMPETITOR NAMES!')

from database import DatabaseManager
db = DatabaseManager('backend/competitor_intelligence.db')
trends = db.get_trend_analysis(49)
print(f"\nProject 49 Trend Analysis:")
print(f"Total posts: {trends['total_posts']} | Total competitors: {trends['total_competitors']}")
print("\nTopic trends:")
for t in trends['topic_trends']:
    print(f"  {t['topic']} | {t['competitors_using']} of {t['total_competitors']} comps | {t['occurrence']} posts ({t['occurrence_pct']}%) | Trend: {t['trend_direction']}")

print("\nTop 5 Keywords:")
for k in trends['keyword_trends'][:5]:
    print(f"  {k['keyword']} | {k['competitors_using']} comps | {k['occurrence']} occurrences ({k['occurrence_pct']}%)")

print("\nMonthly volume:", trends['monthly_volume'])

