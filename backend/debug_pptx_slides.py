import os
import zipfile
import re
from xml.etree import ElementTree as ET
import sqlite3
import unicodedata

def normalize(n):
    if not n: return ""
    return unicodedata.normalize('NFKD', n).encode('ASCII', 'ignore').decode('utf-8').lower().strip()

def inspect_pptx():
    pptx_path = r"C:\Users\Jose Vicente\Downloads\Pasaporte Jugador.pptx"
    if not os.path.exists(pptx_path):
        print("PPTX not found!")
        return

    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "depor_demographic.db"))
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT id, name, team_id FROM players")
    all_db_players = [dict(r) for r in c.fetchall()]
    conn.close()

    print(f"Total DB players across all teams: {len(all_db_players)}")

    with zipfile.ZipFile(pptx_path, 'r') as z:
        slide_files = [f for f in z.namelist() if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
        slide_files.sort(key=lambda x: int(re.search(r'\d+', x.split('/')[-1]).group()))

        print(f"Total PPTX slides: {len(slide_files)}")

        for slide_file in slide_files:
            s_num = re.search(r'\d+', slide_file.split('/')[-1]).group()
            slide_xml = z.read(slide_file)
            root = ET.fromstring(slide_xml)

            texts = [node.text for node in root.iter() if node.text and node.text.strip()]
            full_text = " ".join(texts)

            name_search = re.search(r'NOMBRE\|\s*([A-ZÁÉÍÓÚÑa-zàéíóúñ\s\-\.]+)', full_text)
            scraped_name = name_search.group(1).strip() if name_search else "UNKNOWN"
            scraped_name = re.split(r'Overview|Posicion|Season|CURRENT|International', scraped_name)[0].strip()

            # Find images in rels
            rels_file = f"ppt/slides/_rels/{os.path.basename(slide_file)}.rels"
            media_info = []
            if rels_file in z.namelist():
                rels_root = ET.fromstring(z.read(rels_file))
                for rel in rels_root.iter():
                    target = rel.attrib.get('Target', '')
                    if 'media/image' in target:
                        m_path = target.replace('../', 'ppt/')
                        if m_path in z.namelist():
                            sz = len(z.read(m_path))
                            media_info.append((m_path, sz))

            # Sort images by size descending
            media_info.sort(key=lambda x: x[1], reverse=True)

            print(f"Slide {s_num:2s}: Scraped Name: '{scraped_name[:30]:30s}' | Images: {len(media_info)} | Best Image: {media_info[0] if media_info else 'None'}")

if __name__ == "__main__":
    inspect_pptx()
