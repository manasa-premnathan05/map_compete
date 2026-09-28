import urllib.request, json, sys
sys.stdout.reconfigure(encoding='utf-8')

# Wait for Flask to start
import time
time.sleep(3)

# Test generate ideas for project 49 — should NOT contain competitor names
req = urllib.request.Request(
    'http://127.0.0.1:5000/api/projects/49/ideas',
    data=json.dumps({'count': 3}).encode(),
    headers={'Content-Type': 'application/json'},
    method='POST'
)
try:
    r = urllib.request.urlopen(req, timeout=35)
    d = json.loads(r.read())
    ideas = d.get('ideas', [])

    # Known competitor names for P49
    competitor_names = ['Zudio', 'Park Avenue', 'Crazy world', 'M&Z Fashion', 'Linenism']

    print(f'Generated {len(ideas)} ideas:')
    has_violation = False
    for i, idea in enumerate(ideas):
        text = idea.get('update_text', idea.get('idea_text', ''))
        kws  = idea.get('keywords', [])
        cta  = idea.get('cta', '')
        img  = (idea.get('image_concept') or '')[:80]

        # Check for competitor name violations
        violations = [c for c in competitor_names if c.lower() in text.lower()]
        kw_violations = [k for k in kws for c in competitor_names if c.lower() in k.lower()]

        print(f'\n[{i+1}] {text[:120]}')
        print(f'     KW: {kws[:3]} | CTA: {cta}')
        if img: print(f'     Img: {img}')
        if violations:
            print(f'     !!! VIOLATION: competitor name found in text: {violations}')
            has_violation = True
        elif kw_violations:
            print(f'     !!! VIOLATION: competitor name in keyword: {kw_violations}')
            has_violation = True
        else:
            print(f'     CLEAN: no competitor names detected')

    print('\n' + ('FAIL: competitor name found in generated posts!' if has_violation else 'PASS: all posts clean — no competitor names'))
except Exception as e:
    print(f'Error: {type(e).__name__}: {e}')
