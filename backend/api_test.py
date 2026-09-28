import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Quick live API tests
tests = [
    ('market-overview P49', '/api/projects/49/market-overview'),
    ('market-gaps P49', '/api/projects/49/market-gaps'),
    ('market-overview P1', '/api/projects/1/market-overview'),
    ('market-gaps P27', '/api/projects/27/market-gaps'),
    ('market-overview P32', '/api/projects/32/market-overview'),
    ('review-analytics P49', '/api/projects/49/reviews/analytics'),
]
all_ok = True
for name, path in tests:
    try:
        r = urllib.request.urlopen('http://127.0.0.1:5000' + path)
        d = json.loads(r.read())
        if 'competitors' in d:
            last = d['competitors'][-1]['name'] if d['competitors'] else 'none'
            print(f'{name} OK. Last={last}  pos={d.get("positive_sentiment_pct", "?")}%')
        elif 'gaps' in d:
            print(f'{name} OK. {len(d["gaps"])} gaps returned')
        elif 'sentiment_distribution' in d:
            sd = d['sentiment_distribution']
            print(f'{name} OK. Sentiment: {sd}')
    except Exception as e:
        print(f'{name} FAIL: {e}')
        all_ok = False
print('All tests passed!' if all_ok else 'Some tests failed.')
