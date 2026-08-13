import py_compile
import sys

try:
    py_compile.compile("c:/Users/Jose Vicente/Desktop/Depor - Demographic/backend/scraper.py", doraise=True)
    print("Syntax OK")
except Exception as e:
    print(f"Syntax Error: {e}")
