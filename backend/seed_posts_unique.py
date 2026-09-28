import sys
sys.path.insert(0, '.')
from database import DatabaseManager
db = DatabaseManager()

# Get all projects
projects = db.get_projects()
print('Projects:', len(projects))

# Delete existing demo posts to reseed
from database import DatabaseManager
db2 = DatabaseManager()
conn = db2.get_connection()
cursor = conn.cursor()
cursor.execute("DELETE FROM posts WHERE post_url LIKE '%demo%'")
conn.commit()
conn.close()
print('Cleared old demo posts')

# Reseed with unique content per project
demo_post_templates = [
    {
        'base_text': 'New Year, New Look! Start 2025 with a fresh haircut. Book your appointment today and get 20% off your first visit! Our expert stylists are ready to transform your look.',
        'published_date': '2025-01-15T10:00:00',
        'scrape_date': '2025-01-20T14:30:00',
        'image_urls': ['https://lh3.googleusercontent.com/demo1.jpg'],
        'cta': 'Book Now',
        'detected_topic': 'Special Promotions',
        'detected_keywords': ['new year', 'haircut', 'discount', 'booking'],
    },
    {
        'base_text': 'Introducing our new Organic Hair Spa treatment! Pamper your hair with 100% natural ingredients. Perfect for damaged or dry hair. Limited time introductory price of 1999 (regular 2999).',
        'published_date': '2025-01-10T11:30:00',
        'scrape_date': '2025-01-20T14:30:00',
        'image_urls': ['https://lh3.googleusercontent.com/demo2.jpg'],
        'cta': 'Learn More',
        'detected_topic': 'Service Highlights',
        'detected_keywords': ['organic', 'hair spa', 'treatment', 'natural'],
    },
    {
        'base_text': 'Meet our new stylist, Priya! With 8 years of experience in precision cuts and color techniques, Priya specializes in balayage and ombre. Book your session with her this week and get a free deep conditioning treatment.',
        'published_date': '2025-01-05T09:00:00',
        'scrape_date': '2025-01-20T14:30:00',
        'image_urls': ['https://lh3.googleusercontent.com/demo3.jpg'],
        'cta': 'Book with Priya',
        'detected_topic': 'Team Updates',
        'detected_keywords': ['stylist', 'balayage', 'color', 'haircut'],
    },
]

for project in projects:
    pid = project['id']
    competitors = db.get_competitors(pid)
    competitors_with_url = [c for c in competitors if c.get('gmap_url')]
    if not competitors_with_url:
        continue
    
    print('Seeding for project ' + str(pid) + ': ' + project['name'])
    for comp_idx, comp in enumerate(competitors_with_url[:2]):
        for t_idx, template in enumerate(demo_post_templates):
            post_data = template.copy()
            # Make content unique per project/competitor/template
            post_data['text_content'] = template['base_text'] + ' [Project: ' + project['name'] + ', Competitor: ' + comp['name'] + ']'
            post_data['competitor_id'] = comp['id']
            post_data['post_url'] = 'https://www.google.com/maps/place/' + comp['name'].replace(' ', '+') + '/posts/demo' + str(pid) + '_' + str(comp_idx) + '_' + str(t_idx)
            db.add_post(comp['id'], post_data)
    posts = db.get_posts(project_id=pid, limit=100)
    print('  Project ' + str(pid) + ' (' + project['name'] + '): ' + str(len(posts)) + ' posts')

print('\nDone!')