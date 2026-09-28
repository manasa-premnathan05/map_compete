from backend.database import DatabaseManager
from backend.place_identity import extract_place_identity

db = DatabaseManager()

# Test place identity extraction
identity = extract_place_identity(
    gmap_url='https://www.google.com/maps/place/Amber+Chinese/@19.033,73.029,17z/data=!3m1!4b1!4m6!3m5!1s0x3be7e96f92ea224f:0xa9ff73e60b0c7c2a!8m2!3d19.033!4d73.029!16s%2Fg%2F11c5w7v8x9',
    name='Amber Chinese'
)
print('Identity:', identity['place_key'])
print('Source:', identity['identity_source'])
print('Confidence:', identity['confidence'])
print('Strong:', identity['is_strong'])
print('Google Place ID:', identity['google_place_id'])
print('Hex ID:', identity['hex_id'])

# Test database operations
projects = db.get_projects()
print(f'\nProjects: {len(projects)}')
for p in projects[:2]:
    print(f'  {p["name"]} (place_key: {p.get("place_key")})')

competitors = db.get_competitors(1)
print(f'\nCompetitors for project 1: {len(competitors)}')
for c in competitors[:3]:
    print(f'  {c["name"]} (place_key: {c.get("place_key")}, source: {c.get("identity_source")})')

places = db.get_places()
print(f'\nTotal canonical places: {len(places)}')
for p in places[:3]:
    print(f'  {p["name"]} (key: {p["place_key"]}, source: {p["identity_source"]})')