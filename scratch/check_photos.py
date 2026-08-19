import sqlite3

conn = sqlite3.connect('depor_demographic.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()

print("=== Jugadores con foto de xabicampos ===")
c.execute("SELECT id, name, photo_url FROM players WHERE photo_url LIKE '%xabicampos%'")
for r in c.fetchall():
    print(dict(r))

print("\n=== Jugador Xabi Campos ===")
c.execute("SELECT id, name, photo_url, team_id FROM players WHERE name LIKE '%Xabi%' OR name LIKE '%xabi%'")
for r in c.fetchall():
    print(dict(r))

print("\n=== Jugador David Mella ===")
c.execute("SELECT id, name, photo_url, team_id FROM players WHERE name LIKE '%Mella%'")
for r in c.fetchall():
    print(dict(r))

print("\n=== Todos los equipos ===")
c.execute("SELECT id, name FROM teams")
for r in c.fetchall():
    print(dict(r))

conn.close()
