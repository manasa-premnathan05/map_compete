import sys
sys.path.insert(0, '.')
from database import DatabaseManager
db = DatabaseManager()

projects = db.get_projects()
print('Total projects:', len(projects))
for p in projects:
    print('  ID: ' + str(p['id']) + ' | Name: ' + p['name'] + ' | Field: ' + str(p.get('field', 'N/A')))