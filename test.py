import sys
import os
sys.path.insert(0, r"c:\Users\Jose Vicente\Desktop\Depor - Demographic")

from backend import database as db
conn = db.get_connection()
c = conn.cursor()
c.execute("SELECT id, name, team_id, photo_url FROM players")
rows = c.fetchall()
with_photo = [r for r in rows if r['photo_url']]
without_photo = [r for r in rows if not r['photo_url']]
print(f"Total players: {len(rows)}")
print(f"With photo: {len(with_photo)}")
print(f"Without photo: {len(without_photo)}")
for r in without_photo:
    print(f"  NO PHOTO: {r['id']} - {r['name']} ({r['team_id']})")
