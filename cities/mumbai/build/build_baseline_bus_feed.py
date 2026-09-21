"""Stage the acquired community bus feed for the provisional broad baseline."""
import hashlib
import json
from pathlib import Path
import shutil

import city

OUTPUT_INPUTS = {
    'schedules/baseline_bus.zip': ['data/raw/transit/bus_gtfs_20260918_*.zip'],
}


def main():
    record = json.loads(Path(city.path('data/raw/transit/provenance_bus_gtfs_20260918.json'))
                        .read_text(encoding='utf-8'))['files'][0]
    incoming = Path(city.path(record['path']))
    with incoming.open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != record['sha256']:
            raise ValueError('Source bus feed changed')
    output = Path(city.path('schedules/baseline_bus.zip'))
    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(incoming, output)
    print('Staged community schedule; operational accuracy remains provisional:', city.rel(str(output)))


if __name__ == '__main__':
    main()
