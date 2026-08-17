from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Response, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import tempfile
import pandas as pd
from typing import List, Dict, Optional, Tuple
from backend.models import Player, PlayerCreate, Team, Match, MatchCreate, LineupEntry, SubstitutionEvent
from backend import database as db
from backend.layout_engine import LayoutEngine, PitchSpec
from backend.pptx_generator import PPTXGenerator
from backend.pdf_converter import convert_pptx_to_pdf

app = FastAPI(title="Depor Demographic & Match Report Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"]
)

# Initialize Database
db.init_db()

# Mount frontend static files
frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

@app.get("/")
def read_root():
    index_path = os.path.join(frontend_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "Depor Demographic API running"}

# Teams API
@app.get("/api/teams", response_model=List[Team])
def list_teams():
    return db.get_teams()

@app.post("/api/teams", response_model=Team)
def create_team(team: Team):
    return db.create_team(team.name, team.season, team.club_name, team.id)

# Players API
@app.get("/api/teams/{team_id}/players", response_model=List[Player])
def list_players(team_id: str):
    return db.get_players_by_team(team_id)

@app.post("/api/teams/{team_id}/players", response_model=Player)
def add_player(team_id: str, player: PlayerCreate):
    return db.create_player(player.name, player.birthdate, player.detailed_position, team_id)

@app.put("/api/players/{player_id}", response_model=Player)
def update_player(player_id: str, player: PlayerCreate):
    return db.update_player(player_id, player.name, player.birthdate, player.detailed_position, player.team_id)

@app.delete("/api/players/{player_id}")
def delete_player(player_id: str):
    db.delete_player(player_id)
    return {"status": "ok"}

@app.post("/api/players/{player_id}/injured")
def toggle_player_injured(player_id: str):
    db.toggle_injured_status(player_id)
    return {"status": "ok"}

@app.get("/api/players/all")
def get_all_players_global():
    return db.get_all_players()

@app.put("/api/players/{player_id}/pitch-position")
def update_player_pitch_position(player_id: str, pitch_x: float = Body(...), pitch_y: float = Body(...), extra_pitch_team_id: str = Body(None)):
    db.update_player_pitch_position(player_id, pitch_x, pitch_y, extra_pitch_team_id)
    return {"status": "ok"}

@app.post("/api/players/{player_id}/photo")
async def upload_player_photo(player_id: str, file: UploadFile = File(...)):
    p = db.get_player(player_id)
    if not p:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
        
    photos_dir = os.path.join(frontend_dir, "photos")
    os.makedirs(photos_dir, exist_ok=True)
    
    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"{player_id}{ext}"
    filepath = os.path.join(photos_dir, filename)
    
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    photo_url = f"/static/photos/{filename}"
    db.update_player_photo(player_id, photo_url)
    return {"success": True, "photo_url": photo_url}

@app.put("/api/players/{player_id}/stats")
def update_player_stats(player_id: str, stats: Dict):
    p = db.get_player(player_id)
    if not p:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    db.update_player_stats(player_id, stats)
    return {"success": True}

@app.get("/api/admin/import-all-teams-passport")
def import_all_teams_passport():
    import zipfile, re
    from xml.etree import ElementTree as ET

    pptx_path = r"C:\Users\Jose Vicente\Downloads\Pasaporte Jugador.pptx"
    if not os.path.exists(pptx_path):
        return {"success": False, "error": f"Archivo no encontrado en {pptx_path}"}

    photos_dir = os.path.join(frontend_dir, "photos")
    os.makedirs(photos_dir, exist_ok=True)

    slide_map = {
        # Depor
        3: ("depor", "p_depor_leoroman"),
        4: ("depor", "p_depor_ferllo"),
        5: ("depor", "p_depor_german"),
        6: ("depor", "p_depor_puerto"),
        7: ("depor", "p_depor_noubi"),
        8: ("depor", "p_depor_barcia"),
        9: ("depor", "p_depor_ede"),
        10: ("depor", "p_depor_comas"),
        11: ("depor", "p_depor_quagliata"),
        12: ("depor", "p_depor_angelino"),
        13: ("depor", "p_depor_altimira"),
        14: ("depor", "p_depor_loureiro"),
        15: ("depor", "p_depor_ximo"),
        16: ("depor", "p_depor_amatucci"),
        17: ("depor", "p_depor_riki"),
        18: ("depor", "p_depor_villares"),
        19: ("depor", "p_depor_carrillo"),
        20: ("depor", "p_depor_gijselhart"),
        21: ("depor", "p_depor_patino"),
        22: ("depor", "p_depor_joseangel"),
        23: ("depor", "p_depor_soriano"),
        24: ("depor", "p_depor_aspjensen"),
        25: ("depor", "p_depor_jairo"),
        26: ("depor", "p_depor_yeremay"),
        27: ("depor", "p_depor_mella"),
        28: ("depor", "p_depor_luismicruz"),
        29: ("depor", "p_depor_bilnsongo"),
        30: ("depor", "p_depor_auba"),
        31: ("depor", "p_depor_eddahchouri"),
        32: ("depor", "p_depor_kevinsanchez"),

        # Penafiel
        33: ("penafiel", "p_pena_femenias"),
        34: ("penafiel", "p_pena_alexei"),
        35: ("penafiel", "p_pena_migueloliveira"),
        36: ("penafiel", "p_pena_pica"),
        37: ("penafiel", "p_pena_claudiosilva"),
        38: ("penafiel", "p_pena_jaimesanchez"),
        39: ("penafiel", "p_pena_joaomiguel"),
        40: ("penafiel", "p_pena_injai"),
        41: ("penafiel", "p_pena_simao"),
        42: ("penafiel", "p_pena_alloh"),
        43: ("penafiel", "p_pena_martim"),
        44: ("penafiel", "p_pena_negrao"),
        45: ("penafiel", "p_extra_douglasborel"),
        46: ("penafiel", "p_pena_pedrosa"),
        47: ("penafiel", "p_pena_neto"),
        48: ("penafiel", "p_pena_carbonell"),
        49: ("penafiel", "p_pena_carlinhos"),
        50: ("penafiel", "p_pena_joaopinto"),
        51: ("penafiel", "p_pena_juanda"),
        52: ("penafiel", "p_pena_davo"),
        53: ("penafiel", "p_pena_jota"),
        54: ("penafiel", "p_pena_maddi"),
        55: ("penafiel", "p_pena_nunomartins"),
        56: ("penafiel", "p_pena_joaoleal"),
        57: ("penafiel", "p_pena_alcaina"),
        58: ("penafiel", "p_pena_sery"),
        59: ("penafiel", "p_pena_svensson"),
        60: ("penafiel", "p_extra_andreschutte"),

        # Fabril
        61: ("fabril", "p_fabril_hugorios"),
        62: ("fabril", "p_fabril_alexmarques"),
        63: ("fabril", "p_fabril_samu"),
        64: ("fabril", "p_fabril_canedo"),
        65: ("fabril", "p_fabril_malick"),
        66: ("fabril", "p_fabril_vergara"),
        67: ("fabril", "p_fabril_ikervidal"),
        68: ("fabril", "p_fabril_pablogarcia"),
        69: ("fabril", "p_fabril_teijo"),
        70: ("fabril", "p_fabril_mardones"),
        71: ("fabril", "p_fabril_carrillo"),
        72: ("fabril", "p_fabril_estevez"),
        73: ("fabril", "p_fabril_sanjose"),
        74: ("fabril", "p_fabril_niang"),
        75: ("fabril", "p_fabril_ferreiro"),
        76: ("fabril", "p_fabril_luisao"),
        77: ("fabril", "p_fabril_rubenlopez"),
        78: ("fabril", "p_fabril_justino"),
        79: ("fabril", "p_fabril_guerrero"),
        80: ("fabril", "p_fabril_cortes"),
        81: ("fabril", "p_fabril_areosa"),
        82: ("fabril", "p_fabril_ochoa"),
        83: ("fabril", "p_fabril_dipanda"),
        84: ("fabril", "p_fabril_dominguez"),
    }

    updated_players = []

    with zipfile.ZipFile(pptx_path, 'r') as z:
        for slide_num, (t_id, player_id) in slide_map.items():
            slide_file = f"ppt/slides/slide{slide_num}.xml"
            if slide_file not in z.namelist():
                continue

            slide_xml = z.read(slide_file)
            root = ET.fromstring(slide_xml)

            texts = [node.text for node in root.iter() if node.text and node.text.strip()]
            full_text = " ".join(texts)

            # Parse image
            rels_file = f"ppt/slides/_rels/{os.path.basename(slide_file)}.rels"
            if rels_file in z.namelist():
                rels_root = ET.fromstring(z.read(rels_file))
                media_files = []
                for rel in rels_root.iter():
                    target = rel.attrib.get('Target', '')
                    if 'media/image' in target:
                        media_path = target.replace('../', 'ppt/')
                        if media_path in z.namelist():
                            size = len(z.read(media_path))
                            media_files.append((media_path, size))

                if media_files:
                    media_files.sort(key=lambda x: x[1], reverse=True)
                    best_img_path = media_files[0][0]

                    ext = os.path.splitext(best_img_path)[1] or ".png"
                    photo_filename = f"{player_id}{ext}"
                    photo_filepath = os.path.join(photos_dir, photo_filename)

                    with z.open(best_img_path) as f_in, open(photo_filepath, 'wb') as f_out:
                        f_out.write(f_in.read())

                    photo_url = f"/static/photos/{photo_filename}"
                    db.update_player_photo(player_id, photo_url)

            # Parse season stats breakdown
            season_entries = []
            s_blocks = re.findall(r'(20\d{2}-\d{2})\s+([\s\S]+?)(?=(?:20\d{2}-\d{2}|International|Posicion|$))', full_text)
            for s_year, s_content in s_blocks:
                tot_m = re.search(r'TOTAL\s+(\d+)\s+([\d\.\']+)\'', s_content)
                if tot_m:
                    apps_v = int(tot_m.group(1))
                    mins_v = int(tot_m.group(2).replace('.', '').replace("'", ''))
                    season_entries.append(f"• {s_year}: {mins_v}' mins ({apps_v} partidos)")
                else:
                    dir_m = re.search(r'(\d+)\s+([\d\.\']+)\'', s_content)
                    if dir_m:
                        apps_v = int(dir_m.group(1))
                        mins_v = int(dir_m.group(2).replace('.', '').replace("'", ''))
                        season_entries.append(f"• {s_year}: {mins_v}' mins ({apps_v} partidos)")

            seasons_summary = "\n".join(season_entries) if season_entries else None

            # Keep 2026-27 match stats derived dynamically from stored matches
            cur_s = db.get_player_season_26_27_stats(player_id)
            stats_update = {
                "minutes_played": cur_s["minutes_played"],
                "starts": cur_s["starts"],
                "subs_in": cur_s["subs_in"],
                "yellow_cards": cur_s["yellow_cards"],
                "red_cards": cur_s["red_cards"],
                "goals": cur_s["goals"],
                "seasons_data": seasons_summary
            }
            db.update_player_stats(player_id, stats_update)

            p_obj = db.get_player(player_id)
            p_name = p_obj.name if p_obj else player_id
            updated_players.append({"id": player_id, "name": p_name, "team": t_id, "photo_url": f"/static/photos/{player_id}.png"})

    return {"success": True, "count": len(updated_players), "players": updated_players}

@app.get("/api/admin/auto-import-passport")
def auto_import_passport():
    import zipfile, re, unicodedata
    from xml.etree import ElementTree as ET

    pptx_path = r"C:\Users\Jose Vicente\Downloads\Pasaporte Jugador.pptx"
    if not os.path.exists(pptx_path):
        return {"success": False, "error": f"Archivo no encontrado en {pptx_path}"}

    photos_dir = os.path.join(frontend_dir, "photos")
    os.makedirs(photos_dir, exist_ok=True)

    db_players = db.get_players_by_team("depor")
    
    def norm(n):
        if not n: return ""
        return unicodedata.normalize('NFKD', n).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

    def match_p(scraped):
        sn = norm(scraped)
        if not sn: return None
        for p in db_players:
            pn = norm(p.name)
            if sn == pn or sn in pn or pn in sn:
                return p
        special_map = {
            "jose angel esmoris": "angelino",
            "ricardo rodriguez": "riki rodriguez",
            "joaquin navarro": "ximo navarro",
            "enrique teijo": "quique teijo"
        }
        for k, v in special_map.items():
            if k in sn:
                for p in db_players:
                    if v in norm(p.name):
                        return p

        s_words = sn.split()
        if s_words:
            last = s_words[-1]
            if len(last) >= 3:
                for p in db_players:
                    p_words = norm(p.name).split()
                    if last in p_words:
                        return p
        return None

    updated_players = []

    with zipfile.ZipFile(pptx_path, 'r') as z:
        slide_files = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
        slide_files.sort(key=lambda x: int(re.search(r'\d+', x.split('/')[-1]).group()))

        for slide_file in slide_files:
            slide_xml = z.read(slide_file)
            root = ET.fromstring(slide_xml)

            texts = [node.text for node in root.iter() if node.text and node.text.strip()]
            full_text = " ".join(texts)

            if "NOMBRE|" not in full_text:
                continue

            parts = full_text.split("NOMBRE|")
            if len(parts) < 2: continue
            raw_name = parts[1].split("Overview")[0].strip()
            raw_name = re.split(r'Posicion|Season|CURRENT|International', raw_name)[0].strip()

            player = match_p(raw_name)
            if not player:
                continue

            rels_file = f"ppt/slides/_rels/{os.path.basename(slide_file)}.rels"
            if rels_file not in z.namelist(): continue

            rels_root = ET.fromstring(z.read(rels_file))
            media_files = []
            for rel in rels_root.iter():
                target = rel.attrib.get('Target', '')
                if 'media/image' in target:
                    media_path = target.replace('../', 'ppt/')
                    if media_path in z.namelist():
                        size = len(z.read(media_path))
                        media_files.append((media_path, size))

            if media_files:
                media_files.sort(key=lambda x: x[1], reverse=True)
                best_img_path = media_files[0][0]

                ext = os.path.splitext(best_img_path)[1] or ".png"
                photo_filename = f"{player.id}{ext}"
                photo_filepath = os.path.join(photos_dir, photo_filename)

                with z.open(best_img_path) as f_in, open(photo_filepath, 'wb') as f_out:
                    f_out.write(f_in.read())

                photo_url = f"/static/photos/{photo_filename}"
                db.update_player_photo(player.id, photo_url)

                # Extract per-season statistics (2023-24, 2024-25, 2025-26, 2026-27)
                season_entries = []
                latest_mins = 0
                latest_apps = 0

                # Regex find season rows: e.g. "2025-26 ... TOTAL 2.970' 33"
                s_blocks = re.findall(r'(20\d{2}-\d{2})\s+([\s\S]+?)(?=(?:20\d{2}-\d{2}|International|Posicion|$))', full_text)
                for s_year, s_content in s_blocks:
                    # Find TOTAL line in season content
                    tot_m = re.search(r'TOTAL\s+(\d+)\s+([\d\.\']+)\'', s_content)
                    if tot_m:
                        apps_v = int(tot_m.group(1))
                        mins_v = int(tot_m.group(2).replace('.', '').replace("'", ''))
                        season_entries.append(f"• {s_year}: {mins_v}' mins ({apps_v} partidos)")
                        latest_mins = mins_v
                        latest_apps = apps_v
                    else:
                        # Direct line without TOTAL keyword
                        dir_m = re.search(r'(\d+)\s+([\d\.\']+)\'', s_content)
                        if dir_m:
                            apps_v = int(dir_m.group(1))
                            mins_v = int(dir_m.group(2).replace('.', '').replace("'", ''))
                            season_entries.append(f"• {s_year}: {mins_v}' mins ({apps_v} partidos)")
                            latest_mins = mins_v
                            latest_apps = apps_v

                seasons_summary = "\n".join(season_entries) if season_entries else None

                # Keep 2026-27 match stats derived dynamically from stored matches
                cur_s = db.get_player_season_26_27_stats(player.id)
                stats_update = {
                    "minutes_played": cur_s["minutes_played"],
                    "starts": cur_s["starts"],
                    "subs_in": cur_s["subs_in"],
                    "yellow_cards": cur_s["yellow_cards"],
                    "red_cards": cur_s["red_cards"],
                    "goals": cur_s["goals"],
                    "seasons_data": seasons_summary
                }
                db.update_player_stats(player.id, stats_update)

                updated_players.append({"name": player.name, "id": player.id, "photo_url": photo_url})

@app.get("/api/admin/debug-slides")
def debug_slides():
    import zipfile, re, unicodedata
    from xml.etree import ElementTree as ET

    pptx_path = r"C:\Users\Jose Vicente\Downloads\Pasaporte Jugador.pptx"
    if not os.path.exists(pptx_path):
        return {"error": "PPTX not found"}

    db_players = db.get_all_players()
    
    slides_info = []

    with zipfile.ZipFile(pptx_path, 'r') as z:
        slide_files = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
        slide_files.sort(key=lambda x: int(re.search(r'\d+', x.split('/')[-1]).group()))

        for slide_file in slide_files:
            s_num = int(re.search(r'\d+', slide_file.split('/')[-1]).group())
            slide_xml = z.read(slide_file)
            root = ET.fromstring(slide_xml)

            texts = [node.text for node in root.iter() if node.text and node.text.strip()]
            full_text = " ".join(texts)

            name_search = re.search(r'NOMBRE\|\s*([A-ZÁÉÍÓÚÑa-zàéíóúñ\s\-\.]+)', full_text)
            scraped_name = name_search.group(1).strip() if name_search else "UNKNOWN"
            scraped_name = re.split(r'Overview|Posicion|Season|CURRENT|International', scraped_name)[0].strip()

            rels_file = f"ppt/slides/_rels/{os.path.basename(slide_file)}.rels"
            media_files = []
            if rels_file in z.namelist():
                rels_root = ET.fromstring(z.read(rels_file))
                for rel in rels_root.iter():
                    target = rel.attrib.get('Target', '')
                    if 'media/image' in target:
                        m_path = target.replace('../', 'ppt/')
                        if m_path in z.namelist():
                            sz = len(z.read(m_path))
                            media_files.append((m_path, sz))

            media_files.sort(key=lambda x: x[1], reverse=True)

            slides_info.append({
                "slide": s_num,
                "scraped_name": scraped_name,
                "best_image": media_files[0][0] if media_files else None,
                "images_count": len(media_files)
            })


    pitch_x = float(payload.get("pitch_x", 0.5))
    pitch_y = float(payload.get("pitch_y", 0.5))
    db.update_player_pitch_position(player_id, pitch_x, pitch_y)
    return {"success": True, "player_id": player_id, "pitch_x": pitch_x, "pitch_y": pitch_y}

@app.post("/api/teams/{team_id}/pitch_positions")



def update_team_pitch_positions(team_id: str, payload: List[Dict]):
    db.update_team_pitch_positions(payload)
    return {"success": True, "count": len(payload)}

@app.post("/api/teams/{team_id}/reset_pitch_positions")
def reset_team_pitch_positions(team_id: str):
    db.reset_team_pitch_positions(team_id)
    return {"success": True, "team_id": team_id}

@app.post("/api/matches/{match_id}/lineup_positions")
def update_match_lineup_positions(match_id: str, payload: List[Dict]):
    db.update_match_lineup_positions(match_id, payload)
    return {"success": True, "count": len(payload)}

@app.post("/api/teams/{team_id}/players/import-csv")
async def import_players_csv(team_id: str, file: UploadFile = File(...)):
    filename = file.filename.lower()
    contents = await file.read()
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
        
    try:
        if filename.endswith(".csv"):
            df = pd.read_csv(tmp_path)
        else:
            df = pd.read_excel(tmp_path)
        count = db.import_players_from_dataframe(df, team_id)
        os.remove(tmp_path)
        return {"imported_count": count}
    except Exception as e:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(status_code=400, detail=f"Error parsing CSV/Excel: {str(e)}")

# Matches & Lineups API
@app.get("/api/teams/{team_id}/matches", response_model=List[Match])
def list_matches(team_id: str):
    return db.get_matches_by_team(team_id)

@app.post("/api/matches", response_model=Match)
def create_match(match: MatchCreate):
    return db.create_match(
        team_id=match.team_id,
        opponent=match.opponent,
        date=match.date,
        result_type=match.result_type,
        home_goals=match.home_goals,
        away_goals=match.away_goals,
        is_home=match.is_home,
        competition=match.competition,
        custom_title=match.custom_title,
        playing_time=match.playing_time,
        substitute_cadence=match.substitute_cadence,
        substitution_times=match.substitution_times
    )

@app.delete("/api/matches/{match_id}")
def delete_match(match_id: str):
    db.delete_match(match_id)
    return {"success": True, "match_id": match_id}

@app.put("/api/matches/{match_id}")
def update_match(match_id: str, payload: Dict):
    updated = db.update_match_details(match_id, payload)
    if not updated:
        raise HTTPException(status_code=404, detail="Match not found")
    return updated

@app.get("/api/matches/{match_id}/lineup_positions")
def get_match_lineup_positions(match_id: str):
    data = db.get_match_full_data(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="Match not found")
    # Para el guardado de lineup via posiciones
    return {"status": "ok"}

@app.get("/api/matches/{match_id}/squad_roster")
def get_match_squad_roster(match_id: str):
    data = db.get_match_full_data(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="Match not found")
    
    match_obj = data["match"]
    team_players = db.get_players_by_team(match_obj.team_id)
    starters_map = {s.player_id: s for s in data["starters"]}
    subs_map = {s.player_id: s for s in data["substitutes"]}
    
    roster = []
    for p in team_players:
        p_dict = p.model_dump()
        if p.id in starters_map:
            st = starters_map[p.id]
            p_dict["match_status"] = "STARTER"
            p_dict["field_position"] = st.field_position
            p_dict["grid_x"] = st.grid_x
            p_dict["grid_y"] = st.grid_y
            p_dict["has_yellow_card"] = st.has_yellow_card
            p_dict["has_red_card"] = st.has_red_card
            p_dict["card_minute"] = st.card_minute
            p_dict["card_type"] = st.card_type
            p_dict["sub_out_minute"] = st.sub_out_minute
        elif p.id in subs_map:
            sub = subs_map[p.id]
            p_dict["match_status"] = "SUBSTITUTE"
            p_dict["field_position"] = "SUB"
            p_dict["grid_x"] = 0.0
            p_dict["grid_y"] = 0.0
            p_dict["has_yellow_card"] = sub.has_yellow_card
            p_dict["has_red_card"] = sub.has_red_card
            p_dict["card_minute"] = sub.card_minute
            p_dict["card_type"] = sub.card_type
            p_dict["sub_in_minute"] = sub.sub_in_minute
        else:
            p_dict["match_status"] = "UNSELECTED"
            p_dict["field_position"] = "NONE"
            p_dict["grid_x"] = 0.5
            p_dict["grid_y"] = 0.5
            p_dict["has_yellow_card"] = False
            p_dict["has_red_card"] = False
            p_dict["card_minute"] = None
            p_dict["card_type"] = None
            p_dict["sub_out_minute"] = None
            p_dict["sub_in_minute"] = None
            
        roster.append(p_dict)
        
    return {
        "match": match_obj,
        "roster": roster,
        "starters_count": len(data["starters"]),
        "substitutes_count": len(data["substitutes"]),
        "substitutions": data["substitutions"],
        "players_map": data["players_map"]
    }

@app.get("/api/matches/{match_id}")
def get_match_details(match_id: str):
    data = db.get_match_full_data(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="Match not found")
    return data

@app.post("/api/matches/{match_id}/lineup")
def save_lineup(match_id: str, payload: Dict):
    starters = payload.get("starters", [])
    substitutes = payload.get("substitutes", [])
    subs_events = payload.get("substitutions", [])
    db.save_lineup_and_subs(match_id, starters, substitutes, subs_events)
    return {"success": True}

from pydantic import BaseModel
from bs4 import BeautifulSoup

@app.get("/api/debug-scraper")
def debug_scraper():
    try:
        with open("c:/Users/Jose Vicente/Desktop/Depor - Demographic/besoccer_dump.html", "r", encoding="utf-8") as f:
            html = f.read()
        soup = BeautifulSoup(html, 'html.parser')
        
        wrappers = soup.select('.player-wrapper')
        results = []
        for w in wrappers[:5]: # just look at first 5 to keep it small
            results.append({"html": str(w)})
        
        return {"wrappers": results}
    except Exception as e:
        return {"error": str(e)}

class ImportMatchRequest(BaseModel):
    url: str
    create_unknowns: bool = False
    ignore_unknowns: bool = False

@app.post("/api/matches/{match_id}/import")
def import_match_from_url(match_id: str, req: ImportMatchRequest):
    data = db.get_match_full_data(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="Match not found")
        
    match = data["match"]
    team_id = match.team_id
    
    from backend import scraper
    scrape_result = scraper.scrape_besoccer_match(req.url)
    if "error" in scrape_result:
        raise HTTPException(status_code=400, detail=scrape_result["error"])
        
    team_players = db.get_players_by_team(team_id)
    name_to_id = {p.name.lower(): p.id for p in team_players}
    
    def normalize_name(n: str):
        import unicodedata
        n = unicodedata.normalize('NFKD', n).encode('ASCII', 'ignore').decode('utf-8')
        return n.lower().strip()
        
    def is_match(scraped_name: str, db_name: str) -> bool:
        s = normalize_name(scraped_name)
        d = normalize_name(db_name)
        if s == d: return True
        if s in d or d in s: return True
        
        import re
        s_clean = re.sub(r'[^\w\s]', '', s).split()
        d_clean = re.sub(r'[^\w\s]', '', d).split()
        
        if not s_clean or not d_clean: return False
        
        if s_clean[-1] == d_clean[-1] and len(s_clean[-1]) >= 3:
            if s_clean[0][0] == d_clean[0][0]:
                return True
                
        return False

    def count_matches(players_list):
        count = 0
        for s_data in players_list:
            name = s_data if isinstance(s_data, str) else s_data.get("name", "")
            for p in team_players:
                if is_match(name, p.name):
                    count += 1
                    break
        return count
        
    home_players = scrape_result["home"]["starters"] + scrape_result["home"]["subs"]
    away_players = scrape_result["away"]["starters"] + scrape_result["away"]["subs"]
    
    home_matches = count_matches(home_players)
    away_matches = count_matches(away_players)
    
    if home_matches >= away_matches and home_matches > 0:
        scraped_starters = scrape_result["home"]["starters"]
        scraped_subs = scrape_result["home"]["subs"]
    elif away_matches > home_matches:
        scraped_starters = scrape_result["away"]["starters"]
        scraped_subs = scrape_result["away"]["subs"]
    else:
        # Fallback
        if match.is_home:
            scraped_starters = scrape_result["home"]["starters"]
            scraped_subs = scrape_result["home"]["subs"]
        else:
            scraped_starters = scrape_result["away"]["starters"]
            scraped_subs = scrape_result["away"]["subs"]
            
    if not scraped_starters and not scraped_subs:
        raise HTTPException(
            status_code=400, 
            detail="No se ha podido leer ningún jugador. Motivos posibles: BeSoccer está bloqueando la extracción (Anti-bot) o el partido aún no tiene las alineaciones publicadas en la web."
        )

    def find_player_id(name: str):
        for p in team_players:
            if is_match(name, p.name):
                return p.id
        return None

    import uuid
    
    unknown_players_found = []
    
    def get_or_handle_player(s_data: dict):
        name = s_data.get("name", "")
        if not name: return None
        pid = find_player_id(name)
        if pid: return pid
        
        if req.create_unknowns:
            new_id = f"p_{team_id}_{uuid.uuid4().hex[:8]}"
            db.create_player(name=name, birthdate="", detailed_position="Desconocida", team_id=team_id, player_id=new_id)
            image_url = s_data.get("image")
            if image_url:
                db.update_player_photo(new_id, image_url)
            p_obj = db.get_player(new_id)
            if p_obj: team_players.append(p_obj)
            return new_id
            
        if not req.ignore_unknowns:
            if name not in unknown_players_found:
                unknown_players_found.append(name)
        return None

    # Pre-pass to find unknown players
    if not req.create_unknowns and not req.ignore_unknowns:
        for s_data in scraped_starters + scraped_subs:
            if isinstance(s_data, str): s_data = {"name": s_data}
            name = s_data.get("name", "")
            if name and not find_player_id(name):
                if name not in unknown_players_found:
                    unknown_players_found.append(name)
        
        if unknown_players_found:
            return {"status": "pending_creation", "unknown_players": unknown_players_found}

    slots = [
        {"role": "GK", "grid_x": 0.50, "grid_y": 0.89},
        {"role": "LB", "grid_x": 0.20, "grid_y": 0.73},
        {"role": "LCB", "grid_x": 0.40, "grid_y": 0.77},
        {"role": "RCB", "grid_x": 0.60, "grid_y": 0.77},
        {"role": "RB", "grid_x": 0.80, "grid_y": 0.73},
        {"role": "DM", "grid_x": 0.50, "grid_y": 0.60},
        {"role": "LCM", "grid_x": 0.38, "grid_y": 0.48},
        {"role": "RCM", "grid_x": 0.62, "grid_y": 0.48},
        {"role": "LW", "grid_x": 0.20, "grid_y": 0.28},
        {"role": "ST", "grid_x": 0.50, "grid_y": 0.18},
        {"role": "RW", "grid_x": 0.80, "grid_y": 0.28},
    ]

    new_starters = []
    
    for i, s_data in enumerate(scraped_starters[:11]):
        if isinstance(s_data, str): s_data = {"name": s_data}
        p_id = get_or_handle_player(s_data)
        if not p_id: continue
        
        slot = slots[i] if i < len(slots) else {"role": "POS", "grid_x": 0.5, "grid_y": 0.5}
        
        starter = {
            "player_id": p_id,
            "field_position": slot["role"],
            "grid_x": slot["grid_x"],
            "grid_y": slot["grid_y"],
            "has_yellow_card": s_data.get("has_yellow_card", False),
            "has_red_card": s_data.get("has_red_card", False),
            "sub_out_minute": s_data.get("sub_out_minute"),
            "goals": s_data.get("goals", 0)
        }
        new_starters.append(starter)
        
    new_subs = []
    for s_data in scraped_subs:
        if isinstance(s_data, str): s_data = {"name": s_data}
        p_id = get_or_handle_player(s_data)
        if not p_id: continue
        
        sub = {
            "player_id": p_id,
            "has_yellow_card": s_data.get("has_yellow_card", False),
            "has_red_card": s_data.get("has_red_card", False),
            "sub_in_minute": s_data.get("sub_in_minute"),
            "goals": s_data.get("goals", 0)
        }
        new_subs.append(sub)
        
    # Build substitutions list from sub_out_minute and sub_in_minute mapping
    subs_events = []
    
    # All players in this match
    all_players_in_match = new_starters + new_subs
    
    # Find players who came in
    players_in = [p for p in all_players_in_match if p.get("sub_in_minute") is not None]
    # Find players who went out
    players_out = [p for p in all_players_in_match if p.get("sub_out_minute") is not None]
    
    for p_in in players_in:
        # Try to find someone who went out at the exact same minute
        p_out_match = next((p for p in players_out if p["sub_out_minute"] == p_in["sub_in_minute"]), None)
        if p_out_match:
            subs_events.append({
                "player_in_id": p_in["player_id"],
                "player_out_id": p_out_match["player_id"],
                "minute": p_in["sub_in_minute"]
            })
            # Remove from players_out so we don't match them again if multiple subs in same minute
            players_out.remove(p_out_match)
        else:
            # If no exact match, just create an event with a dummy out player or skip
            # We'll skip for now if we can't match it, but it should match in most cases
            pass
            
    db.save_lineup_and_subs(match_id, new_starters, new_subs, subs_events)
    
    return {"success": True}

@app.get("/api/debug-events")
def debug_events():
    import cloudscraper
    from bs4 import BeautifulSoup
    url = "https://www.besoccer.es/partido/st-pauli/deportivo/202729586/eventos"
    try:
        scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False})
        html = scraper.get(url).text
        soup = BeautifulSoup(html, 'html.parser')
        
        matches = []
        for name in ['ede', 'eddahchouri']:
            nodes = soup.find_all(string=lambda text: text and name in text.lower())
            for node in nodes:
                matches.append(f"Name: {name} | Text matched: {node.strip()} | Parent HTML: {str(node.parent)[:200]}")
                
        with open("c:/Users/Jose Vicente/Desktop/Depor - Demographic/debug_name_matches.txt", "w", encoding="utf-8") as f:
            f.write("\n\n".join(matches))
            
        return {"success": True, "count": len(matches)}
    except Exception as e:
        return {"error": str(e)}

# Live Slide Previews API
@app.get("/api/preview/demographic/{team_id}")
def preview_demographic(team_id: str):
    team = db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    players = db.get_players_by_team(team_id)
    engine = LayoutEngine()
    col_widths = engine.calculate_demographic_column_widths([p.model_dump() for p in players])
    
    return {
        "team": team,
        "players": players,
        "column_widths": col_widths
    }

@app.get("/api/preview/squad-pitch/{team_id}")
def preview_squad_pitch(team_id: str):
    team = db.get_team(team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    players = db.get_players_by_team(team_id, include_extra_pitch=True)
    engine = LayoutEngine()
    
    injured = []
    pitch_players = []
    for p in players:
        if getattr(p, 'is_injured', False):
            injured.append(p)
        else:
            pitch_players.append(p)
            
    boxes = engine.layout_full_squad([p.model_dump() for p in pitch_players])
    return {
        "team": team,
        "boxes": boxes,
        "injured": injured,
        "all_pitch_players": players
    }

@app.get("/api/preview/match/{match_id}")
def preview_match(match_id: str):
    data = db.get_match_full_data(match_id)
    if not data:
        raise HTTPException(status_code=404, detail="Match not found")
        
    engine = LayoutEngine(PitchSpec(x_center=6.4, y_top=1.35, height=5.25, w_top=5.5, w_bottom=7.8))
    starters_dicts = []
    subbed_out = {s.player_out_id: s.minute for s in data['substitutions']}
    
    for st in data['starters']:
        sd = st.model_dump()
        if st.player_id in subbed_out:
            sd['substituted_minute'] = subbed_out[st.player_id]
        starters_dicts.append(sd)
        
    starter_boxes = engine.layout_match_starters(starters_dicts, {k: v.model_dump() for k, v in data['players_map'].items()})
    return {
        "match": data['match'],
        "team": data['team'],
        "starter_boxes": starter_boxes,
        "substitutes": data['substitutes'],
        "substitutions": data['substitutions'],
        "players_map": data['players_map']
    }

from backend.pdf_generator import PDFReportGenerator

def sanitize_filename(name: str) -> str:
    replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n', 'Ñ': 'N', 'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U'}
    for k, v in replacements.items():
        name = name.replace(k, v)
    clean = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)
    return clean

def build_pptx(team_id: Optional[str], match_ids: List[str], export_all: bool) -> Tuple[str, str]:
    generator = PPTXGenerator()
    if export_all:
        teams = db.get_teams()
        for team in teams:
            players = db.get_players_by_team(team.id, include_extra_pitch=True)
            generator.generate_demographic_slide(team, db.get_players_by_team(team.id)) # demographic slide is original roster
            generator.generate_squad_pitch_slide(team, players)
            matches = db.get_matches_by_team(team.id)
            for m in matches:
                m_data = db.get_match_full_data(m.id)
                if m_data:
                    generator.generate_match_report_slide(m_data)
        out_name = "Full_Club_Analysis_Player.pptx"
    else:
        team = db.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        players_demographic = db.get_players_by_team(team_id)
        players_pitch = db.get_players_by_team(team_id, include_extra_pitch=True)
        generator.generate_demographic_slide(team, players_demographic)
        generator.generate_squad_pitch_slide(team, players_pitch)
        if not match_ids:
            match_ids = [m.id for m in db.get_matches_by_team(team_id)]
        for m_id in match_ids:
            m_data = db.get_match_full_data(m_id)
            if m_data:
                generator.generate_match_report_slide(m_data)
        clean_team = sanitize_filename(team.name)
        out_name = f"{clean_team}_Analysis_Player.pptx"
            
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, out_name)
    generator.save(file_path)
    return file_path, out_name

def build_pdf(team_id: Optional[str], match_ids: List[str], export_all: bool) -> Tuple[str, str]:
    tmp_dir = tempfile.mkdtemp()
    if export_all:
        out_name = "Full_Club_Analysis_Player.pdf"
        pdf_path = os.path.join(tmp_dir, out_name)
        generator = PDFReportGenerator(pdf_path)
        teams = db.get_teams()
        for team in teams:
            players_demographic = db.get_players_by_team(team.id)
            players_pitch = db.get_players_by_team(team.id, include_extra_pitch=True)
            generator.generate_cover_slide(team)
            generator.generate_demographic_slide(team, players_demographic)
            generator.generate_squad_pitch_slide(team, players_pitch)
            matches = db.get_matches_by_team(team.id)
            for m in matches:
                m_data = db.get_match_full_data(m.id)
                if m_data:
                    generator.generate_match_report_slide(m_data)
        generator.save()
    else:
        team = db.get_team(team_id)
        if not team:
            raise HTTPException(status_code=404, detail="Team not found")
        players_demographic = db.get_players_by_team(team_id)
        players_pitch = db.get_players_by_team(team_id, include_extra_pitch=True)
        clean_team = sanitize_filename(team.name)
        out_name = f"{clean_team}_Analysis_Player.pdf"
        pdf_path = os.path.join(tmp_dir, out_name)
        generator = PDFReportGenerator(pdf_path)
        generator.generate_cover_slide(team)
        generator.generate_demographic_slide(team, players_demographic)
        generator.generate_squad_pitch_slide(team, players_pitch)
        if not match_ids:
            match_ids = [m.id for m in db.get_matches_by_team(team_id)]
        for m_id in match_ids:
            m_data = db.get_match_full_data(m_id)
            if m_data:
                generator.generate_match_report_slide(m_data)
        generator.save()
    return pdf_path, out_name

# Export Actions
@app.post("/api/export/pptx")
def export_pptx_post(payload: Dict):
    team_id = payload.get("team_id")
    match_ids = payload.get("match_ids", [])
    export_all = payload.get("all_teams", False)
    file_path, out_name = build_pptx(team_id, match_ids, export_all)
    return FileResponse(
        file_path,
        filename=out_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )

@app.get("/api/export/pptx")
def export_pptx_get(team_id: Optional[str] = "depor", all_teams: bool = False):
    file_path, out_name = build_pptx(team_id, [], all_teams)
    return FileResponse(
        file_path,
        filename=out_name,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )

@app.post("/api/export/pdf")
def export_pdf_post(payload: Dict):
    team_id = payload.get("team_id")
    match_ids = payload.get("match_ids", [])
    export_all = payload.get("all_teams", False)
    pdf_path, out_name = build_pdf(team_id, match_ids, export_all)
    return FileResponse(
        pdf_path,
        filename=out_name,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )

@app.get("/api/export/pdf")
def export_pdf_get(team_id: Optional[str] = "depor", all_teams: bool = False):
    pdf_path, out_name = build_pdf(team_id, [], all_teams)
    return FileResponse(
        pdf_path,
        filename=out_name,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{out_name}"'}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
