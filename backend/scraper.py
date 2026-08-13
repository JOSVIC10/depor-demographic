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
        # 1. Try to extract name from BeSoccer's JSON-LD script (new format)
        script_tag = node.select_one('script[type="application/ld+json"]')
        if script_tag and script_tag.string:
            try:
                js_data = json.loads(script_tag.string)
                if isinstance(js_data, dict) and "name" in js_data:
                    name = js_data["name"]
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
            
        data = {"name": name.strip(), "has_yellow_card": False, "has_red_card": False, "sub_out_minute": None, "sub_in_minute": None, "goals": 0}
        
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
            
    with open("c:/Users/Jose Vicente/Desktop/Depor - Demographic/debug_scraper_output.json", "w", encoding="utf-8") as f:
        json.dump({"starters_nodes_len": len(starters_nodes), "valid_starters_len": len(valid_starters), "debug_names": debug_starters}, f, indent=2)
            
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
