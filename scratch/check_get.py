import re

with open('app.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    matches = re.findall(r'(\b\w+)\.get\(', l)
    for m in matches:
        if m not in ('user', 'session_state', 'TRANSLATIONS', 'SLOT_HOUR_MAP', 'recs', 'kwargs', 'prices', 'curr_user'):
            print(f'Line {i+1}: variable "{m}" in: {l.strip()}')

