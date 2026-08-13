import sys
sys.path.append("c:/Users/Jose Vicente/Desktop/Depor - Demographic")
from backend.scraper import scrape_besoccer_match

url = "https://www.besoccer.es/partido/st-pauli/deportivo/202729586/alineaciones"
res = scrape_besoccer_match(url)
print(res)
