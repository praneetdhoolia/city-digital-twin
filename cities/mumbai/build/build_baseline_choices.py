"""Prepare mode alternatives without changing the selected daily demand."""
import gzip
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import city
import registry
from build.enumerate_mode_plans import add_mode_alternatives
from build.extract_osm_network import fingerprint

OUTPUT_INPUTS = {
    'demand/baseline/plans_with_choices.xml.gz': [
        'demand/baseline/plans_with_freight.xml.gz', 'registry/RUN_baseline_smoke.json'],
    'data/processed/acquisition/baseline_choices.json': [
        'demand/baseline/plans_with_freight.xml.gz', 'registry/RUN_baseline_smoke.json'],
}


def main():
    cfg = registry.load()
    source = Path(city.path('demand/baseline/plans_with_freight.xml.gz'))
    with gzip.open(source, 'rb') as stream:
        population = ET.parse(stream).getroot()
    audit = add_mode_alternatives(population, cfg.get('RUN.smoke.subtourModeChoice.modes'))
    audit.update(source='derived_initial_choice_set_not_observed_mode_shares',
        input_sha256={path: fingerprint(Path(city.path(path)))
                      for path in OUTPUT_INPUTS['demand/baseline/plans_with_choices.xml.gz']},
        limitations=['Alternatives are unscored; only native execution can evaluate them.',
            'Each added alternative uses one eligible mode for the whole day; the original mixed-mode plan is retained.',
            'Subtour innovation can discover further mixed-mode combinations.',
            'Eligibility, household coherence and behaviour retain the provisional baseline limitations.',
            'No mode share or ridership observation determines these alternatives.'])
    output = Path(city.path('demand/baseline/plans_with_choices.xml.gz'))
    with output.open('wb') as raw:
        with gzip.GzipFile(fileobj=raw, mode='wb', filename='', mtime=0) as stream:
            stream.write(b'<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n')
            stream.write(ET.tostring(population, encoding='utf-8'))
    Path(city.path('data/processed/acquisition/baseline_choices.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
