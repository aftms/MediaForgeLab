"""Private staged file transactions shared by catalog and refresh."""
import json
import os
from pathlib import Path
import shutil
import uuid


def json_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return default


def recover(journal):
    """An unfinished transaction always rolls back before loading the catalog."""
    entries = read_json(journal, [])
    for entry in entries:
        target, backup = Path(entry['target']), Path(entry['backup'])
        if entry['existed']:
            if backup.exists():
                shutil.copyfile(backup, target)
        elif target.exists():
            target.unlink()
    if entries:
        Path(journal).unlink(missing_ok=True)
        for entry in entries:
            Path(entry['backup']).unlink(missing_ok=True)
            Path(entry['temp']).unlink(missing_ok=True)


def atomic_batch(files, journal, validator=None, replace=os.replace):
    """Stage, validate, back up, journal, replace; rollback on any failed replace."""
    journal = Path(journal)
    journal.parent.mkdir(parents=True, exist_ok=True)
    recover(journal)
    entries = []
    try:
        for path, content in files.items():
            target = Path(path)
            target.parent.mkdir(parents=True, exist_ok=True)
            suffix = '.portal-' + uuid.uuid4().hex
            temp, backup = Path(str(target)+suffix+'.tmp'), Path(str(target)+suffix+'.bak')
            entry = dict(target=str(target), temp=str(temp), backup=str(backup), existed=target.exists())
            entries.append(entry)
            with temp.open('wb') as output:
                output.write(content)
                output.flush()
                os.fsync(output.fileno())
            if temp.read_bytes() != content:
                raise ValueError('Staged file mismatch')
            if validator:
                validator(target, temp)
            if entry['existed']:
                shutil.copyfile(target, backup)
        with journal.open('wb') as output:
            output.write(json_bytes(entries))
            output.flush()
            os.fsync(output.fileno())
        for entry in entries:
            replace(entry['temp'], entry['target'])
        journal.unlink()
    except Exception:
        if journal.exists():
            recover(journal)
        raise
    finally:
        # Keep backups if rollback itself failed; next startup can recover.
        if not journal.exists():
            for entry in entries:
                Path(entry['temp']).unlink(missing_ok=True)
                Path(entry['backup']).unlink(missing_ok=True)
