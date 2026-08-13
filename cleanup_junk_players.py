import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "depor_demographic.db")

# Exact names of legitimate Deportivo players from seed_data.py
valid_depor_names = {
    "Germán Parreño", "Leo Román", "Álvaro Ferllo", "Eric Puerto",
    "Arnau Comas", "Dani Barcia", "Lucas Noubi", "Bright Ede",
    "Ximo Navarro", "Giacomo Quagliata", "Miguel Loureiro", "Angeliño", "Adrià Altimira",
    "Diego Villares", "José Ángel Jurado", "Riki Rodríguez", "Lorenzo Amatucci",
    "Charlie Patiño", "Mario Soriano", "Jairo Noriega", "Noé Carrillo",
    "Teun Gijselhart", "Jonathan Asp Jensen",
    "Yeremay Hernández", "Luismi Cruz", "David Mella",
    "Pierre-Emerick Aubameyang", "Zakaria Eddahchouri", "Bil Nsongo", "Kevin Sánchez"
}

def clean_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # 1. Get all players in depor
    c.execute("SELECT id, name FROM players WHERE team_id = 'depor'")
    all_depor_players = c.fetchall()
    
    deleted_count = 0
    for p_id, name in all_depor_players:
        if name not in valid_depor_names:
            c.execute("DELETE FROM players WHERE id = ?", (p_id,))
            deleted_count += 1
            print(f"Borrando jugador: {name}")
            
    conn.commit()
    conn.close()
    print(f"\nLimpieza completada: {deleted_count} jugadores eliminados de la base de datos.")

if __name__ == "__main__":
    clean_db()
