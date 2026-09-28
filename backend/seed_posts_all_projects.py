import sys
sys.path.insert(0, '.')
from database import DatabaseManager
db = DatabaseManager()

# Get all projects
projects = db.get_projects()
print('Projects:', len(projects))
for p in projects:
    print('  Project ' + str(p['id']) + ': ' + p['name'])

# Seed demo posts for each project that has competitors with gmap_url
demo_post_templates = [
    {
        'text_content': 'New Year, New Look! Start 2025 with a fresh haircut. Book your appointment today and get 20% off your first visit! Our expert stylists are ready to transform your look.',
        'published_date': '2025-01-15T10:00:00',
        'scrape_date': '2025-01-20T14:30:00',
        'image_urls': ['https://lh3.googleusercontent.com/demo1.jpg'],
        'cta': 'Book Now',
        'detected_topic': 'Special Promotions',
        'detected_keywords': ['new year', 'haircut', 'discount', 'booking'],
    },
    {
        'text_content': 'Introducing our new Organic Hair Spa treatment! Pamper your hair with 100% natural ingredients. Perfect for damaged or dry hair. Limited time introductory price of 1999 (regular 2999).',
        'published_date': '2025-01-10T11:30:00',
        'scrape_date': '2025-01-20T14:30:00',
        'image_urls': ['https://lh3.googleusercontent.com/demo2.jpg'],
        'cta': 'Learn More',
        'detected_topic': 'Service Highlights',
        'detected_keywords': ['organic', 'hair spa', 'treatment', 'natural'],
    },
    {
        'text_content': 'Meet our new stylist, Priya! With 8 years of experience in precision cuts and color techniques, Priya specializes in balayage and ombre. Book your session with her this week and get a free deep conditioning treatment.',
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
    existing_posts = db.get_posts(project_id=pid, limit=1)
    if competitors_with_url and not existing_posts:
        print('Seeding posts for project ' + str(pid) + ': ' + project['name'])
        for comp in competitors_with_url[:2]:
            for template in demo_post_templates:
                post_data = template.copy()
                post_data['competitor_id'] = comp['id']
                post_data['post_url'] = 'https://www.google.com/maps/place/' + comp['name'].replace(' ', '+') + '/posts/demo' + str(pid)
                db.add_post(comp['id'], post_data)
        seeded = len(demo_post_templates) * min(2, len(competitors_with_url))
        print('  Seeded ' + str(seeded) + ' posts')

# Verify
for project in projects:
    pid = project['id']
    posts = db.get_posts(project_id=pid, limit=100)
    print('Project ' + str(pid) + ' (' + project['name'] + '): ' + str(len(posts)) + ' posts')