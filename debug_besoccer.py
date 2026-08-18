import cloudscraper
from bs4 import BeautifulSoup
import json, re, sys
sys.stdout.reconfigure(encoding='utf-8')

scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept-Language': 'es-ES,es;q=0.9',
    'Referer': 'https://es.besoccer.com/',
}

# Test with a Depor player URL - Lucas Pérez
resp = scraper.get('https://es.besoccer.com/jugador/lucas-perez-297491', headers=headers, timeout=12)
print(f'STATUS: {resp.status_code}, LENGTH: {len(resp.text)}')

soup = BeautifulSoup(resp.text, 'html.parser')

# ===== NAME =====
# Method 1: og:title meta
og = soup.select_one('meta[property="og:title"]')
if og:
    og_title = og.get('content', '')
    # Extract player name: "Estadísticas de PLAYER_NAME hoy, ..."
    m = re.match(r'Estad.sticas de (.+?) hoy', og_title)
    if m:
        print('NAME from og:title:', m.group(1))
    else:
        print('OG:TITLE (raw):', og_title)

# Method 2: .head-title
ht = soup.select_one('.head-title')
if ht:
    print('NAME from .head-title:', ht.get_text(strip=True))

# Method 3: title tag
title_tag = soup.select_one('title')
if title_tag:
    t = title_tag.get_text()
    m2 = re.match(r'Estad.sticas (.+?) hoy', t)
    if m2:
        print('NAME from title:', m2.group(1))

# ===== PHOTO =====
# Look for main player photo
for sel in ['.head-player img', 'img.player-img', '.photo img', '.avatar-box img', '.main-player-info img']:
    imgs = soup.select(sel)
    for img in imgs:
        src = img.get('src', '')
        if src and 'nofoto' not in src and not src.startswith('data:'):
            print(f'PHOTO ({sel}):', src)

# Also check data-onerror and lazyload 
for img in soup.select('img[data-onerror]'):
    src = img.get('src', '') or img.get('data-src', '')
    if src and 'nofoto' not in src and 'players' in src:
        print(f'PHOTO (data-onerror):', src)

# ===== BIRTHDATE =====
for sel in ['.personal-info', '.datos-personales', '.panel-body']:
    nodes = soup.select(sel)
    for n in nodes:
        txt = n.get_text()
        if 'Nacido' in txt or 'nacimiento' in txt.lower():
            print(f'BIRTHDATE SECTION ({sel}):', txt[:300])

# ===== POSITION =====
for sel in ['.pos-text', '.position', '.demarcacion', '.tag-position']:
    for n in soup.select(sel):
        print(f'POSITION ({sel}):', n.get_text(strip=True))

# ===== CAREER / SEASONS DATA =====
# Look for tables with season data
tables = soup.select('table')
for i, t in enumerate(tables):
    headers_row = t.select('th')
    header_texts = [th.get_text(strip=True) for th in headers_row]
    if any('temporada' in h.lower() or 'equipo' in h.lower() or 'season' in h.lower() for h in header_texts):
        print(f'\n=== CAREER TABLE {i} ===')
        print('HEADERS:', header_texts)
        for row in t.select('tr')[1:6]:  # first 5 data rows
            cells = [td.get_text(strip=True) for td in row.select('td')]
            print('ROW:', cells)

# Look for .historial-deportivo or similar
for sel in ['.historial-deportivo', '.career-history', '.trayectoria']:
    for n in soup.select(sel):
        print(f'\nCAREER ({sel}):', n.get_text(strip=True)[:500])

# Look for rendimiento section
for h2 in soup.select('h2'):
    txt = h2.get_text(strip=True)
    if 'rendimiento' in txt.lower() or 'trayectoria' in txt.lower() or 'carrera' in txt.lower():
        parent = h2.parent
        print(f'\nSECTION ({txt}):', parent.get_text(strip=True)[:500] if parent else 'No parent')

# Check for stats grid/boxes with match counts
for sel in ['.grid-table', '.player-stats-table', '.stats-season']:
    for n in soup.select(sel):
        txt = n.get_text(strip=True)
        if len(txt) > 10:
            print(f'\nSTATS ({sel}):', txt[:300])

# ===== DIRECT STAT NUMBERS =====
# Check .num or .stat-num
for sel in ['.num', '.stat-num', '.stat-value']:
    for n in soup.select(sel):
        print(f'STAT ({sel}):', n.get_text(strip=True))
