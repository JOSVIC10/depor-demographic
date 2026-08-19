"""
Create Supabase tables using the Management API.
"""
import requests
import json

SUPABASE_URL = "https://evphxfveswschcbivrkl.supabase.co"
# Using the anon key to call the REST API with a POST to /rest/v1/rpc if that's available
# But first, let's try with the service role approach via the DB direct connection

# Supabase anon key (already in the codebase)
ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2cGh4ZnZlc3dzY2hjYml2cmtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwMzcxNjksImV4cCI6MjEwMjYxMzE2OX0.WbC5XVgwaVXwnuOtl_91iwvZZkDa2pVX2d2Bo0nSt8Y"

headers = {
    "apikey": ANON_KEY,
    "Authorization": f"Bearer {ANON_KEY}",
    "Content-Type": "application/json",
}

# Test connection
print("Testing Supabase connection...")
r = requests.get(f"{SUPABASE_URL}/rest/v1/", headers=headers, timeout=10)
print(f"Status: {r.status_code}")
print(f"Response: {r.text[:500]}")

# Try listing tables
print("\nChecking if tables exist...")
for table in ["teams", "players", "matches", "lineup_entries", "substitutions"]:
    r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?select=id&limit=1", headers=headers, timeout=10)
    print(f"  {table}: {r.status_code} - {r.text[:100]}")
