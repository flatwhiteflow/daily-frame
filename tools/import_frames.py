#!/usr/bin/env python3
"""Import finished batch PNGs without advancing the daily rotation.

Requires cwebp. Reimports corrected sources and refreshes their thumbnails.
Run with --dry-run to list the planned import without changing files.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'tools' / 'frame-sources.json'
RECIPE = 'cwebp-q95-m6-1672x941;thumb-q80-m6-640'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=Path.home() / 'Downloads')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.workers < 1:
        parser.error('--workers must be positive')
    sources = {}
    for batch in sorted(args.source.glob('Two of a Kind - Batch *')):
        for source in sorted(batch.glob('*.png')):
            match = re.fullmatch(r'(\d{2,3})-(.+)\.png', source.name)
            if not match:
                continue
            number = int(match[1])
            if number in sources:
                raise SystemExit(f'Duplicate source number {number}: {source}')
            sources[number] = (source, f'{number:03d}-{match[2]}.webp')
    if not sources:
        raise SystemExit('No numbered final PNGs found')
    missing = sorted(set(range(1, max(sources) + 1)) - sources.keys())
    if missing:
        raise SystemExit(f'Missing source numbers: {missing}')
    existing = {}
    for frame in (ROOT / 'frames').glob('*.webp'):
        match = re.match(r'^(\d+)-', frame.name)
        if match:
            existing.setdefault(int(match[1]), []).append(frame.name)
    for number, (_, target) in sources.items():
        conflicts = [name for name in existing.get(number, []) if name != target]
        if conflicts:
            raise SystemExit(f'Conflicting frame names for {number}: {conflicts}')
    old = json.loads(INDEX.read_text()) if INDEX.exists() else {}
    jobs, records = [], {}
    for number, (source, name) in sorted(sources.items()):
        frame, thumb = ROOT / 'frames' / name, ROOT / 'thumbs' / name
        record = {'source': f'{source.parent.name}/{source.name}',
                  'source_sha256': digest(source), 'recipe': RECIPE}
        cached = old.get(name, {})
        current = (all(cached.get(k) == v for k, v in record.items())
                   and frame.exists() and thumb.exists()
                   and cached.get('frame_sha256') == digest(frame)
                   and cached.get('thumb_sha256') == digest(thumb))
        if current:
            records[name] = cached
        else:
            jobs.append((source, name, record))
    print(f'{len(sources)} sources; {len(jobs)} to encode/check; '
          f'{len(records)} unchanged; {max(sources)} highest number', flush=True)
    if args.dry_run:
        return
    encoder = shutil.which('cwebp')
    if not encoder:
        raise SystemExit('cwebp missing; install with brew install webp')
    for directory in ('frames', 'thumbs'):
        (ROOT / directory).mkdir(exist_ok=True)

    def convert(job):
        source, name, record = job
        target, thumb = ROOT / 'frames' / name, ROOT / 'thumbs' / name
        with tempfile.TemporaryDirectory(prefix='daily-frame-') as temp:
            frame_tmp, thumb_tmp = Path(temp) / name, Path(temp) / 'thumb.webp'
            subprocess.run([encoder, '-quiet', '-q', '95', '-m', '6',
                            '-resize', '1672', '941', str(source),
                            '-o', str(frame_tmp)], check=True)
            changed = not target.exists() or digest(target) != digest(frame_tmp)
            if changed:
                shutil.copyfile(frame_tmp, target)
            cached_thumb = old.get(name, {}).get('thumb_sha256')
            if (changed or not thumb.exists()
                    or (cached_thumb is not None and digest(thumb) != cached_thumb)):
                subprocess.run([encoder, '-quiet', '-q', '80', '-m', '6',
                                '-resize', '640', '0', str(target),
                                '-o', str(thumb_tmp)], check=True)
                shutil.copyfile(thumb_tmp, thumb)
        record.update(frame_sha256=digest(target), thumb_sha256=digest(thumb))
        return name, record, changed

    changed_count = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for i, (name, record, changed) in enumerate(pool.map(convert, jobs), 1):
            records[name] = record
            changed_count += changed
            if i % 25 == 0 or i == len(jobs):
                print(f'Checked {i}/{len(jobs)}; updated {changed_count} frames', flush=True)
    INDEX.write_text(json.dumps(dict(sorted(records.items())), indent=2) + '\n')
    print(f'Imported {len(sources)} covers; updated {changed_count}. '
          'Daily state and history were not advanced.', flush=True)


if __name__ == '__main__':
    main()
