import sys
sys.path.insert(0, '.')
from database import DatabaseManager
db = DatabaseManager()

# Delete all demo posts
conn = db.get_connection()
cursor = conn.cursor()
cursor.execute("DELETE FROM posts WHERE post_url LIKE '%demo%'")
conn.commit()
conn.close()
print('Deleted demo posts')

# Verify
for pid in [1, 2, 27, 28]:
    posts = db.get_posts(project_id=pid, limit=100)
    print('Project ' + str(pid) + ': ' + str(len(posts)) + ' posts remaining')