"""Build complete native road/path geometry without adopting operating defaults."""
import json

import city
from build.osm_way_geometry import build

OUTPUT_INPUTS = {
    'data/processed/network/road_geometry/nodes.csv': ['city.json#osm_network_inputs'],
    'data/processed/network/road_geometry/ways.csv': ['city.json#osm_network_inputs'],
    'data/processed/network/road_geometry/segments.csv': ['city.json#osm_network_inputs'],
    'data/processed/network/road_geometry/audit.json': ['city.json#osm_network_inputs'],
}


if __name__ == '__main__':
    print('Reading complete native road and path geometry', flush=True)
    report = build(city.network_osm_inputs(), city.path('data/processed/network/road_geometry'),
                   city.crs(), feature_key='highway')
    print(json.dumps(report), flush=True)
