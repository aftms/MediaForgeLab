"""Bounded local playback checkpoints. No URLs, titles, credentials or free text."""
import json
from pathlib import Path
import re
import threading
import time

STAGES = {'boot', 'seek_call', 'seek_return', 'seek_rejected',
          'position_call', 'position_return', 'seek_done', 'seek_timeout', 'native_event', 'back'}
NUMBERS = {'revision': (12, 1000), 'seq': (1, 10000000), 'target': (0, 604800),
           'position': (-1, 604800), 'duration': (0, 604800), 'event': (0, 65535)}


def validate(data):
    if not isinstance(data, dict) or set(data) - (set(NUMBERS) | {'session', 'stage', 'id', 'native'}):
        raise ValueError('Invalid diagnostic')
    if data.get('stage') not in STAGES or not re.fullmatch(r'[a-z0-9-]{1,48}', str(data.get('session', ''))):
        raise ValueError('Invalid checkpoint')
    if not {'revision', 'seq'} <= set(data):
        raise ValueError('Missing revision')
    for key, (low, high) in NUMBERS.items():
        if key in data and (type(data[key]) is not int or not low <= data[key] <= high):
            raise ValueError('Invalid number')
    if 'id' in data and not re.fullmatch(r'(?:[me]?[0-9]{1,20})?', str(data['id'])):
        raise ValueError('Invalid item')
    if 'native' in data and type(data['native']) is not bool:
        raise ValueError('Invalid player')
    return dict(data)


class PlaybackDiagnostics:
    def __init__(self, path):
        self.path = Path(path)
        self.lock = threading.Lock()
        self.rows = []
        try:
            if self.path.stat().st_size <= 131072:
                for saved in json.loads(self.path.read_text(encoding='utf-8'))[-128:]:
                    received = saved.get('received')
                    row = validate({k:v for k,v in saved.items() if k != 'received'})
                    if type(received) is int and received >= 0:
                        self.rows.append(dict(row, received=received))
        except (OSError,ValueError,TypeError,AttributeError):
            self.rows = []

    def append(self, data):
        row = validate(data)
        row['received'] = int(time.time())
        with self.lock:
            updated = (self.rows + [row])[-128:]
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temp = self.path.with_suffix('.tmp')
            temp.write_text(json.dumps(updated, separators=(',', ':')), encoding='utf-8')
            temp.replace(self.path)
            self.rows = updated

    def read(self):
        with self.lock:
            return {'events': list(self.rows)}
