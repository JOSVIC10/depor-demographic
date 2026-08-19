"""
Script para hacer push de TODOS los datos de la DB local a Supabase.
Ejecutar localmente antes del push a Git para asegurarse de que
Supabase tiene todos los datos actualizados.

Uso: python push_to_supabase.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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


def upsert(table, data):
    if not data:
        return True
    r = requests.post(
        f"{SUPABASE_URL}/rest/v1/{table}",
        headers=HEADERS,
        json=data,
        timeout=30
    )
    if r.status_code in [200, 201]:
        print(f"  [{table}] OK - {len(data)} rows")
        return True
    else:
        print(f"  [{table}] ERROR {r.status_code}: {r.text[:200]}")
        return False


def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("=== Pushing data to Supabase ===\n")

    # Teams
    rows = [dict(r) for r in conn.execute("SELECT id, name, season, club_name FROM teams").fetchall()]
    upsert("teams", rows)

    # Players
    raw = [dict(r) for r in conn.execute("SELECT * FROM players").fetchall()]
    players = []
    for p in raw:
        players.append({
            "id": p["id"], "name": p["name"], "birthdate": p["birthdate"],
            "detailed_position": p["detailed_position"], "derived_category": p["derived_category"],
            "team_id": p["team_id"], "pitch_x": p.get("pitch_x"), "pitch_y": p.get("pitch_y"),
            "photo_url": p.get("photo_url"), "minutes_played": p.get("minutes_played", 0) or 0,
            "starts": p.get("starts", 0) or 0, "subs_in": p.get("subs_in", 0) or 0,
            "yellow_cards": p.get("yellow_cards", 0) or 0, "red_cards": p.get("red_cards", 0) or 0,
            "goals": p.get("goals", 0) or 0, "seasons_data": p.get("seasons_data"),
            "is_injured": p.get("is_injured", 0) or 0,
            "injury_description": p.get("injury_description") or "",
            "injury_return_time": p.get("injury_return_time") or "",
            "injury_phase": p.get("injury_phase") or "",
            "extra_pitch_team_id": p.get("extra_pitch_team_id"),
        })
    upsert("players", players)

    # Matches
    raw = [dict(r) for r in conn.execute("SELECT * FROM matches").fetchall()]
    matches = []
    for m in raw:
        st = m.get("substitution_times", "[]")
        try:
            st = json.loads(st) if isinstance(st, str) else st
        except Exception:
            st = []
        matches.append({
            "id": m["id"], "team_id": m["team_id"], "opponent": m["opponent"],
            "date": m["date"], "result_type": m["result_type"],
            "home_goals": m["home_goals"], "away_goals": m["away_goals"],
            "is_home": m["is_home"], "competition": m.get("competition") or "LALIGA HYPERMOTION",
            "match_type": m.get("match_type") or "LIGA", "matchday": m.get("matchday") or "",
            "custom_title": m.get("custom_title"),
            "playing_time": m.get("playing_time") or "90 Minutes",
            "substitute_cadence": m.get("substitute_cadence") or "",
            "substitution_times": st,
        })
    upsert("matches", matches)

    # Lineup entries — only upload those with valid player references
    valid_player_ids = set(p["id"] for p in all_players_raw)
    raw = [dict(r) for r in conn.execute("SELECT * FROM lineup_entries").fetchall()]
    lineups = []
    skipped = 0
    for le in raw:
        if le["player_id"] not in valid_player_ids:
            skipped += 1
            continue  # skip orphaned entries
        lineups.append({
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
    if skipped:
        print(f"  [lineup_entries] Saltando {skipped} entradas huerfanas")
    # Push in batches of 100
    BATCH = 100
    ok_count = 0
    for i in range(0, len(lineups), BATCH):
        batch = lineups[i:i+BATCH]
        if upsert("lineup_entries", batch):
            ok_count += len(batch)
    print(f"  [lineup_entries] Total subidas: {ok_count}/{len(lineups)}")


    # Substitutions
    raw = [dict(r) for r in conn.execute("SELECT * FROM substitutions").fetchall()]
    subs = [
        {"id": s["id"], "match_id": s["match_id"], "player_out_id": s["player_out_id"],
         "player_in_id": s["player_in_id"], "minute": s["minute"]}
        for s in raw
    ]
    upsert("substitutions", subs)

    conn.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
