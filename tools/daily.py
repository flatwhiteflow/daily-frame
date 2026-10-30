#!/usr/bin/env python3
"""Picks today's frame, one a day in numbered order, and publishes it as latest.webp + manifest.json.

state.json remembers which frame is next, so frames added later (higher numbers) come after the ones already shown.
Runs at most once a day (Dublin date); a second run on the same day does nothing. Standard library only.
"""
import json, os, shutil
from datetime import datetime
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://flatwhiteflow.github.io/daily-frame'
W, H = 1672, 941

today = datetime.now(ZoneInfo('Europe/Dublin')).strftime('%Y-%m-%d')
frames = sorted(f for f in os.listdir(os.path.join(ROOT, 'frames')) if f.lower().endswith('.webp'))
if not frames:
    raise SystemExit('no frames in frames/')

state_path = os.path.join(ROOT, 'state.json')
state = json.load(open(state_path)) if os.path.exists(state_path) else {'next': 0, 'date': '', 'file': ''}
if state.get('date') == today:
    print('already done today:', state.get('file'))
    raise SystemExit(0)

i = state.get('next', 0) % len(frames)
shutil.copyfile(os.path.join(ROOT, 'frames', frames[i]), os.path.join(ROOT, 'latest.webp'))
manifest = {'updated': today, 'photos': [{'url': SITE + '/latest.webp', 'w': W, 'h': H, 'date': today}]}
json.dump(manifest, open(os.path.join(ROOT, 'manifest.json'), 'w'), indent=2)
json.dump({'next': (i + 1) % len(frames), 'date': today, 'file': frames[i]}, open(state_path, 'w'), indent=2)
# history.json: every day shown, oldest first. The website shows the last one as today's and puts a day in its archive only once the next day has replaced it
history_path = os.path.join(ROOT, 'history.json')
history = json.load(open(history_path)) if os.path.exists(history_path) else []
history.append({'date': today, 'file': frames[i]})
json.dump(history, open(history_path, 'w'), indent=2)
print(f'{today}: {frames[i]} ({i + 1} of {len(frames)})')
