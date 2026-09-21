"""The CSV and JSON plumbing every evidence builder in this directory shares.

Five harbour-line builders and three road-evidence builders each carried
their own byte-identical `read`, `serial`, `digest` and `dump` (21 September
2026); one copy lives here. City-relative paths throughout, as everywhere.
"""
import csv
import hashlib
import json
from pathlib import Path

import city
from manifest_io import manifest_reader


def read_rows(path):
    """Every row of a city-relative CSV, through the manifest-sized reader."""
    with Path(city.path(path)).open(encoding='utf-8') as stream:
        return list(manifest_reader(stream))


def serial(value):
    """One canonical JSON spelling of a value, for hashing and cell storage."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def digest(path):
    return hashlib.sha256(Path(city.path(path)).read_bytes()).hexdigest()


def dump_rows(path, rows, what='evidence'):
    """Write rows to a city-relative CSV (LF, header from the first row);
    an empty table is refused, because an evidence file with no rows is a
    claim nobody made."""
    if not rows:
        raise ValueError('Expected nonempty %s: %s' % (what, path))
    target = Path(city.path(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
