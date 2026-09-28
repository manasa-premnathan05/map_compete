from backend.database import DatabaseManager
db = DatabaseManager()

# Test project places
places = db.get_project_places(1)
print('Project places for project 1:', len(places))
for p in places:
    print(f'  {p["name"]} (key: {p["place_key"]})')

# Test place lookup by key
place = db.get_place_by_key('cid:101')
print('\nPlace by key cid:101:', place['name'] if place else 'Not found')

# Test place projects
projects = db.get_place_projects(1)
print('\nProjects tracking place 1:', len(projects))
for p in projects:
    print(f'  {p["name"]}')