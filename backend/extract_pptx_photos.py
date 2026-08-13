import os
import zipfile
import re
from xml.etree import ElementTree as ET
import sqlite3
import unicodedata

def normalize_name(n):
    if not n: return ""
    return unicodedata.normalize('NFKD', n).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def match_player(scraped_name, db_players):
    s_norm = normalize_name(scraped_name)
    for p in db_players:
        p_norm = normalize_name(p['name'])
        if s_norm == p_norm or s_norm in p_norm or p_norm in s_norm:
            return p
    # Try matching last name
    s_words = s_norm.split()
    if s_words:
        s_last = s_words[-1]
        for p in db_players:
            p_words = normalize_name(p['name']).split()
            if len(s_last) >= 3 and s_last in p_words:
                return p
    return None

def process_pptx():
    pptx_path = r"C:\Users\Jose Vicente\Downloads\Pasaporte Jugador.pptx"
    if not os.path.exists(pptx_path):
        print(f"PPTX file not found at {pptx_path}")
        return

    output_photos_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "photos"))
    os.makedirs(output_photos_dir, exist_ok=True)

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "depor_demographic.db"))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM players WHERE team_id = 'depor'")
    db_players = [dict(r) for r in c.fetchall()]

    print(f"Loaded {len(db_players)} DB players for depor.")

    with zipfile.ZipFile(pptx_path, 'r') as z:
        # Find all slide files
        slide_files = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
        # Sort slides numerically: slide1.xml, slide2.xml, ...
        slide_files.sort(key=lambda x: int(re.search(r'\d+', x.split('/')[-1]).group()))

        updated_count = 0
        for slide_file in slide_files:
            slide_num = re.search(r'\d+', slide_file.split('/')[-1]).group()
            slide_xml = z.read(slide_file)
            root = ET.fromstring(slide_xml)

            # Extract all text in slide
            texts = [node.text for node in root.iter() if node.text and node.text.strip()]
            full_text = " ".join(texts)

            # Check if there's a player name header like "NOMBRE| LEO ROMÁN"
            name_match = re.search(r'NOMBRE\|\s*([A-ZÁÉÍÓÚÑa-zàéíóúñ\s\-\.]+)', full_text)
            if not name_match:
                continue

            raw_name = name_match.group(1).strip()
            # Clean up trailing words like Overview, Posicion, etc.
            raw_name = re.split(r'Overview|Posicion|Season|CURRENT', raw_name, flags=re.IGNORECASE)[0].strip()

            player = match_player(raw_name, db_players)
            if not player:
                print(f"Slide {slide_num}: No DB match for '{raw_name}'")
                continue

            # Look for rels to find image
            rels_file = f"ppt/slides/_rels/{os.path.basename(slide_file)}.rels"
            if rels_file not in z.namelist():
                continue

            rels_xml = z.read(rels_file)
            rels_root = ET.fromstring(rels_xml)

            img_rel_target = None
            for rel in rels_root.iter():
                target = rel.attrib.get('Target', '')
                if 'media/image' in target:
                    # In slides with multiple images (logo, pitch icon, photo), the player photo is usually image1 or largest image
                    # Let's inspect media targets for this slide
                    img_rel_target = target.replace('../', 'ppt/')
                    break

            if img_rel_target and img_rel_target in z.namelist():
                ext = os.path.splitext(img_rel_target)[1]
                saved_filename = f"{player['id']}{ext}"
                saved_filepath = os.path.join(output_photos_dir, saved_filename)

                with z.open(img_rel_target) as img_in, open(saved_filepath, 'wb') as img_out:
                    img_out.write(img_in.read())

                photo_url = f"/static/photos/{saved_filename}"
                c.execute("UPDATE players SET photo_url = ? WHERE id = ?", (photo_url, player['id']))
                updated_count += 1
                print(f"SUCCESS: Assigned photo for {player['name']} -> {photo_url}")

    conn.commit()
    conn.close()
    print(f"\nDone! Updated {updated_count} players with photos.")

if __name__ == "__main__":
    process_pptx()
