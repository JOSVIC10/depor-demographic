import sys
import os

sys.path.insert(0, r"c:\Users\Jose Vicente\Desktop\Depor - Demographic")
from backend.main import is_match

print("Test 1:", is_match("P. Aubameyang", "Pierre-Emerick Aubameyang"))
print("Test 2:", is_match("B. Ede", "Bright Ede"))
print("Test 3:", is_match("Álvaro Ferllo", "Álvaro Ferllo"))
print("Test 4:", is_match("Noé Carrillo", "Noé Carrillo"))
print("Test 5:", is_match("Z. Eddahchouri", "Zakaria Eddahchouri"))
print("Test 6:", is_match("Lucas Noubi", "Lucas Noubi"))
print("Test 7:", is_match("T. Gijselhart", "T. Gijselhart"))

from backend import database as db
conn = db.get_connection()
c = conn.cursor()
c.execute("SELECT name FROM players WHERE team_id = 'depor'")
players = [row['name'] for row in c.fetchall()]

print("Depor players in DB:", players)
