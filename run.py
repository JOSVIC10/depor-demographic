import os
import sys
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import uvicorn
from backend import database as db
from seed_data import seed

def main():
    print("Initializing SQLite Database and seeding default data...")
    db.init_db()
    
    # Seed default data if teams table is empty
    teams = db.get_teams()
    if not teams:
        seed()
        
    print("Starting Depor Demographic & Match Report Generator server...")
    print("Open your browser at: http://localhost:8000 or http://<TU_IP_LOCAL>:8000")
    
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
