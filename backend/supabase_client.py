import os
import requests
from typing import List, Dict, Optional, Any

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://evphxfveswschcbivrkl.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV2cGh4ZnZlc3dzY2hjYml2cmtsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODcwMzcxNjksImV4cCI6MjEwMjYxMzE2OX0.WbC5XVgwaVXwnuOtl_91iwvZZkDa2pVX2d2Bo0nSt8Y")

class SupabaseSync:
    def __init__(self):
        self.url = SUPABASE_URL.rstrip('/')
        self.key = SUPABASE_KEY
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=minimal"
        }
        self._available = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            r = requests.get(f"{self.url}/rest/v1/teams?select=id&limit=1", headers=self.headers, timeout=4)
            self._available = (r.status_code == 200)
        except Exception:
            self._available = False
        return self._available

    def reset_availability(self):
        self._available = None

    def upsert(self, table: str, data: List[Dict[str, Any]]) -> bool:
        if not self.is_available() or not data:
            return False
        try:
            headers = {**self.headers, "Prefer": "resolution=merge-duplicates"}
            r = requests.post(f"{self.url}/rest/v1/{table}", headers=headers, json=data, timeout=5)
            return r.status_code in [200, 201]
        except Exception as e:
            print(f"[Supabase] Upsert error on {table}: {e}")
            return False

    def delete(self, table: str, key_field: str, key_val: Any) -> bool:
        if not self.is_available():
            return False
        try:
            r = requests.delete(f"{self.url}/rest/v1/{table}?{key_field}=eq.{key_val}", headers=self.headers, timeout=5)
            return r.status_code in [200, 204]
        except Exception as e:
            print(f"[Supabase] Delete error on {table}: {e}")
            return False

    def fetch_all(self, table: str) -> List[Dict[str, Any]]:
        if not self.is_available():
            return []
        try:
            r = requests.get(f"{self.url}/rest/v1/{table}?select=*", headers=self.headers, timeout=6)
            if r.status_code == 200:
                return r.json()
            return []
        except Exception as e:
            print(f"[Supabase] Fetch error on {table}: {e}")
            return []

supabase_sync = SupabaseSync()
