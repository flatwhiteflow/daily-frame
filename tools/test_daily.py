import contextlib
from datetime import date, datetime, timedelta
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('daily', Path(__file__).with_name('daily.py'))
daily = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(daily)


class SeasonalPickerTests(unittest.TestCase):
    def test_entire_season_then_return_to_unshown_queue(self):
        root = Path(daily.ROOT)
        frames = sorted(p.name for p in (root / 'frames').glob('*.webp'))
        schedule = json.loads((root / 'schedule.json').read_text())
        state = {'next': 6, 'date': '2026-11-03', 'file': '005-artsy-paws.webp'}
        history = [{'file': name} for name in frames[:6]]
        start = date(2026, 11, 4)
        self.assertEqual(len(schedule), 58)
        for offset in range(58):
            day = (start + timedelta(days=offset)).isoformat()
            name, cursor = daily.choose_frame(frames, state, history, schedule, day)
            self.assertEqual(name, schedule[day])
            self.assertNotIn(name, {entry['file'] for entry in history})
            self.assertEqual(cursor, 6)
            history.append({'date': day, 'file': name})
            state.update(next=cursor, date=day, file=name)
        name, cursor = daily.choose_frame(frames, state, history, schedule, '2027-01-01')
        self.assertEqual(name, '006-at-ease.webp')
        history.append({'file': name})
        state.update(next=cursor, file=name)
        name, _ = daily.choose_frame(frames, state, history, schedule, '2027-01-02')
        self.assertEqual(name, '016-bagel-break.webp')

    def test_fallback_reserves_future_frames_and_skips_seen(self):
        frames = ['a.webp', 'b.webp', 'c.webp']
        schedule = {'2026-12-01': 'a.webp'}
        name, _ = daily.choose_frame(frames, {'next': 0}, [{'file': 'b.webp'}], schedule, '2026-11-03')
        self.assertEqual(name, 'c.webp')
        # An already-shown scheduled image must not repeat that day.
        name, _ = daily.choose_frame(frames, {'next': 0}, [{'file': 'a.webp'}], schedule, '2026-12-01')
        self.assertEqual(name, 'b.webp')

    def test_invalid_schedule_fails_before_publishing(self):
        with self.assertRaises(ValueError):
            daily.choose_frame(['a.webp'], {}, [], {'2026-12-01': 'missing.webp'}, '2026-11-04')
        with self.assertRaises(ValueError):
            daily.validate_schedule({'2026-12-01': 'a.webp', '2026-12-02': 'a.webp'}, ['a.webp'])

    def test_publish_once_and_preview_without_mutation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'frames').mkdir()
            (root / 'frames' / 'a.webp').write_bytes(b'old frame')
            (root / 'frames' / 'b.webp').write_bytes(b'seasonal frame')
            (root / 'state.json').write_text(json.dumps({'next': 0, 'date': '2026-11-03', 'file': 'a.webp'}))
            (root / 'history.json').write_text(json.dumps([{'date': '2026-11-03', 'file': 'a.webp'}]))
            (root / 'schedule.json').write_text(json.dumps({'2026-11-04': 'b.webp'}))
            before = {p.name: p.read_bytes() for p in root.glob('*.json')}
            with patch.object(daily, 'ROOT', temp), contextlib.redirect_stdout(io.StringIO()):
                with patch('sys.argv', ['daily.py', '--dry-run', '--date', '2026-11-04']):
                    daily.main()
                self.assertEqual(before, {p.name: p.read_bytes() for p in root.glob('*.json')})
                self.assertFalse((root / 'latest.webp').exists())
                with patch.object(daily, 'datetime', wraps=datetime) as clock:
                    clock.now.return_value = datetime(2026, 11, 4, 0, 10)
                    with patch('sys.argv', ['daily.py']):
                        daily.main()
                        daily.main()
                    self.assertEqual(clock.now.call_args.args[0].key, 'Europe/Dublin')
                self.assertEqual((root / 'latest.webp').read_bytes(), b'seasonal frame')
                self.assertEqual(len(json.loads((root / 'history.json').read_text())), 2)
                state = json.loads((root / 'state.json').read_text())
                self.assertEqual(state['next'], 0)
                self.assertEqual(state['file'], 'b.webp')
                manifest = json.loads((root / 'manifest.json').read_text())
                self.assertEqual(manifest['photos'][0]['url'], daily.SITE + '/latest.webp')


if __name__ == '__main__':
    unittest.main()
