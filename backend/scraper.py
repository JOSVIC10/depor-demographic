import cloudscraper
from bs4 import BeautifulSoup
import re

import cloudscraper
import requests
from bs4 import BeautifulSoup
import re
import time

def scrape_besoccer_match(url: str):
    html_content = None
    last_error = None

    headers_list = [
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://es.besoccer.com/',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://es.besoccer.com/',
        }
    ]

    # Attempt 1 & 2: Cloudscraper with different browsers
    for browser_name in ['chrome', 'firefox']:
        try:
            scraper = cloudscraper.create_scraper(
                browser={'browser': browser_name, 'platform': 'windows', 'desktop': True}
            )
            resp = scraper.get(url, headers=headers_list[0 if browser_name == 'chrome' else 1], timeout=12)
            if resp.status_code == 200 and len(resp.text) > 1000:
                html_content = resp.text
                break
        except Exception as e:
            last_error = str(e)

    # Attempt 3: Standard requests Session with custom headers if Cloudscraper failed
    if not html_content:
        for headers in headers_list:
            try:
                session = requests.Session()
                resp = session.get(url, headers=headers, timeout=12)
                if resp.status_code == 200 and len(resp.text) > 1000:
                    html_content = resp.text
                    break
            except Exception as e:
                last_error = str(e)

    if not html_content:
        return {"error": f"No se pudo descargar la información del partido: {last_error or 'Bloqueo o timeout'}"}

    try:
        with open("c:/Users/Jose Vicente/Desktop/Depor - Demographic/besoccer_dump.html", "w", encoding="utf-8") as f:
            f.write(html_content)
    except Exception:
        pass

    soup = BeautifulSoup(html_content, 'html.parser')
    
    home_starters, away_starters = [], []
    home_subs, away_subs = [], []
    
    # 1. Extraer Titulares (Starters)
    starters_nodes = soup.select('.player-wrapper, .pitch-player, .col-lineup .player, .col-lineup tr, .lineup-list .player')
    
    import json
    def extract_player_data(node):
        name = ""
        image = None
        # 1. Try to extract name from BeSoccer's JSON-LD script (new format)
        script_tag = node.select_one('script[type="application/ld+json"]')
        if script_tag and script_tag.string:
            try:
                js_data = json.loads(script_tag.string)
                if isinstance(js_data, dict):
                    if "name" in js_data: name = js_data["name"]
                    if "image" in js_data: image = js_data["image"]
            except:
                pass
                
        # 2. Fallback to .name span
        if not name:
            name_node = node.select_one('.name, .player-name, .pn')
            if name_node:
                name = name_node.get_text(strip=True)
                
        # 3. Last fallback (messy text)
        if not name:
            text = node.get_text(separator=" ", strip=True)
            name = text.split(" ")[-1] if len(text) > 40 else text

        if not image:
            img_tag = node.select_one('img')
            if img_tag and img_tag.get('src'):
                image = img_tag['src']
                if 'data:image' in image: image = None
            
        data = {"name": name.strip(), "image": image, "has_yellow_card": False, "has_red_card": False, "sub_out_minute": None, "sub_in_minute": None, "goals": 0}
        
        # Check for icons indicating goals
        for icon in node.select('.icon-gol, .goal-icon, .gol'):
            m = re.search(r'\d+', icon.get_text())
            if m:
                data["goals"] += int(m.group())
            else:
                data["goals"] += 1
                
        # Check for cards
        if node.select_one('.icon-tarjeta-amarilla, .yellow-card, .tarjeta-amarilla, .amarilla'):
            data["has_yellow_card"] = True
        if node.select_one('.icon-tarjeta-roja, .red-card, .tarjeta-roja, .roja'):
            data["has_red_card"] = True
            
        # Check for substitutions
        sub_out = node.select_one('.sub-out, .icon-sub-out, .sale, .cambio-sale')
        if sub_out:
            m = re.search(r'\d+', sub_out.get_text())
            if m: data["sub_out_minute"] = int(m.group())
            
        sub_in = node.select_one('.sub-in, .icon-sub-in, .entra, .cambio-entra')
        if sub_in:
            m = re.search(r'\d+', sub_in.get_text())
            if m: data["sub_in_minute"] = int(m.group())
            
        return data
        
    def get_player_parent(p):
        if p.name == 'span' or (p.get('class') and isinstance(p.get('class'), list) and len(p.get('class')) > 0 and p.get('class')[0] in ['name', 'player-name', 'pn']):
            return p.parent if p.parent else p
        return p

    valid_starters = []
    debug_starters = []
    for p in starters_nodes:
        parent = get_player_parent(p)
        data = extract_player_data(parent)
        debug_starters.append(data["name"])
        if len(data["name"]) > 2 and len(data["name"]) < 40:
            valid_starters.append(data)
            
    try:
        with open("c:/Users/Jose Vicente/Desktop/Depor - Demographic/debug_scraper_output.json", "w", encoding="utf-8") as f:
            json.dump({"starters_nodes_len": len(starters_nodes), "valid_starters_len": len(valid_starters), "debug_names": debug_starters}, f, indent=2)
    except Exception:
        pass
    for i, data in enumerate(valid_starters):
        if i < 11:
            home_starters.append(data)
        else:
            away_starters.append(data)
            
    # 2. Extraer Suplentes Locales
    for p in soup.select('.col-bench.local .player, .col-bench.local tr, .col-bench.local li, .col-bench.local .name'):
        parent = get_player_parent(p)
        data = extract_player_data(parent)
        if len(data["name"]) > 2 and len(data["name"]) < 40:
            if not any(x['name'] == data['name'] for x in home_subs):
                home_subs.append(data)
            
    # 3. Extraer Suplentes Visitantes
    for p in soup.select('.col-bench.visitor .player, .col-bench.visitor tr, .col-bench.visitor li, .col-bench.visitor .name'):
        parent = get_player_parent(p)
        data = extract_player_data(parent)
        if len(data["name"]) > 2 and len(data["name"]) < 40:
            if not any(x['name'] == data['name'] for x in away_subs):
                away_subs.append(data)

    # 4. Fallback: Fetch /eventos URL to get events if not found on alineaciones page
    try:
        events_url = url.replace('/alineaciones', '/eventos')
        if '/eventos' not in events_url:
            events_url = url.rstrip('/') + '/eventos'
            
        ev_response = scraper.get(events_url, timeout=15)
        ev_soup = BeautifulSoup(ev_response.text, 'html.parser')
        
        all_players = home_starters + away_starters + home_subs + away_subs
        for p_data in all_players:
            if not p_data["name"] or len(p_data["name"]) < 3: continue
            
            # Use the last word of the name for broader matching in events
            last_name = p_data["name"].split(" ")[-1].lower()
            
            import re
            pattern = re.compile(rf'\b{re.escape(last_name)}\b', re.IGNORECASE)
            nodes = ev_soup.find_all(string=lambda text: text and pattern.search(text))
            
            processed_containers = set()
            eventos_goals = 0
            goal_minutes = set()
            
            for text_node in nodes:
                container = text_node.parent
                # Go up to 3 levels to find a block container like li, tr, or div.row
                for _ in range(3):
                    if not container: break
                    if container.name in ['li', 'tr'] or (container.name == 'div' and ('row' in container.get('class', []) or 'event' in container.get('class', []))):
                        break
                    container = container.parent
                    
                if not container:
                    container = text_node.parent.parent if text_node.parent else text_node.parent
                    
                if not container or id(container) in processed_containers:
                    continue
                processed_containers.add(id(container))
                
                # Find minute text from parent tree
                minute_text = container.get_text()
                if container.parent: minute_text += " " + container.parent.get_text()
                if container.parent and container.parent.parent: minute_text += " " + container.parent.parent.get_text()
                
                # check for goals
                if container.select('.icon-gol, .goal-icon, .gol, .icon-ball, img[src*="ball"], img[src*="gol"], img[src*="accion1"], img[alt*="Gol"], .event-1, .event-7'):
                    m = re.search(r"(\d+)'", minute_text) or re.search(r"\b(\d+)\b", minute_text)
                    minute = int(m.group(1)) if m else len(goal_minutes) + 1000 # Fallback unique ID if no minute
                    if minute not in goal_minutes:
                        goal_minutes.add(minute)
                        eventos_goals += 1
                    
                # check for cards
                if container.select_one('.icon-tarjeta-amarilla, .yellow-card, .tarjeta-amarilla, .amarilla, .icon-yellow-card, img[src*="accion5"], img[alt*="amarilla"], .event-2'):
                    p_data["has_yellow_card"] = True
                if container.select_one('.icon-tarjeta-roja, .red-card, .tarjeta-roja, .roja, .icon-red-card, img[src*="accion6"], img[alt*="roja"], .event-3, .event-4'):
                    p_data["has_red_card"] = True
                    
                # check for subs
                sub_out = container.select_one('.sub-out, .icon-sub-out, .sale, .cambio-sale, .event-18')
                if sub_out:
                    m = re.search(r"(\d+)'", minute_text) or re.search(r"\b(\d+)\b", minute_text)
                    if m: p_data["sub_out_minute"] = int(m.group(1))
                    
                sub_in = container.select_one('.sub-in, .icon-sub-in, .entra, .cambio-entra, .event-19')
                if sub_in:
                    m = re.search(r"(\d+)'", minute_text) or re.search(r"\b(\d+)\b", minute_text)
                    if m: p_data["sub_in_minute"] = int(m.group(1))
                    
            # Avoid double counting goals from the alineaciones page and eventos page
            p_data["goals"] = max(p_data["goals"], eventos_goals)
    except Exception as e:
        print(f"Error fetching eventos: {e}")

    return {
        "success": True,
        "home": {
            "starters": home_starters,
            "subs": home_subs
        },
        "away": {
            "starters": away_starters,
            "subs": away_subs
        }
    }

def scrape_besoccer_player(url: str):
    """Scrapes a BeSoccer player profile page to extract details, photo, birthdate, career stats."""
    html_content = None
    last_error = None

    headers_list = [
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Referer': 'https://es.besoccer.com/',
        },
        {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://es.besoccer.com/',
        }
    ]

    for browser_name in ['chrome', 'firefox']:
        try:
            scraper = cloudscraper.create_scraper(
                browser={'browser': browser_name, 'platform': 'windows', 'desktop': True}
            )
            resp = scraper.get(url, headers=headers_list[0 if browser_name == 'chrome' else 1], timeout=12)
            if resp.status_code == 200 and len(resp.text) > 1000:
                html_content = resp.text
                break
        except Exception as e:
            last_error = str(e)

    if not html_content:
        for headers in headers_list:
            try:
                session = requests.Session()
                resp = session.get(url, headers=headers, timeout=12)
                if resp.status_code == 200 and len(resp.text) > 1000:
                    html_content = resp.text
                    break
            except Exception as e:
                last_error = str(e)

    if not html_content:
        return {"error": f"No se pudo descargar la información del jugador: {last_error or 'Bloqueo o timeout'}"}

    soup = BeautifulSoup(html_content, 'html.parser')
    import json

    player_data = {
        "name": "",
        "photo_url": None,
        "photo_src_url": None,
        "birthdate": "2000-01-01",
        "detailed_position": "Centrocampista",
        "minutes_played": 0,
        "starts": 0,
        "subs_in": 0,
        "goals": 0,
        "yellow_cards": 0,
        "red_cards": 0,
        "seasons_data": ""
    }

    # ===== 1. EXTRACT NAME =====
    # Priority: .head-title > og:title > title tag > JSON-LD (only @type=Person with birthDate)
    head_title = soup.select_one('.head-title')
    if head_title:
        player_data["name"] = head_title.get_text(strip=True)

    if not player_data["name"]:
        og = soup.select_one('meta[property="og:title"]')
        if og:
            og_content = og.get('content', '')
            m = re.match(r'Estad[ií]sticas de (.+?) hoy', og_content)
            if m:
                player_data["name"] = m.group(1).strip()
            else:
                # Try extracting before " | BeSoccer"
                player_data["name"] = og_content.split('|')[0].replace('Estadísticas de', '').replace('Estadisticas de', '').strip().rstrip(',').strip()

    if not player_data["name"]:
        title_tag = soup.select_one('title')
        if title_tag:
            t_text = title_tag.get_text()
            m = re.match(r'Estad[ií]sticas (.+?) hoy', t_text)
            if m:
                player_data["name"] = m.group(1).strip()
            else:
                player_data["name"] = t_text.split("-")[0].split("|")[0].strip()

    # JSON-LD fallback: only use if it has birthDate (main player entity, not squad members)
    if not player_data["name"]:
        for script_tag in soup.select('script[type="application/ld+json"]'):
            if script_tag and script_tag.string:
                try:
                    js_data = json.loads(script_tag.string)
                    if isinstance(js_data, dict) and js_data.get("@type") in ["Person", "Athlete"] and "birthDate" in js_data:
                        if "name" in js_data:
                            player_data["name"] = js_data["name"].strip()
                            break
                except Exception:
                    pass

    # ===== 2. EXTRACT PHOTO =====
    # Main player photo: img with alt matching player name and size=340x (large), or first non-nofoto player img
    player_name_lower = player_data["name"].lower() if player_data["name"] else ""

    # Try finding img with alt matching the player name
    for img in soup.select('img'):
        alt = (img.get('alt') or '').strip().lower()
        src = img.get('src') or img.get('data-src') or ''
        if not src or src.startswith('data:'):
            continue
        if 'nofoto' in src:
            continue
        if alt and player_name_lower and alt == player_name_lower:
            # Prefer the largest version (size=340x)
            if '340x' in src or 'medium' in src:
                player_data["photo_src_url"] = src
                break
            elif not player_data["photo_src_url"]:
                player_data["photo_src_url"] = src

    # Fallback: .head-player img, .avatar-box img
    if not player_data["photo_src_url"]:
        for sel in ['.head-player img', '.avatar-box img', '.player-photo img', '.main-player-info img']:
            node = soup.select_one(sel)
            if node:
                src = node.get('src') or node.get('data-src') or ''
                if src and 'nofoto' not in src and not src.startswith('data:'):
                    player_data["photo_src_url"] = src
                    break

    # Even nofoto is acceptable as last resort if no other image found
    if not player_data["photo_src_url"]:
        for img in soup.select('img'):
            alt = (img.get('alt') or '').strip().lower()
            src = img.get('src') or ''
            if alt and player_name_lower and alt == player_name_lower and src:
                player_data["photo_src_url"] = src
                break

    # ===== 3. EXTRACT BIRTHDATE =====
    # Look for "Nacido el DD MES YYYY" pattern in panel-body
    page_text = soup.get_text()
    
    # Spanish month names
    month_map = {
        'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
        'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
        'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12',
        'january': '01', 'february': '02', 'march': '03', 'april': '04',
        'may': '05', 'june': '06', 'july': '07', 'august': '08',
        'september': '09', 'october': '10', 'november': '11', 'december': '12',
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
        'jun': '06', 'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12',
    }
    
    bdate_match = re.search(r'Nacido el (\d{1,2})\s+(\w+)\.?\s+(\d{4})', page_text, re.IGNORECASE)
    if bdate_match:
        day = bdate_match.group(1).zfill(2)
        month_str = bdate_match.group(2).lower().rstrip('.')
        year = bdate_match.group(3)
        month = month_map.get(month_str, '01')
        player_data["birthdate"] = f"{year}-{month}-{day}"
    else:
        # Fallback: ISO date from JSON-LD
        for script_tag in soup.select('script[type="application/ld+json"]'):
            if script_tag and script_tag.string:
                try:
                    js_data = json.loads(script_tag.string)
                    if isinstance(js_data, dict) and "birthDate" in js_data:
                        bdate = js_data["birthDate"].strip()
                        if re.match(r"^\d{4}-\d{2}-\d{2}$", bdate):
                            player_data["birthdate"] = bdate
                            break
                except Exception:
                    pass

    if player_data["birthdate"] == "2000-01-01":
        # Fallback: YYYY-MM-DD or DD/MM/YYYY pattern
        bdate_iso = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", page_text)
        if bdate_iso:
            player_data["birthdate"] = f"{bdate_iso.group(1)}-{bdate_iso.group(2).zfill(2)}-{bdate_iso.group(3).zfill(2)}"
        else:
            bdate_dmy = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", page_text)
            if bdate_dmy:
                player_data["birthdate"] = f"{bdate_dmy.group(3)}-{bdate_dmy.group(2).zfill(2)}-{bdate_dmy.group(1).zfill(2)}"

    # ===== 4. EXTRACT POSITION =====
    # BeSoccer shows position near age info like "31 años DC" or in .panel-body
    pos_panel = soup.select_one('.panel-body')
    if pos_panel:
        # Look for "Posición principal" or position abbreviations
        pos_text = pos_panel.get_text()
        pos_match = re.search(r'Posici[oó]n principal\s*(\w[\w\s]*?)(?:\d|$)', pos_text)
        if pos_match:
            found_pos = pos_match.group(1).strip()
            if found_pos:
                player_data["detailed_position"] = found_pos

    # Position from abbreviation codes in the profile header
    pos_abbrev_map = {
        'GK': 'Portero', 'PT': 'Portero',
        'CB': 'Defensa central', 'DC': 'Defensa central',
        'LB': 'Lateral izquierdo', 'RB': 'Lateral derecho',
        'LI': 'Lateral izquierdo', 'LD': 'Lateral derecho',
        'DM': 'Pivote', 'MC': 'Mediocentro', 'MCD': 'Pivote',
        'MCO': 'Mediocentro ofensivo', 'CAM': 'Mediocentro ofensivo',
        'EI': 'Extremo izquierdo', 'ED': 'Extremo derecho',
        'LW': 'Extremo izquierdo', 'RW': 'Extremo derecho',
        'ST': 'Delantero centro', 'CF': 'Delantero centro',
        'SS': 'Segundo delantero', 'SD': 'Segundo delantero',
        'CEN': 'Delantero centro',
    }

    if player_data["detailed_position"] == "Centrocampista":
        # Try position abbreviation from profile
        for sel in ['.pos', '.pos-text', '.position', '.demarcacion', '.tag-position']:
            nodes = soup.select(sel)
            for n in nodes:
                txt = n.get_text(strip=True).upper()
                if txt in pos_abbrev_map:
                    player_data["detailed_position"] = pos_abbrev_map[txt]
                    break

    if player_data["detailed_position"] == "Centrocampista":
        # Search position keywords in text
        pos_keywords = [
            ("Portero", "Portero"),
            ("Defensa central", "Defensa central"),
            ("Lateral izquierdo", "Lateral izquierdo"),
            ("Lateral derecho", "Lateral derecho"),
            ("Pivote", "Pivote"),
            ("Mediocentro ofensivo", "Mediocentro ofensivo"),
            ("Mediocentro", "Mediocentro"),
            ("Extremo izquierdo", "Extremo izquierdo"),
            ("Extremo derecho", "Extremo derecho"),
            ("Delantero centro", "Delantero centro"),
            ("Delantero", "Delantero centro"),
            ("Defensa", "Defensa central"),
            ("Centrocampista", "Mediocentro")
        ]
        for kw, mapped in pos_keywords:
            if kw.lower() in page_text.lower():
                player_data["detailed_position"] = mapped
                break

    # Check the header area for position abbreviation like "31 años DC"
    for ta_c in soup.select('.ta-c'):
        txt = ta_c.get_text(strip=True)
        m = re.match(r'\d+\s*a[ñn]os?\s*(\w{2,3})', txt)
        if m:
            abbrev = m.group(1).upper()
            if abbrev in pos_abbrev_map and player_data["detailed_position"] == "Centrocampista":
                player_data["detailed_position"] = pos_abbrev_map[abbrev]

    # ===== 5. EXTRACT CAREER / SEASON STATS =====
    # Parse the career table (table.table_parents)
    # Structure: parent_row = team + season aggregates, parent_son = competition breakdown
    # Columns: Equipos | Temp | PJ | Goals | Assists | Yellow | Red | PJ | PT | PS | MIN | Age | Pts | ELO
    career_table = soup.select_one('table.table_parents')
    seasons_list = []
    total_minutes = 0
    total_starts = 0
    total_subs = 0
    total_goals = 0
    total_yellows = 0
    total_reds = 0

    if career_table:
        for row in career_table.select('tr.parent_row'):
            cells = row.select('td')
            if len(cells) < 11:
                continue

            # Extract team name
            team_link = cells[0].select_one('a span')
            team_name = team_link.get_text(strip=True) if team_link else cells[0].get_text(strip=True)

            # Extract season
            season_cell = cells[1].get_text(strip=True)
            season = re.search(r'(\d{4}/\d{2,4})', season_cell)
            season_str = season.group(1) if season else season_cell.strip()

            # Extract stats from cells
            try:
                pj = int(cells[2].get_text(strip=True) or 0)
                goles = int(cells[3].get_text(strip=True) or 0)
                asist = int(cells[4].get_text(strip=True) or 0)
                amarillas = int(cells[5].get_text(strip=True) or 0)
                rojas = int(cells[6].get_text(strip=True) or 0)
                pj2 = int(cells[7].get_text(strip=True) or 0)
                pt = int(cells[8].get_text(strip=True) or 0)
                ps = int(cells[9].get_text(strip=True) or 0)
                min_text = cells[10].get_text(strip=True).replace("'", "").replace(".", "").replace(",", "")
                mins = int(re.search(r'\d+', min_text).group()) if re.search(r'\d+', min_text) else 0
            except (ValueError, IndexError, AttributeError):
                continue

            seasons_list.append(f"{season_str}: {mins}' mins ({pj} partidos)")
            total_minutes += mins
            total_starts += pt
            total_subs += ps
            total_goals += goles
            total_yellows += amarillas
            total_reds += rojas

    # Only use the last 3 seasons for the seasons_data summary
    if seasons_list:
        player_data["seasons_data"] = " | ".join(seasons_list[:3])
    
    player_data["minutes_played"] = total_minutes
    player_data["starts"] = total_starts
    player_data["subs_in"] = total_subs
    player_data["goals"] = total_goals
    player_data["yellow_cards"] = total_yellows
    player_data["red_cards"] = total_reds

    # Fallback: If no career table found, try aggregated stats from stat-row
    if not career_table:
        stat_rows = soup.select('.stat-row, tr.stats, .stats-box tr, table.stats tr')
        for sr in stat_rows:
            txt = sr.get_text(separator=" ", strip=True).lower()
            if "minuto" in txt or "min" in txt:
                m = re.search(r"(\d+[\.,]?\d*)\s*(?:min|')", txt)
                if m:
                    player_data["minutes_played"] = int(m.group(1).replace(".", "").replace(",", ""))
            if "gol" in txt:
                m = re.search(r"(\d+)\s*gol", txt)
                if m:
                    player_data["goals"] = int(m.group(1))

    return {
        "success": True,
        "player": player_data
    }

