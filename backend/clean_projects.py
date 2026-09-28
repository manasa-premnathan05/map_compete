import sys
sys.path.insert(0, '.')
from database import DatabaseManager
db = DatabaseManager()

# Delete fake/UI verification projects
fake_project_ids = [28, 29, 33, 35, 39, 40, 41, 42, 43, 44, 46, 34, 35]  # UI Verification + Test projects
# Also remove duplicate Bombay fries (keep 38, remove 37)

for pid in fake_project_ids:
    try:
        # First delete related data
        conn = db.get_connection()
        cursor = conn.cursor()
        # Delete posts for competitors in this project
        competitors = db.get_competitors(pid)
        for comp in competitors:
            cursor.execute("DELETE FROM posts WHERE competitor_id = ?", (comp['id'],))
        # Delete competitors
        cursor.execute("DELETE FROM competitors WHERE project_id = ?", (pid,))
        # Delete project
        cursor.execute("DELETE FROM projects WHERE id = ?", (pid,))
        conn.commit()
        conn.close()
        print('Deleted project ' + str(pid))
    except Exception as e:
        print('Error deleting project ' + str(pid) + ': ' + str(e))

# Remove duplicate Bombay fries (keep 38, remove 37)
try:
    conn = db.get_connection()
    cursor = conn.cursor()
    # Delete posts for competitor in project 37
    comps = db.get_competitors(37)
    for comp in comps:
        cursor.execute("DELETE FROM posts WHERE competitor_id = ?", (comp['id'],))
    cursor.execute("DELETE FROM competitors WHERE project_id = ?", (37,))
    cursor.execute("DELETE FROM projects WHERE id = ?", (37,))
    conn.commit()
    conn.close()
    print('Removed duplicate Bombay fries (ID 37)')
except Exception as e:
    print('Error removing duplicate: ' + str(e))

# Verify remaining projects
projects = db.get_projects()
print('\nRemaining projects:', len(projects))
for p in projects:
    print('  ID: ' + str(p['id']) + ' | Name: ' + p['name'] + ' | Field: ' + str(p.get('field', 'N/A')))