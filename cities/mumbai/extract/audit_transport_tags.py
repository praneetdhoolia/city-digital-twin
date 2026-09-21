"""Measure the retained native tags before selecting physical model parameters."""
from pathlib import Path
import json

import city
from build.audit_osm_transport_tags import audit, write

OUTPUT_INPUTS = {
    'data/processed/acquisition/network_source/transport_tag_values.csv': [
        'city.json#osm_network_inputs'],
    'data/processed/acquisition/network_source/transport_tag_audit.json': [
        'city.json#osm_network_inputs'],
}


def main():
    inputs = city.network_osm_inputs()
    report, rows = audit(inputs)
    report['inputs'] = [Path(path).relative_to(city.CITY_DIR).as_posix() for path in inputs]
    write(report, rows, city.path('data/processed/acquisition/network_source'))
    print(json.dumps({key: report[key] for key in (
        'counts', 'unique_source_ways', 'linear_transport_ways', 'histogram_rows')}))


if __name__ == '__main__':
    main()
