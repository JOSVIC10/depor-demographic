import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from backend import database as db

def seed():
    db.init_db()
    
    # 1. Create Teams
    depor = db.create_team(name="DEPORTIVO A CORUÑA", season="2026/27 SEASON", club_name="DEPORTIVO DE A CORUÑA FC", team_id="depor")
    fabril = db.create_team(name="FABRIL", season="2026/27 SEASON", club_name="DEPORTIVO DE A CORUÑA FC", team_id="fabril")
    penafiel = db.create_team(name="PEÑAFIEL", season="2026/27 SEASON", club_name="DEPORTIVO A CORUÑA FC", team_id="penafiel")
    
    # Clear existing players & matches for clean seed
    conn = db.get_connection()
    c = conn.cursor()
    c.execute("DELETE FROM players")
    c.execute("DELETE FROM matches")
    c.execute("DELETE FROM lineup_entries")
    c.execute("DELETE FROM substitutions")
    conn.commit()
    conn.close()

    # 2. Deportivo Squad (30 players)
    depor_players_data = [
        # Porteros (4)
        ("Germán Parreño", "1993-02-16", "Portero", "p_depor_german"),
        ("Leo Román", "2000-07-06", "Portero", "p_depor_leoroman"),
        ("Álvaro Ferllo", "1998-07-26", "Portero", "p_depor_ferllo"),
        ("Eric Puerto", "2002-10-28", "Portero", "p_depor_puerto"),
        
        # Centrales (4)
        ("Arnau Comas", "2000-04-11", "Defensa central", "p_depor_comas"),
        ("Dani Barcia", "2003-01-19", "Defensa central", "p_depor_barcia"),
        ("Lucas Noubi", "2005-01-15", "Defensa central", "p_depor_noubi"),
        ("Bright Ede", "2007-02-14", "Defensa central", "p_depor_ede"),
        
        # Laterales (5)
        ("Ximo Navarro", "1990-01-23", "Lateral derecho", "p_depor_ximo"),
        ("Giacomo Quagliata", "2000-02-19", "Lateral izquierdo", "p_depor_quagliata"),
        ("Miguel Loureiro", "1996-12-04", "Lateral derecho", "p_depor_loureiro"),
        ("Angeliño", "1997-01-04", "Lateral izquierdo", "p_depor_angelino"),
        ("Adrià Altimira", "2001-03-28", "Lateral derecho", "p_depor_altimira"),
        
        # Mediocentros (10)
        ("Diego Villares", "1996-06-17", "Mediocentro", "p_depor_villares"),
        ("José Ángel Jurado", "1992-03-07", "Pivote", "p_depor_joseangel"),
        ("Riki Rodríguez", "1997-09-25", "Mediocentro", "p_depor_riki"),
        ("Lorenzo Amatucci", "2004-02-05", "Mediocentro", "p_depor_amatucci"),
        ("Charlie Patiño", "2003-10-17", "Mediocentro", "p_depor_patino"),
        ("Mario Soriano", "2002-04-22", "Mediocentro", "p_depor_soriano"),
        ("Jairo Noriega", "2003-09-02", "Mediocentro", "p_depor_jairo"),
        ("Noé Carrillo", "2007-05-18", "Mediocentro", "p_depor_carrillo"),
        ("Teun Gijselhart", "2005-05-28", "Mediocentro", "p_depor_gijselhart"),
        ("Jonathan Asp Jensen", "2006-01-14", "Mediocentro", "p_depor_aspjensen"),
        
        # Int/Extremos (3)
        ("Yeremay Hernández", "2002-12-10", "Extremo", "p_depor_yeremay"),
        ("Luismi Cruz", "2001-05-23", "Extremo", "p_depor_luismicruz"),
        ("David Mella", "2005-05-23", "Extremo", "p_depor_mella"),
        
        # Delanteros (4)
        ("Pierre-Emerick Aubameyang", "1989-06-18", "Delantero centro", "p_depor_auba"),
        ("Zakaria Eddahchouri", "2000-05-11", "Delantero centro", "p_depor_eddahchouri"),
        ("Bil Nsongo", "2004-11-25", "Delantero centro", "p_depor_bilnsongo"),
        ("Kevin Sánchez", "2005-02-20", "Delantero centro", "p_depor_kevinsanchez"),
    ]
    
    depor_map = {}
    for name, bdate, pos, p_id in depor_players_data:
        p = db.create_player(name=name, birthdate=bdate, detailed_position=pos, team_id="depor", player_id=p_id)
        depor_map[p_id] = p

    # 3. Fabril Squad (24 players)
    fabril_players_data = [
        # Porteros (2)
        ("Hugo Rios", "2003-05-10", "Portero", "p_fabril_hugorios"),
        ("Álex Marqués", "2005-12-28", "Portero", "p_fabril_alexmarques"),
        
        # Centrales (4)
        ("Damián Canedo", "2003-08-25", "Defensa central", "p_fabril_canedo"),
        ("Malick Ndiaye", "2006-10-15", "Defensa central", "p_fabril_malick"),
        ("David Vergara", "2007-03-15", "Defensa central", "p_fabril_vergara"),
        ("Samu Fernández", "2007-01-10", "Defensa central", "p_fabril_samu"),
        
        # Laterales (4)
        ("Quique Teijo", "2004-07-18", "Lateral derecho", "p_fabril_teijo"),
        ("Iker Vidal", "2004-12-01", "Lateral izquierdo", "p_fabril_ikervidal"),
        ("Pablo García", "2007-08-14", "Lateral izquierdo", "p_fabril_pablogarcia"),
        ("Alvaro Mardones", "2005-09-20", "Lateral", "p_fabril_mardones"),
        
        # Mediocentros (6)
        ("Koke San José", "2003-11-12", "Mediocentro", "p_fabril_sanjose"),
        ("Dani Estévez", "2006-02-15", "Mediocentro", "p_fabril_estevez"),
        ("Papa Samsou Niang", "2006-01-20", "Mediocentro", "p_fabril_niang"),
        ("Manu Ferreiro", "2006-09-05", "Mediocentro", "p_fabril_ferreiro"),
        ("Noé Carrillo", "2007-05-18", "Mediocentro", "p_fabril_carrillo"),
        ("Luisao Macías", "2005-04-10", "Mediocentro", "p_fabril_luisao"),
        
        # Int/Extremos (5)
        ("Pablo Cortés", "2004-01-15", "Extremo", "p_fabril_cortes"),
        ("Rubén López", "2004-08-26", "Extremo", "p_fabril_rubenlopez"),
        ("Justino Barbosa", "2005-03-08", "Extremo", "p_fabril_justino"),
        ("Adrián Guerrero", "2006-04-12", "Extremo", "p_fabril_guerrero"),
        ("Héctor Areosa", "2006-02-10", "Extremo", "p_fabril_areosa"),
        
        # Delanteros (3)
        ("Martín Ochoa", "2004-11-20", "Delantero centro", "p_fabril_ochoa"),
        ("Rodrigue Dipanda", "2006-06-18", "Delantero centro", "p_fabril_dipanda"),
        ("David Domínguez", "2005-04-15", "Delantero centro", "p_fabril_dominguez"),
    ]
    
    fabril_map = {}
    for name, bdate, pos, p_id in fabril_players_data:
        p = db.create_player(name=name, birthdate=bdate, detailed_position=pos, team_id="fabril", player_id=p_id)
        fabril_map[p_id] = p

    # 4. Peñafiel Squad (27 players)
    penafiel_players_data = [
        # Porteros (3)
        ("Miguel Oliveira", "1994-05-25", "Portero", "p_pena_migueloliveira"),
        ("Joan Femenías", "1996-08-19", "Portero", "p_pena_femenias"),
        ("Alexéi Rojas", "2005-09-28", "Portero", "p_pena_alexei"),
        
        # Centrales (5)
        ("Jaime Sánchez", "1995-03-11", "Defensa central", "p_pena_jaimesanchez"),
        ("João Miguel", "1993-09-14", "Defensa central", "p_pena_joaomiguel"),
        ("Cláudio Silva", "2000-06-29", "Defensa central", "p_pena_claudiosilva"),
        ("Adrián Pica", "2002-04-25", "Defensa central", "p_pena_pica"),
        ("Meireles Injai", "2003-05-10", "Defensa central", "p_pena_injai"),
        
        # Laterales (4)
        ("Iano Simão", "1999-02-02", "Lateral izquierdo", "p_pena_simao"),
        ("Teddy Alloh", "2002-01-23", "Lateral", "p_pena_alloh"),
        ("Martim Alberto", "2004-04-20", "Lateral derecho", "p_pena_martim"),
        ("Gonçalo Negrão", "2003-01-17", "Lateral derecho", "p_pena_negrao"),
        
        # Mediocentros (6)
        ("Pedro Sá", "1993-12-01", "Mediocentro", "p_pena_pedrosa"),
        ("Neto", "2000-03-27", "Mediocentro", "p_pena_neto"),
        ("Àlex Carbonell", "1997-09-15", "Mediocentro", "p_pena_carbonell"),
        ("Carlinhos Augusto", "2004-01-10", "Mediocentro", "p_pena_carlinhos"),
        ("João Pinto", "2002-08-31", "Mediocentro", "p_pena_joaopinto"),
        ("Juanda Fuentes", "2003-05-19", "Mediocentro", "p_pena_juanda"),
        
        # Int/Extremos (5)
        ("Davo", "1994-12-18", "Extremo derecho", "p_pena_davo"),
        ("Maddi", "1998-10-21", "Extremo", "p_pena_maddi"),
        ("Jota", "2002-09-06", "Extremo", "p_pena_jota"),
        ("Nuno Martins", "2003-02-05", "Extremo", "p_pena_nunomartins"),
        ("João Leal", "2005-10-12", "Extremo", "p_pena_joaoleal"),
        
        # Delanteros (4)
        ("Raúl Alcaina", "2000-07-19", "Delantero centro", "p_pena_alcaina"),
        ("Ricardo Schutte", "1998-05-21", "Delantero centro", "p_pena_schutte"),
        ("Joseph Séry", "2000-08-05", "Delantero centro", "p_pena_sery"),
        ("Max Svensson", "2001-11-08", "Delantero centro", "p_pena_svensson"),
    ]
    
    penafiel_map = {}
    for name, bdate, pos, p_id in penafiel_players_data:
        p = db.create_player(name=name, birthdate=bdate, detailed_position=pos, team_id="penafiel", player_id=p_id)
        penafiel_map[p_id] = p

    # 5. Create Extra players seen in matches but not in main squads
    extra_players = [
        ("Xabi Campos", "2006-03-12", "Lateral izquierdo", "depor", "p_extra_xabicampos"),
        ("Rodri Leiva", "2004-06-18", "Portero", "fabril", "p_extra_rodrileiva"),
        ("Hatim", "2005-02-22", "Defensa central", "fabril", "p_extra_hatim"),
        ("Leandro", "2005-08-11", "Centrocampista", "fabril", "p_extra_leandro"),
        ("M. Valeiro", "2006-07-19", "Centrocampista", "fabril", "p_extra_valeiro"),
        ("Guille P.", "2005-05-15", "Lateral derecho", "fabril", "p_extra_guillep"),
        ("Lucas Castro", "2006-09-09", "Centrocampista", "fabril", "p_extra_lucascastro"),
        ("Íker Gil", "2005-01-30", "Delantero centro", "fabril", "p_extra_ikergil"),
        ("J. Vega", "2006-04-18", "Centrocampista", "fabril", "p_extra_jvega"),
        ("David Fernández", "2006-03-01", "Defensa central", "fabril", "p_extra_davidfdez"),
        ("Íker Fernández", "2006-11-20", "Centrocampista", "fabril", "p_extra_ikerfdez"),
        ("Ibra Kébé", "2000-08-01", "Mediocentro", "penafiel", "p_extra_kebe"),
        ("Reko", "1999-06-21", "Mediocentro", "penafiel", "p_extra_reko"),
        ("Bruno Pereira", "2001-04-14", "Lateral izquierdo", "penafiel", "p_extra_brunopereira"),
        ("Zé Leite", "2001-08-17", "Extremo derecho", "penafiel", "p_extra_zeleite"),
        ("Nuniho", "2002-05-05", "Extremo", "penafiel", "p_extra_nuniho"),
        ("André Schutte", "2000-01-01", "Extremo", "penafiel", "p_extra_andreschutte"),
        ("Douglas Borel", "2002-03-30", "Lateral", "penafiel", "p_extra_douglasborel"),
        ("Mairlon Ramon", "2000-01-01", "Jugador", "penafiel", "p_extra_mairlon"),
        ("D. Oliveira", "2000-01-01", "Jugador", "penafiel", "p_extra_doliveira"),
        ("Juanda", "2000-01-01", "Jugador", "penafiel", "p_extra_juanda2"),
        ("Papa", "2006-01-20", "Mediocentro", "fabril", "p_extra_papa"),
        ("David", "2000-01-01", "Jugador", "fabril", "p_extra_david"),
        ("Rodrigo", "2000-01-01", "Jugador", "fabril", "p_extra_rodrigo"),
        ("Héctor", "2000-01-01", "Jugador", "fabril", "p_extra_hector"),
        ("Justino", "2000-01-01", "Jugador", "fabril", "p_extra_justino2"),
        ("Álvaro", "2000-01-01", "Jugador", "fabril", "p_extra_alvaro"),
        ("Pablo G.", "2000-01-01", "Jugador", "fabril", "p_extra_pablog"),
        ("David D.", "2000-01-01", "Jugador", "fabril", "p_extra_davidd"),
        ("Álvaro Fraga", "2000-01-01", "Jugador", "fabril", "p_extra_alvarofraga"),
    ]
    for name, bdate, pos, t_id, p_id in extra_players:
        db.create_player(name=name, birthdate=bdate, detailed_position=pos, team_id=t_id, player_id=p_id)

    # 6. Matches
    matches_data = [
        {
            "match_id": "m1_compostela", "team_id": "depor", "opponent": "COMPOSTELA", "date": "2026-08-01",
            "result_type": "WIN", "home_goals": 0, "away_goals": 4, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "COMPOSTELA v DEPORTIVO (WIN 0-4)",
            "playing_time": "92 Minutes", "substitute_cadence": "11 | 2 |"
        },
        {
            "match_id": "m2_oviedo", "team_id": "depor", "opponent": "OVIEDO", "date": "2026-08-03",
            "result_type": "DRAW", "home_goals": 0, "away_goals": 0, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "OVIEDO v DEPORTIVO (DRAW 0-0)",
            "playing_time": "90 Minutes", "substitute_cadence": "1 | 7 | 2 |"
        },
        {
            "match_id": "m3_lugo", "team_id": "depor", "opponent": "LUGO", "date": "2026-08-05",
            "result_type": "WIN", "home_goals": 1, "away_goals": 0, "is_home": True,
            "competition": "FRIENDLY", "custom_title": "DEPORTIVO v LUGO (WIN 1-0)",
            "playing_time": "90 Minutes", "substitute_cadence": "4 | 6 | 1 |"
        },
        {
            "match_id": "m4_stpauli", "team_id": "depor", "opponent": "ST. PAULI", "date": "2026-08-07",
            "result_type": "DRAW", "home_goals": 2, "away_goals": 2, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "ST. PAULI v DEPORTIVO (DRAW 2-2)",
            "playing_time": "120 Minutes", "substitute_cadence": "8 | 2 | 1 |"
        },
        {
            "match_id": "m5_fiorentina", "team_id": "depor", "opponent": "FIORENTINA", "date": "2026-08-09",
            "result_type": "DRAW", "home_goals": 1, "away_goals": 1, "is_home": True,
            "competition": "FRIENDLY", "custom_title": "FIORENTINA v DEPORTIVO (DRAW 1-1)",
            "playing_time": "90 Minutes", "substitute_cadence": "1 | 1 | 8 |"
        },
        {
            "match_id": "m6_genoa", "team_id": "depor", "opponent": "GENOA", "date": "2026-08-11",
            "result_type": "WIN", "home_goals": 0, "away_goals": 1, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "GENOA v DEPORTIVO (WIN 0-1)",
            "playing_time": "90 Minutes", "substitute_cadence": "2 | 2 | 7 |"
        },
        {
            "match_id": "m7_pontevedra", "team_id": "fabril", "opponent": "PONTEVEDRA", "date": "2026-08-01",
            "result_type": "LOSE", "home_goals": 2, "away_goals": 1, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "PONTEVEDRA v FABRIL (LOSE 2-1)",
            "playing_time": "90 Minutes", "substitute_cadence": "11 |"
        },
        {
            "match_id": "m8_lugo_fab", "team_id": "fabril", "opponent": "LUGO", "date": "2026-08-03",
            "result_type": "LOSE", "home_goals": 2, "away_goals": 0, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "LUGO v FABRIL (LOSE 2-0)",
            "playing_time": "90 Minutes", "substitute_cadence": ""
        },
        {
            "match_id": "m9_castilla", "team_id": "fabril", "opponent": "CASTILLA", "date": "2026-08-05",
            "result_type": "LOSE", "home_goals": 0, "away_goals": 1, "is_home": True,
            "competition": "FRIENDLY", "custom_title": "FABRIL v CASTILLA (LOSE 0-1)",
            "playing_time": "90 Minutes", "substitute_cadence": "3 | 7 |"
        },
        {
            "match_id": "m10_astorga", "team_id": "fabril", "opponent": "ATL. ASTORGA", "date": "2026-08-07",
            "result_type": "DRAW", "home_goals": 2, "away_goals": 2, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "ATL. ASTORGA v FABRIL (DRAW 2-2)",
            "playing_time": "90 Minutes", "substitute_cadence": "3 | 3 | 5"
        },
        {
            "match_id": "m11_guimaraes", "team_id": "penafiel", "opponent": "VITORIA GUIMARAES", "date": "2026-08-01",
            "result_type": "LOSE", "home_goals": 5, "away_goals": 0, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "VITORIA GUIMARAES v PEÑAFIEL (LOSE 5-0)",
            "playing_time": "90 Minutes", "substitute_cadence": ""
        },
        {
            "match_id": "m12_famalicao", "team_id": "penafiel", "opponent": "FAMALICÃO", "date": "2026-08-03",
            "result_type": "DRAW", "home_goals": 0, "away_goals": 0, "is_home": False,
            "competition": "FRIENDLY", "custom_title": "FAMALICÃO v PEÑAFIEL (DRAW 0-0)",
            "playing_time": "90 Minutes", "substitute_cadence": ""
        },
        {
            "match_id": "m13_leganes", "team_id": "penafiel", "opponent": "LEGANÉS", "date": "2026-08-05",
            "result_type": "LOSE", "home_goals": 0, "away_goals": 2, "is_home": True,
            "competition": "FRIENDLY", "custom_title": "PEÑAFIEL v LEGANÉS (LOSE 0-2)",
            "playing_time": "90 Minutes", "substitute_cadence": ""
        },
        {
            "match_id": "m14_gilvicente", "team_id": "penafiel", "opponent": "GIL VICENTE", "date": "2026-08-07",
            "result_type": "LOSE", "home_goals": 0, "away_goals": 2, "is_home": True,
            "competition": "FRIENDLY", "custom_title": "PEÑAFIEL v GIL VICENTE (LOSE 0-2)",
            "playing_time": "90 Minutes", "substitute_cadence": ""
        },
        {
            "match_id": "m15_braga2", "team_id": "penafiel", "opponent": "SPORTING BRAGA II", "date": "2026-08-09",
            "result_type": "LOSE", "home_goals": 0, "away_goals": 2, "is_home": True,
            "competition": "FRIENDLY", "custom_title": "PEÑAFIEL v SPORTING BRAGA II (LOSE 0-2)",
            "playing_time": "90 Minutes", "substitute_cadence": ""
        },
        {
            "match_id": "m16_portimonense", "team_id": "penafiel", "opponent": "PORTIMONENSE", "date": "2026-08-11",
            "result_type": "LOSE", "home_goals": 0, "away_goals": 1, "is_home": True,
            "competition": "FRIENDLY", "custom_title": "PEÑAFIEL v PORTIMONENSE (LOSE 0-1)",
            "playing_time": "90 Minutes", "substitute_cadence": "2 | 1 | 2"
        },
    ]
    
    import uuid
    from seed_matches_data import matches_lineups_data
    
    all_players = db.get_all_players()
    name_to_id = {p.name.lower(): p.id for p in all_players}
    
    def get_or_create_player_id(name: str, team_id: str):
        low_name = name.lower().strip()
        if low_name in name_to_id:
            return name_to_id[low_name]
        for p in all_players:
            if low_name in p.name.lower() or p.name.lower() in low_name:
                return p.id
        p_id = "p_auto_" + str(uuid.uuid4())[:8]
        db.create_player(name=name, birthdate="2000-01-01", detailed_position="Jugador", team_id=team_id, player_id=p_id)
        all_players.append(type('obj', (object,), {'name': name, 'id': p_id}))
        name_to_id[low_name] = p_id
        return p_id

    for md in matches_data:
        m = db.create_match(**md)
        m_id = m.id
        team_id = m.team_id
        if m_id in matches_lineups_data:
            lineup_info = matches_lineups_data[m_id]
            starters = []
            for st in lineup_info["starters"]:
                p_id = get_or_create_player_id(st["name"], team_id)
                starters.append({
                    "player_id": p_id,
                    "field_position": st["pos"],
                    "grid_x": st["x"],
                    "grid_y": st["y"]
                })
            subs = []
            for sub_name in lineup_info["subs"]:
                p_id = get_or_create_player_id(sub_name, team_id)
                subs.append({"player_id": p_id})
                
            db.save_lineup_and_subs(m_id, starters, subs, [])

    print("All 3 teams, players, and exactly 16 matches seeded successfully.")

if __name__ == "__main__":
    seed()
