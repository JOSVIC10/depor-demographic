import sqlite3
import os
import uuid
import pandas as pd
from typing import List, Optional, Dict
from backend.models import Player, Team, Match, LineupEntry, SubstitutionEvent, derive_position_category, calculate_age

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "depor_demographic.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS teams (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        season TEXT NOT NULL,
        club_name TEXT NOT NULL
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS players (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        birthdate TEXT NOT NULL,
        detailed_position TEXT NOT NULL,
        derived_category TEXT NOT NULL,
        team_id TEXT NOT NULL,
        pitch_x REAL,
        pitch_y REAL,
        FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
    );
    """)
    
    # Check if columns exist in players
    cursor.execute("PRAGMA table_info(players)")
    p_cols = [c[1] for c in cursor.fetchall()]
    new_cols = [
        ("pitch_x", "REAL"),
        ("pitch_y", "REAL"),
        ("photo_url", "TEXT"),
        ("minutes_played", "INTEGER DEFAULT 0"),
        ("starts", "INTEGER DEFAULT 0"),
        ("subs_in", "INTEGER DEFAULT 0"),
        ("yellow_cards", "INTEGER DEFAULT 0"),
        ("red_cards", "INTEGER DEFAULT 0"),
        ("goals", "INTEGER DEFAULT 0"),
        ("seasons_data", "TEXT"),
        ("is_injured", "INTEGER DEFAULT 0"),
        ("extra_pitch_team_id", "TEXT")
    ]
    for col_name, col_type in new_cols:
        if col_name not in p_cols:
            try:
                cursor.execute(f"ALTER TABLE players ADD COLUMN {col_name} {col_type}")
            except Exception:
                pass
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS matches (
        id TEXT PRIMARY KEY,
        team_id TEXT NOT NULL,
        opponent TEXT NOT NULL,
        date TEXT NOT NULL,
        result_type TEXT NOT NULL,
        home_goals INTEGER NOT NULL,
        away_goals INTEGER NOT NULL,
        is_home INTEGER NOT NULL,
        competition TEXT NOT NULL,
        custom_title TEXT,
        playing_time TEXT DEFAULT '90 Minutes',
        substitute_cadence TEXT DEFAULT '',
        substitution_times TEXT DEFAULT '[]',
        FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
    );
    """)
    
    # Check if columns exist in matches (in case old table exists)
    cursor.execute("PRAGMA table_info(matches)")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if "custom_title" not in existing_cols:
        try:
            cursor.execute("ALTER TABLE matches ADD COLUMN custom_title TEXT")
            cursor.execute("ALTER TABLE matches ADD COLUMN playing_time TEXT DEFAULT '90 Minutes'")
            cursor.execute("ALTER TABLE matches ADD COLUMN substitute_cadence TEXT DEFAULT ''")
            cursor.execute("ALTER TABLE matches ADD COLUMN substitution_times TEXT DEFAULT '[]'")
        except Exception:
            pass

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS lineup_entries (
        id TEXT PRIMARY KEY,
        match_id TEXT NOT NULL,
        player_id TEXT NOT NULL,
        field_position TEXT NOT NULL,
        is_starter INTEGER NOT NULL,
        grid_x REAL NOT NULL,
        grid_y REAL NOT NULL,
        sub_in_minute INTEGER,
        sub_out_minute INTEGER,
        has_yellow_card INTEGER DEFAULT 0,
        FOREIGN KEY(match_id) REFERENCES matches(id) ON DELETE CASCADE,
        FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("PRAGMA table_info(lineup_entries)")
    l_cols = [c[1] for c in cursor.fetchall()]
    if "sub_in_minute" not in l_cols:
        try:
            cursor.execute("ALTER TABLE lineup_entries ADD COLUMN sub_in_minute INTEGER")
        except Exception:
            pass
    if "sub_out_minute" not in l_cols:
        try:
            cursor.execute("ALTER TABLE lineup_entries ADD COLUMN sub_out_minute INTEGER")
        except Exception:
            pass
    if "goals" not in l_cols:
        try:
            cursor.execute("ALTER TABLE lineup_entries ADD COLUMN goals INTEGER DEFAULT 0")
        except Exception:
            pass
    if "has_yellow_card" not in l_cols:
        try:
            cursor.execute("ALTER TABLE lineup_entries ADD COLUMN has_yellow_card INTEGER DEFAULT 0")
        except Exception:
            pass
    if "has_red_card" not in l_cols:
        try:
            cursor.execute("ALTER TABLE lineup_entries ADD COLUMN has_red_card INTEGER DEFAULT 0")
        except Exception:
            pass
    if "card_minute" not in l_cols:
        try:
            cursor.execute("ALTER TABLE lineup_entries ADD COLUMN card_minute INTEGER")
        except Exception:
            pass
    if "card_type" not in l_cols:
        try:
            cursor.execute("ALTER TABLE lineup_entries ADD COLUMN card_type TEXT")
        except Exception:
            pass
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS substitutions (
        id TEXT PRIMARY KEY,
        match_id TEXT NOT NULL,
        player_out_id TEXT NOT NULL,
        player_in_id TEXT NOT NULL,
        minute INTEGER NOT NULL,
        FOREIGN KEY(match_id) REFERENCES matches(id) ON DELETE CASCADE,
        FOREIGN KEY(player_out_id) REFERENCES players(id) ON DELETE CASCADE,
        FOREIGN KEY(player_in_id) REFERENCES players(id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("DELETE FROM players WHERE id LIKE 'p_auto_%'")
    conn.commit()
    conn.close()

# Teams CRUD
def create_team(name: str, season: str = "2026/27 SEASON", club_name: str = "DEPORTIVO DE A CORUÑA FC", team_id: Optional[str] = None) -> Team:
    conn = get_connection()
    cursor = conn.cursor()
    t_id = team_id or str(uuid.uuid4())[:8]
    cursor.execute("INSERT OR REPLACE INTO teams (id, name, season, club_name) VALUES (?, ?, ?, ?)",
                   (t_id, name, season, club_name))
    conn.commit()
    conn.close()
    return Team(id=t_id, name=name, season=season, club_name=club_name)

def get_teams() -> List[Team]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teams")
    rows = cursor.fetchall()
    conn.close()
    return [Team(**dict(row)) for row in rows]

def get_team(team_id: str) -> Optional[Team]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM teams WHERE id = ?", (team_id,))
    row = cursor.fetchone()
    conn.close()
    return Team(**dict(row)) if row else None

# Players CRUD
def create_player(name: str, birthdate: str, detailed_position: str, team_id: str, player_id: Optional[str] = None) -> Player:
    p_id = player_id or str(uuid.uuid4())[:8]
    cat = derive_position_category(detailed_position)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO players (id, name, birthdate, detailed_position, derived_category, team_id)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (p_id, name, birthdate, detailed_position, cat, team_id))
    conn.commit()
    conn.close()
    age = calculate_age(birthdate)
    return Player(id=p_id, name=name, birthdate=birthdate, detailed_position=detailed_position, derived_category=cat, team_id=team_id, age=age)

def update_player(player_id: str, name: str, birthdate: str, detailed_position: str, team_id: str) -> Player:
    cat = derive_position_category(detailed_position)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE players SET name = ?, birthdate = ?, detailed_position = ?, derived_category = ?, team_id = ?
    WHERE id = ?
    """, (name, birthdate, detailed_position, cat, team_id, player_id))
    conn.commit()
    conn.close()
    age = calculate_age(birthdate)
    return Player(id=player_id, name=name, birthdate=birthdate, detailed_position=detailed_position, derived_category=cat, team_id=team_id, age=age)

def delete_player(player_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM players WHERE id = ?", (player_id,))
    conn.commit()
    conn.close()

def update_player_pitch_position(player_id: str, pitch_x: float, pitch_y: float, extra_pitch_team_id: str = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET pitch_x = ?, pitch_y = ?, extra_pitch_team_id = ? WHERE id = ?", (pitch_x, pitch_y, extra_pitch_team_id, player_id))
    conn.commit()
    conn.close()

def toggle_injured_status(player_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT is_injured FROM players WHERE id = ?", (player_id,))
    row = cursor.fetchone()
    if row:
        new_val = 0 if row['is_injured'] == 1 else 1
        cursor.execute("UPDATE players SET is_injured = ? WHERE id = ?", (new_val, player_id))
        conn.commit()
    conn.close()

def update_team_pitch_positions(positions: List[Dict]):
    conn = get_connection()
    cursor = conn.cursor()
    for pos in positions:
        extra = pos.get('extra_pitch_team_id', None)
        cursor.execute("UPDATE players SET pitch_x = ?, pitch_y = ?, extra_pitch_team_id = ? WHERE id = ?", (pos['pitch_x'], pos['pitch_y'], extra, pos['player_id']))
    conn.commit()
    conn.close()

def reset_team_pitch_positions(team_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET pitch_x = NULL, pitch_y = NULL, extra_pitch_team_id = NULL WHERE team_id = ? OR extra_pitch_team_id = ?", (team_id, team_id))
    conn.commit()
    conn.close()

def update_match_lineup_positions(match_id: str, positions: List[Dict]):
    conn = get_connection()
    cursor = conn.cursor()
    for pos in positions:
        cursor.execute("UPDATE lineup_entries SET grid_x = ?, grid_y = ? WHERE match_id = ? AND player_id = ?",
                       (pos['grid_x'], pos['grid_y'], match_id, pos['player_id']))
    conn.commit()
    conn.close()

def get_player_season_26_27_stats(player_id: str) -> Dict:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    SELECT le.*, m.team_id
    FROM lineup_entries le
    JOIN matches m ON le.match_id = m.id
    WHERE le.player_id = ?
    """, (player_id,))
    
    rows = cursor.fetchall()
    conn.close()
    
    tot_mins = 0
    tot_apps = 0
    tot_starts = 0
    tot_subs = 0
    tot_goals = 0
    tot_yellows = 0
    tot_reds = 0
    
    for r in rows:
        d = dict(r)
        is_starter = bool(d.get("is_starter"))
        sub_in = d.get("sub_in_minute")
        sub_out = d.get("sub_out_minute")
        
        m_played = 0
        if is_starter:
            tot_starts += 1
            tot_apps += 1
            if sub_out and sub_out > 0:
                m_played = sub_out
            else:
                m_played = 90
        elif sub_in and sub_in > 0:
            tot_subs += 1
            tot_apps += 1
            if sub_out and sub_out > sub_in:
                m_played = sub_out - sub_in
            else:
                m_played = max(0, 90 - sub_in)
                
        tot_mins += m_played
        tot_goals += d.get("goals", 0) or 0
        if d.get("has_yellow_card"): tot_yellows += 1
        if d.get("has_red_card"): tot_reds += 1
        
    return {
        "minutes_played": tot_mins,
        "starts": tot_apps,
        "subs_in": tot_subs,
        "goals": tot_goals,
        "yellow_cards": tot_yellows,
        "red_cards": tot_reds
    }

def get_players_by_team(team_id: str, include_extra_pitch: bool = False) -> List[Player]:
    conn = get_connection()
    cursor = conn.cursor()
    if include_extra_pitch:
        cursor.execute("SELECT * FROM players WHERE team_id = ? OR extra_pitch_team_id = ?", (team_id, team_id))
    else:
        cursor.execute("SELECT * FROM players WHERE team_id = ?", (team_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d['age'] = calculate_age(d['birthdate'])
        
        # Calculate dynamic 2026-27 season stats from match lineups
        s_stats = get_player_season_26_27_stats(d['id'])
        d['minutes_played'] = s_stats['minutes_played']
        d['starts'] = s_stats['starts']
        d['subs_in'] = s_stats['subs_in']
        d['goals'] = s_stats['goals']
        d['yellow_cards'] = s_stats['yellow_cards']
        d['red_cards'] = s_stats['red_cards']
        
        res.append(Player(**d))
    return res

def get_player(player_id: str) -> Optional[Player]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE id = ?", (player_id,))
    row = cursor.fetchone()
    conn.close()
    if not row: return None
    d = dict(row)
    d['age'] = calculate_age(d['birthdate'])
    
    # Calculate dynamic 2026-27 season stats from match lineups
    s_stats = get_player_season_26_27_stats(d['id'])
    d['minutes_played'] = s_stats['minutes_played']
    d['starts'] = s_stats['starts']
    d['subs_in'] = s_stats['subs_in']
    d['goals'] = s_stats['goals']
    d['yellow_cards'] = s_stats['yellow_cards']
    d['red_cards'] = s_stats['red_cards']
    
    return Player(**d)

def update_player_photo(player_id: str, photo_url: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE players SET photo_url = ? WHERE id = ?", (photo_url, player_id))
    conn.commit()
    conn.close()

def update_player_stats(player_id: str, stats: Dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    UPDATE players SET 
        minutes_played = ?,
        starts = ?,
        subs_in = ?,
        yellow_cards = ?,
        red_cards = ?,
        goals = ?,
        seasons_data = ?
    WHERE id = ?
    """, (
        stats.get("minutes_played", 0),
        stats.get("starts", 0),
        stats.get("subs_in", 0),
        stats.get("yellow_cards", 0),
        stats.get("red_cards", 0),
        stats.get("goals", 0),
        stats.get("seasons_data"),
        player_id
    ))
    conn.commit()
    conn.close()

def get_all_players() -> List[Player]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players")
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d['age'] = calculate_age(d['birthdate'])
        res.append(Player(**d))
    return res

def import_players_from_dataframe(df: pd.DataFrame, team_id: str) -> int:
    count = 0
    for _, row in df.iterrows():
        name = str(row.get('Nombre', row.get('name', ''))).strip()
        if not name:
            continue
        bdate = str(row.get('FechaNacimiento', row.get('birthdate', '2000-01-01'))).strip()
        if len(bdate) < 8 or '-' not in bdate:
            try:
                age_val = int(bdate)
                bdate = f"{2026 - age_val}-01-01"
            except Exception:
                bdate = "2000-01-01"
        pos = str(row.get('Posicion', row.get('detailed_position', row.get('posicion', 'Mediocentro')))).strip()
        create_player(name=name, birthdate=bdate, detailed_position=pos, team_id=team_id)
        count += 1
    return count

# Matches & Lineups CRUD
import json

def initialize_default_match_lineup(match_id: str, team_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM players WHERE team_id = ?", (team_id,))
    rows = cursor.fetchall()
    if not rows:
        conn.close()
        return
        
    players = [dict(r) for r in rows]
    
    # 4-3-3 Formation slots
    slots = [
        {"role": "GK", "pos": ["portero", "guardameta", "gk"], "grid_x": 0.50, "grid_y": 0.89},
        {"role": "LB", "pos": ["lateral izquierdo", "izq", "lb"], "grid_x": 0.20, "grid_y": 0.73},
        {"role": "LCB", "pos": ["central", "defensa", "cb"], "grid_x": 0.40, "grid_y": 0.77},
        {"role": "RCB", "pos": ["central", "defensa", "cb"], "grid_x": 0.60, "grid_y": 0.77},
        {"role": "RB", "pos": ["lateral derecho", "dcho", "rb"], "grid_x": 0.80, "grid_y": 0.73},
        {"role": "DM", "pos": ["pivote", "defensivo", "dm"], "grid_x": 0.50, "grid_y": 0.60},
        {"role": "LCM", "pos": ["mediocentro", "interior", "cm"], "grid_x": 0.38, "grid_y": 0.48},
        {"role": "RCM", "pos": ["mediocentro", "interior", "ofensivo", "cm"], "grid_x": 0.62, "grid_y": 0.48},
        {"role": "LW", "pos": ["extremo izquierdo", "extremo", "lw"], "grid_x": 0.20, "grid_y": 0.28},
        {"role": "ST", "pos": ["delantero", "punta", "st", "cf"], "grid_x": 0.50, "grid_y": 0.18},
        {"role": "RW", "pos": ["extremo derecho", "extremo", "rw"], "grid_x": 0.80, "grid_y": 0.28},
    ]
    
    assigned_ids = set()
    starters = []
    
    for slot in slots:
        chosen = None
        for p in players:
            if p['id'] in assigned_ids:
                continue
            pos_low = p.get('detailed_position', '').lower()
            if any(k in pos_low for k in slot['pos']):
                chosen = p
                break
        if not chosen:
            # Fallback to any unassigned player
            for p in players:
                if p['id'] not in assigned_ids:
                    chosen = p
                    break
        if chosen:
            assigned_ids.add(chosen['id'])
            starters.append({
                'player_id': chosen['id'],
                'field_position': slot['role'],
                'grid_x': slot['grid_x'],
                'grid_y': slot['grid_y']
            })
            
    substitutes = [{'player_id': p['id']} for p in players if p['id'] not in assigned_ids]
    
    # Save lineup
    for s in starters:
        l_id = str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO lineup_entries (id, match_id, player_id, field_position, is_starter, grid_x, grid_y)
        VALUES (?, ?, ?, ?, 1, ?, ?)
        """, (l_id, match_id, s['player_id'], s['field_position'], s['grid_x'], s['grid_y']))
        
    for sub in substitutes:
        l_id = str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO lineup_entries (id, match_id, player_id, field_position, is_starter, grid_x, grid_y)
        VALUES (?, ?, ?, 'SUB', 0, 0.0, 0.0)
        """, (l_id, match_id, sub['player_id']))
        
    conn.commit()
    conn.close()

def create_match(team_id: str, opponent: str, date: str, result_type: str, home_goals: int, away_goals: int, is_home: bool, competition: str, match_id: Optional[str] = None, custom_title: Optional[str] = None, playing_time: str = "90 Minutes", substitute_cadence: str = "", substitution_times: Optional[List[str]] = None) -> Match:
    m_id = match_id or str(uuid.uuid4())[:8]
    sub_times_json = json.dumps(substitution_times or [])
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO matches (id, team_id, opponent, date, result_type, home_goals, away_goals, is_home, competition, custom_title, playing_time, substitute_cadence, substitution_times)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (m_id, team_id, opponent, date, result_type, home_goals, away_goals, 1 if is_home else 0, competition, custom_title, playing_time, substitute_cadence, sub_times_json))
    conn.commit()
    conn.close()
    
    # Auto-initialize starting 11 and substitutes for the match
    initialize_default_match_lineup(m_id, team_id)
    
    return Match(id=m_id, team_id=team_id, opponent=opponent, date=date, result_type=result_type, home_goals=home_goals, away_goals=away_goals, is_home=is_home, competition=competition, custom_title=custom_title, playing_time=playing_time, substitute_cadence=substitute_cadence, substitution_times=substitution_times or [])

def get_matches_by_team(team_id: str) -> List[Match]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE team_id = ?", (team_id,))
    rows = cursor.fetchall()
    conn.close()
    res = []
    for r in rows:
        d = dict(r)
        d['is_home'] = bool(d['is_home'])
        if 'substitution_times' in d and isinstance(d['substitution_times'], str):
            try:
                d['substitution_times'] = json.loads(d['substitution_times'])
            except Exception:
                d['substitution_times'] = []
        else:
            d['substitution_times'] = []
        res.append(Match(**d))
    return res

def save_lineup_and_subs(match_id: str, starters: List[Dict], substitutes: List[Dict], subs_events: List[Dict]):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM substitutions WHERE match_id = ?", (match_id,))
    cursor.execute("DELETE FROM lineup_entries WHERE match_id = ?", (match_id,))
    
    for s in starters:
        l_id = str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO lineup_entries (id, match_id, player_id, field_position, is_starter, grid_x, grid_y, sub_in_minute, sub_out_minute, has_yellow_card, has_red_card, card_minute, card_type, goals)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            l_id, match_id, s['player_id'], s.get('field_position', 'POS'), 1,
            float(s.get('grid_x', 0.5)), float(s.get('grid_y', 0.5)),
            s.get('sub_in_minute'), s.get('sub_out_minute'),
            1 if s.get('has_yellow_card') else 0,
            1 if s.get('has_red_card') else 0,
            s.get('card_minute'),
            s.get('card_type'),
            int(s.get('goals', 0))
        ))
        
    for sub in substitutes:
        l_id = str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO lineup_entries (id, match_id, player_id, field_position, is_starter, grid_x, grid_y, sub_in_minute, sub_out_minute, has_yellow_card, has_red_card, card_minute, card_type, goals)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            l_id, match_id, sub['player_id'], sub.get('field_position', 'SUB'), 0, 0.0, 0.0,
            sub.get('sub_in_minute'), sub.get('sub_out_minute'),
            1 if sub.get('has_yellow_card') else 0,
            1 if sub.get('has_red_card') else 0,
            sub.get('card_minute'),
            sub.get('card_type'),
            int(sub.get('goals', 0))
        ))
        
    for sub_ev in subs_events:
        se_id = str(uuid.uuid4())[:8]
        cursor.execute("""
        INSERT INTO substitutions (id, match_id, player_out_id, player_in_id, minute)
        VALUES (?, ?, ?, ?, ?)
        """, (se_id, match_id, sub_ev['player_out_id'], sub_ev['player_in_id'], int(sub_ev['minute'])))
        
    conn.commit()
    conn.close()

def update_match_details(match_id: str, data: Dict) -> Optional[Match]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None
        
    d = dict(row)
    for k, v in data.items():
        if k in ['opponent', 'date', 'result_type', 'home_goals', 'away_goals', 'competition', 'custom_title', 'playing_time', 'substitute_cadence']:
            d[k] = v
        elif k == 'is_home':
            d['is_home'] = 1 if v else 0

    cursor.execute("""
    UPDATE matches
    SET opponent = ?, date = ?, result_type = ?, home_goals = ?, away_goals = ?, is_home = ?, competition = ?, custom_title = ?, playing_time = ?, substitute_cadence = ?
    WHERE id = ?
    """, (
        d['opponent'], d['date'], d['result_type'], d['home_goals'], d['away_goals'],
        1 if d['is_home'] else 0, d['competition'], d.get('custom_title'),
        d.get('playing_time', '90 Minutes'), d.get('substitute_cadence', ''), match_id
    ))
    conn.commit()
    conn.close()
    
    d['is_home'] = bool(d['is_home'])
    d['substitution_times'] = json.loads(d['substitution_times']) if isinstance(d.get('substitution_times'), str) else []
    return Match(**d)

def get_match_full_data(match_id: str) -> Optional[Dict]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM matches WHERE id = ?", (match_id,))
    m_row = cursor.fetchone()
    if not m_row:
        conn.close()
        return None
    
    m_dict = dict(m_row)
    m_dict['is_home'] = bool(m_dict['is_home'])
    if 'substitution_times' in m_dict and isinstance(m_dict['substitution_times'], str):
        try:
            m_dict['substitution_times'] = json.loads(m_dict['substitution_times'])
        except Exception:
            m_dict['substitution_times'] = []
    else:
        m_dict['substitution_times'] = []
    match_obj = Match(**m_dict)
    
    team = get_team(match_obj.team_id)
    
    cursor.execute("SELECT * FROM lineup_entries WHERE match_id = ?", (match_id,))
    l_rows = cursor.fetchall()
    
    starters = []
    substitutes = []
    for lr in l_rows:
        ld = dict(lr)
        ld['is_starter'] = bool(ld['is_starter'])
        ld['has_yellow_card'] = bool(ld.get('has_yellow_card', 0))
        ld['has_red_card'] = bool(ld.get('has_red_card', 0))
        entry = LineupEntry(**ld)
        if entry.is_starter:
            starters.append(entry)
        else:
            substitutes.append(entry)
            
    cursor.execute("SELECT * FROM substitutions WHERE match_id = ? ORDER BY minute ASC", (match_id,))
    sub_rows = cursor.fetchall()
    substitutions = [SubstitutionEvent(**dict(sr)) for sr in sub_rows]
    
    # Map all players in database (covers players playing across squads)
    all_players = get_all_players()
    players_map = {p.id: p for p in all_players}
    
    conn.close()
    return {
        "match": match_obj,
        "team": team,
        "starters": starters,
        "substitutes": substitutes,
        "substitutions": substitutions,
        "players_map": players_map
    }

def delete_match(match_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM substitutions WHERE match_id = ?", (match_id,))
    cursor.execute("DELETE FROM lineup_entries WHERE match_id = ?", (match_id,))
    cursor.execute("DELETE FROM matches WHERE id = ?", (match_id,))
    conn.commit()
    conn.close()



