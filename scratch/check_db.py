import sqlite3
conn = sqlite3.connect('depor_demographic.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT id, name, photo_url, seasons_data FROM players WHERE team_id='depor' LIMIT 30")
rows = c.fetchall()
for r in rows:
    d = dict(r)
    print(d['id'], '|', d['name'], '|', d['photo_url'], '| seasons:', bool(d['seasons_data']))

print("\n--- MATCHES ---")
c.execute("SELECT id, team_id, opponent, date, result_type FROM matches ORDER BY date DESC LIMIT 20")
mrows = c.fetchall()
for r in mrows:
    print(dict(r))

conn.close()
