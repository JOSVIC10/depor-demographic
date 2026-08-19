"""
Script para investigar y arreglar el error de lineup_entries en Supabase.
Encuentra las entradas huerfanas y las elimina antes del push.
"""
import sqlite3
import json
import requests

SUPABASE_URL = "https://evphxfveswschcbivrkl.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2cGh4ZnZlc3dzY2hjYml2cmtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwMzcxNjksImV4cCI6MjEwMjYxMzE2OX0.WbC5XVgwaVXwnuOtl_91iwvZZkDa2pVX2d2Bo0nSt8Y"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates",
}

DB_PATH = "depor_demographic.db"
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

# Obtener todos los player_ids validos en la DB local
valid_players = set(r[0] for r in conn.execute("SELECT id FROM players").fetchall())
print(f"Jugadores validos en SQLite: {len(valid_players)}")

# Obtener todas las lineup_entries y encontrar las huerfanas
lineups_raw = [dict(r) for r in conn.execute("SELECT * FROM lineup_entries").fetchall()]
print(f"Total lineup_entries en SQLite: {len(lineups_raw)}")

orphaned = [le for le in lineups_raw if le["player_id"] not in valid_players]
valid_lineups = [le for le in lineups_raw if le["player_id"] in valid_players]

print(f"Entradas huerfanas (player no existe): {len(orphaned)}")
print(f"Entradas validas: {len(valid_lineups)}")

if orphaned:
    print("\nPlayer IDs huerfanos:")
    orphan_pids = set(le["player_id"] for le in orphaned)
    for pid in sorted(orphan_pids):
        count = sum(1 for le in orphaned if le["player_id"] == pid)
        print(f"  {pid} -> {count} lineup entries sin jugador")

# Limpiar entradas huerfanas de SQLite tambien
if orphaned:
    print(f"\nEliminando {len(orphaned)} entradas huerfanas de SQLite...")
    for le in orphaned:
        conn.execute("DELETE FROM lineup_entries WHERE id = ?", (le["id"],))
    conn.commit()
    print("OK - SQLite limpiado")

conn.close()

# Ahora subir las lineup_entries validas a Supabase
print(f"\nSubiendo {len(valid_lineups)} lineup_entries validas a Supabase...")

sb_lineups = []
for le in valid_lineups:
    sb_lineups.append({
        "id": le["id"], "match_id": le["match_id"], "player_id": le["player_id"],
        "is_starter": le.get("is_starter", 0),
        "is_substitute": 0 if le.get("is_starter") else 1,
        "grid_x": le.get("grid_x") or 0.5, "grid_y": le.get("grid_y") or 0.5,
        "position_label": le.get("field_position") or "POS",
        "minute_in": le.get("sub_in_minute"), "minute_out": le.get("sub_out_minute"),
        "minutes_played": le.get("minutes_played") or 0,
        "has_yellow_card": le.get("has_yellow_card") or 0,
        "has_red_card": le.get("has_red_card") or 0,
        "card_minute": le.get("card_minute"), "card_type": le.get("card_type"),
        "goals": le.get("goals") or 0,
    })

# Subir en lotes de 100 para evitar timeouts
BATCH_SIZE = 100
total_ok = 0
for i in range(0, len(sb_lineups), BATCH_SIZE):
    batch = sb_lineups[i:i+BATCH_SIZE]
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/lineup_entries",
        headers=HEADERS,
        json=batch,
        timeout=30
    )
    if r.status_code in [200, 201]:
        total_ok += len(batch)
        print(f"  Lote {i//BATCH_SIZE + 1}: OK ({len(batch)} filas)")
    else:
        print(f"  Lote {i//BATCH_SIZE + 1}: ERROR {r.status_code} - {r.text[:200]}")

print(f"\nTotal lineup_entries subidas: {total_ok}/{len(valid_lineups)}")

# Tambien subir substitutions
print("\nSubiendo substitutions...")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
subs_raw = [dict(r) for r in conn.execute("SELECT * FROM substitutions").fetchall()]
conn.close()

valid_subs = [s for s in subs_raw 
              if s["player_out_id"] in valid_players and s["player_in_id"] in valid_players]
print(f"Substitutions validas: {len(valid_subs)}/{len(subs_raw)}")

if valid_subs:
    sb_subs = [
        {"id": s["id"], "match_id": s["match_id"], "player_out_id": s["player_out_id"],
         "player_in_id": s["player_in_id"], "minute": s["minute"]}
        for s in valid_subs
    ]
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/substitutions",
        headers=HEADERS,
        json=sb_subs,
        timeout=30
    )
    if r.status_code in [200, 201]:
        print(f"  [substitutions] OK - {len(sb_subs)} filas")
    else:
        print(f"  [substitutions] ERROR {r.status_code}: {r.text[:200]}")

print("\nDone!")
