import sqlite3

conn = sqlite3.connect("depor_demographic.db")
c = conn.cursor()

for team in ['depor', 'penafiel', 'fabril']:
    c.execute("SELECT id, name, team_id, detailed_position FROM players WHERE team_id = ?", (team,))
    rows = c.fetchall()
    print(f"\n--- TEAM: {team} ({len(rows)} players) ---")
    for r in rows:
        print(f"  ID: {r[0]:20s} | Name: {r[1]:30s} | Pos: {r[3]}")

conn.close()
