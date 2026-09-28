import sys
sys.path.insert(0, '.')
from api import app

with app.test_client() as client:
    response = client.get('/api/debug/routes')
    print('Status:', response.status_code)
    if response.status_code == 200:
        import json
        data = json.loads(response.data)
        for r in data['routes']:
            if 'project' in r['rule']:
                print(f"  {r['rule']} -> {r['endpoint']}")