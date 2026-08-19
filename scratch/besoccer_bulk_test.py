"""
Test simple para verificar que BeSoccer devuelve fotos.
"""
import sys
sys.path.insert(0, '.')
from backend.scraper import scrape_besoccer_player
import json

test_urls = {
    "p_extra_xabicampos": "https://es.besoccer.com/jugador/xabi-campos/1124736",
    "p_depor_mella": "https://es.besoccer.com/jugador/david-mella/1074394",
}

for pid, url in test_urls.items():
    print(f"\n=== {pid} ===")
    print(f"URL: {url}")
    try:
        result = scrape_besoccer_player(url)
        if result.get("success"):
            p = result["player"]
            print(f"Name: {p.get('name')}")
            print(f"Photo: {p.get('photo_src_url')}")
            print(f"Birthdate: {p.get('birthdate')}")
            print(f"Position: {p.get('detailed_position')}")
            print(f"Seasons: {p.get('seasons_data', '')[:100]}")
        else:
            print(f"ERROR: {result.get('error')}")
    except Exception as e:
        print(f"EXCEPTION: {e}")
        import traceback
        traceback.print_exc()
