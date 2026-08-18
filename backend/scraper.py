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
    """Scrapes a BeSoccer player profile page to extract details, photo, birthdate, and stats."""
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

    # 1. Try JSON-LD script extraction
    for script_tag in soup.select('script[type="application/ld+json"]'):
        if script_tag and script_tag.string:
            try:
                js_data = json.loads(script_tag.string)
                if isinstance(js_data, dict):
                    if js_data.get("@type") in ["Person", "Athlete"] or "birthDate" in js_data or "name" in js_data:
                        if "name" in js_data and not player_data["name"]:
                            player_data["name"] = js_data["name"].strip()
                        if "image" in js_data and not player_data["photo_src_url"]:
                            img = js_data["image"]
                            if isinstance(img, str):
                                player_data["photo_src_url"] = img
                            elif isinstance(img, dict) and "url" in img:
                                player_data["photo_src_url"] = img["url"]
                        if "birthDate" in js_data:
                            bdate = js_data["birthDate"].strip()
                            if re.match(r"^\d{4}-\d{2}-\d{2}$", bdate):
                                player_data["birthdate"] = bdate
                elif isinstance(js_data, list):
                    for item in js_data:
                        if isinstance(item, dict) and item.get("@type") in ["Person", "Athlete"]:
                            if "name" in item and not player_data["name"]:
                                player_data["name"] = item["name"].strip()
                            if "image" in item and not player_data["photo_src_url"]:
                                player_data["photo_src_url"] = item["image"] if isinstance(item["image"], str) else item["image"].get("url")
                            if "birthDate" in item:
                                player_data["birthdate"] = item["birthDate"].strip()
            except Exception:
                pass

    # 2. Extract Name from HTML
    if not player_data["name"]:
        name_node = soup.select_one('h1.name, h1.title, .player-info h1, .head-title h1, .header-player h1, .name-player')
        if name_node:
            player_data["name"] = name_node.get_text(strip=True)
        else:
            title_node = soup.select_one('title')
            if title_node:
                t_text = title_node.get_text()
                player_data["name"] = t_text.split("-")[0].split("|")[0].strip()

    # 3. Extract Photo
    if not player_data["photo_src_url"]:
        photo_node = soup.select_one('.head-player img, .avatar-box img, .player-photo img, .main-player-info img, img.player-img, img[src*="players/"]')
        if photo_node and photo_node.get('src'):
            src = photo_node.get('src')
            if not src.startswith('data:'):
                player_data["photo_src_url"] = src

    # 4. Extract Birthdate & Position from bio items
    page_text = soup.get_text()
    
    # Birthdate search (e.g. 14 May 2002 or 14/05/2002 or 2002-05-14)
    bdate_match = re.search(r"(\d{4})[-/](\d{1,2})[-/](\d{1,2})", page_text)
    if bdate_match and player_data["birthdate"] == "2000-01-01":
        player_data["birthdate"] = f"{bdate_match.group(1)}-{bdate_match.group(2).zfill(2)}-{bdate_match.group(3).zfill(2)}"
    else:
        bdate_match_dmy = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", page_text)
        if bdate_match_dmy and player_data["birthdate"] == "2000-01-01":
            player_data["birthdate"] = f"{bdate_match_dmy.group(3)}-{bdate_match_dmy.group(2).zfill(2)}-{bdate_match_dmy.group(1).zfill(2)}"

    # Position detection
    pos_nodes = soup.select('.pos, .position, .role, .demarcacion, .tag-position')
    found_pos = ""
    for pn in pos_nodes:
        txt = pn.get_text(strip=True)
        if txt:
            found_pos = txt
            break
            
    if not found_pos:
        # Search common position keywords in text
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
                found_pos = mapped
                break

    if found_pos:
        player_data["detailed_position"] = found_pos

    # 5. Extract Stats (Minutes, matches, goals, cards)
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
