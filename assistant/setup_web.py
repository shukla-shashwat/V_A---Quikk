# setup_web.py
"""Run this to create web directories"""
import os

base = r"D:\V_A\assistant"
dirs = [
    "web",
    "web/static",
    "web/static/css", 
    "web/static/js",
    "web/templates"
]

for d in dirs:
    path = os.path.join(base, d)
    os.makedirs(path, exist_ok=True)
    print(f"Created: {path}")

print("\nDone! Now run the assistant again.")
