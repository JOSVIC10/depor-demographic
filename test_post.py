import sys
import requests

url = "http://127.0.0.1:8000/api/matches/202712030/import"
payload = {
    "url": "https://es.besoccer.com/partido/fiorentina/deportivo/202712030/alineaciones",
    "create_unknowns": False,
    "ignore_unknowns": False
}

try:
    res = requests.post(url, json=payload)
    print("Status:", res.status_code)
    print("Response:", res.text)
except Exception as e:
    print("Error:", e)
