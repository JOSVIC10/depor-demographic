"""
Script para descargar la foto correcta de Xabi Campos desde BeSoccer
y actualizar la base de datos.
"""
import sys
sys.path.insert(0, '.')
import requests
import sqlite3
import os

# La foto correcta de Xabi Campos encontrada en BeSoccer
XABI_CAMPOS_PHOTO_URL = "https://cdn.resfu.com/img_data/players/medium/3570447.jpg"

photos_dir = os.path.join('frontend', 'photos')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Referer': 'https://es.besoccer.com/',
}

print(f"Descargando foto correcta de Xabi Campos...")
print(f"URL: {XABI_CAMPOS_PHOTO_URL}")

try:
    r = requests.get(XABI_CAMPOS_PHOTO_URL, headers=headers, timeout=15)
    print(f"Status: {r.status_code}, Size: {len(r.content)} bytes")
    
    if r.status_code == 200 and len(r.content) > 1000:
        # Save the correct Xabi Campos photo
        photo_path = os.path.join(photos_dir, 'p_extra_xabicampos.jpeg')
        with open(photo_path, 'wb') as f:
            f.write(r.content)
        print(f"✅ Foto de Xabi Campos guardada correctamente: {photo_path}")
        print(f"   Tamaño: {len(r.content)} bytes")
    else:
        print(f"❌ Error descargando foto: status={r.status_code}")
except Exception as e:
    print(f"❌ Excepción: {e}")
    import traceback
    traceback.print_exc()

# Also verify the current state of the DB
print("\n=== Estado actual DB ===")
conn = sqlite3.connect('depor_demographic.db')
conn.row_factory = sqlite3.Row
c = conn.cursor()
c.execute("SELECT id, name, photo_url FROM players WHERE id='p_extra_xabicampos'")
row = c.fetchone()
if row:
    print(f"Player: {dict(row)}")
conn.close()
