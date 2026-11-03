#!/usr/bin/env python3
"""Publishes today's seasonal pick or next unshown numbered frame.

state.json remembers which frame is next, so frames added later (higher numbers) come after the ones already shown.
Runs at most once a day (Dublin date); a second run on the same day does nothing. Standard library only.
"""
import argparse
import json, os, shutil
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://daily.fabiopetriccione.com'   # the custom domain: the old github.io address only redirects, and its redirect carries no CORS header
W, H = 1672, 941

def validate_schedule(schedule, frames):
    names = set(frames)
    for day, name in schedule.items():
        if datetime.strptime(day, '%Y-%m-%d').strftime('%Y-%m-%d') != day:
            raise ValueError(f'Invalid schedule date: {day}')
        if name not in names:
            raise ValueError(f'Scheduled frame does not exist: {day}: {name}')
    if len(set(schedule.values())) != len(schedule):
        raise ValueError('The dated playlist contains duplicate frames')


def choose_frame(frames, state, history, schedule, today):
    """Seasonal dates override the queue; the queue skips pictures already shown."""
    if not frames:
        raise ValueError('no frames in frames/')
    validate_schedule(schedule, frames)
    seen = {entry['file'] for entry in history}
    if state.get('file'):
        seen.add(state['file'])
    cursor = state.get('next', 0) % len(frames)
    planned = schedule.get(today)
    if planned and planned not in seen:
        return planned, cursor
    reserved = {name for day, name in schedule.items() if day > today}
    for offset in range(len(frames)):
        index = (cursor + offset) % len(frames)
        if frames[index] not in seen | reserved:
            return frames[index], (index + 1) % len(frames)
    # Start another cycle only after every unreserved picture has been shown.
    for offset in range(len(frames)):
        index = (cursor + offset) % len(frames)
        if frames[index] not in reserved:
            return frames[index], (index + 1) % len(frames)
    raise ValueError('Every frame is reserved for a future date')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run', action='store_true', help='Preview without changing any files')
    parser.add_argument('--date', help='Preview a Dublin date (requires --dry-run)')
    args = parser.parse_args()
    if args.date and not args.dry_run:
        parser.error('--date requires --dry-run')
    today = args.date or datetime.now(ZoneInfo('Europe/Dublin')).strftime('%Y-%m-%d')
    frames = sorted(f for f in os.listdir(os.path.join(ROOT, 'frames')) if f.lower().endswith('.webp'))
    state_path = os.path.join(ROOT, 'state.json')
    state = json.loads(Path(state_path).read_text()) if os.path.exists(state_path) else {'next': 0, 'date': '', 'file': ''}
    if state.get('date') == today:
        print('already done today:', state.get('file'))
        return
    history_path = os.path.join(ROOT, 'history.json')
    history = json.loads(Path(history_path).read_text()) if os.path.exists(history_path) else []
    schedule_path = os.path.join(ROOT, 'schedule.json')
    schedule = json.loads(Path(schedule_path).read_text()) if os.path.exists(schedule_path) else {}
    selected, next_index = choose_frame(frames, state, history, schedule, today)
    print(f'{today}: {selected}' + (' (preview only)' if args.dry_run else ''))
    if args.dry_run:
        return
    shutil.copyfile(os.path.join(ROOT, 'frames', selected), os.path.join(ROOT, 'latest.webp'))
    manifest = {'updated': today, 'photos': [{'url': SITE + '/latest.webp', 'w': W, 'h': H, 'date': today}]}
    Path(ROOT, 'manifest.json').write_text(json.dumps(manifest, indent=2))
    Path(state_path).write_text(json.dumps({'next': next_index, 'date': today, 'file': selected}, indent=2))
    # History contains only pictures actually shown, never upcoming dates.
    history.append({'date': today, 'file': selected})
    Path(history_path).write_text(json.dumps(history, indent=2))


if __name__ == '__main__':
    main()
