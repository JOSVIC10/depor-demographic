import sqlite3
import re

db_path = 'depor_demographic.db'

def fix_seasons_data():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, name, seasons_data FROM players WHERE seasons_data IS NOT NULL")
    players = cursor.fetchall()
    
    updated_count = 0
    for p_id, p_name, seasons_data in players:
        if '(90 partidos)' in seasons_data:
            new_lines = []
            for line in seasons_data.split('\n'):
                match = re.search(r"(\d+)'\s*mins\s*\(90\s*partidos\)", line)
                if match:
                    mins = int(match.group(1))
                    real_games = max(1, round(mins / 90.0))
                    new_line = line.replace("(90 partidos)", f"({real_games} partidos)")
                    new_lines.append(new_line)
                else:
                    new_lines.append(line)
            
            new_data = '\n'.join(new_lines)
            if new_data != seasons_data:
                cursor.execute("UPDATE players SET seasons_data = ? WHERE id = ?", (new_data, p_id))
                print(f"Corregido {p_name}")
                updated_count += 1
                
    conn.commit()
    conn.close()
    print(f"✅ Se han corregido {updated_count} jugadores en la base de datos.")

if __name__ == "__main__":
    fix_seasons_data()
