import urllib.request, json, time, sys
sys.stdout.reconfigure(encoding='utf-8')

time.sleep(2)
# 1. Test trend-analysis endpoint
req1 = urllib.request.Request('http://127.0.0.1:5000/api/projects/49/trend-analysis')
with urllib.request.urlopen(req1, timeout=10) as r:
    data = json.loads(r.read())
    print('Trend Analysis API status:', r.status)
    print('Topics count:', len(data['topic_trends']))
    for t in data['topic_trends']:
        pct = t['occurrence_pct']
        print(f"  {t['topic']}: {t['competitors_using']}/{t['total_competitors']} comps, {t['occurrence']} posts ({pct}%), direction={t['trend_direction']}")

# 2. Test ideas generation with count = 10
req2 = urllib.request.Request(
    'http://127.0.0.1:5000/api/projects/49/ideas',
    data=json.dumps({'count': 10}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
with urllib.request.urlopen(req2, timeout=60) as r:
    ideas_data = json.loads(r.read())
    print('\nIdeas API status:', r.status)
    ideas = ideas_data.get('ideas', [])
    print('Generated ideas count:', len(ideas))
    for idx, idea in enumerate(ideas[:4], 1):
        txt = idea.get('update_text') or idea.get('idea_text') or ''
        topic = idea.get('detected_topic') or 'Product'
        print(f"  [{idx}] [{topic}]: {txt[:75]}...")

    # Check for competitor names
    comp_names = ['Zudio', 'Park Avenue', 'Crazy world', 'M&Z Fashion']
    violations = [c for idea in ideas for c in comp_names if c.lower() in (idea.get('update_text') or '').lower()]
    print('Competitor violations:', violations)
    assert len(violations) == 0, 'Found competitor name violations in generated ideas!'

print('\nALL LIVE API TESTS PASSED!')
