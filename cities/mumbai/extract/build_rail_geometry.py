"""Build native railway segment evidence using the portable geometry reader."""
import json
import city
from build.osm_rail_geometry import build

OUTPUT_INPUTS = {
    'data/processed/network/rail_geometry/nodes.csv': ['city.json#osm_network_inputs'],
    'data/processed/network/rail_geometry/ways.csv': ['city.json#osm_network_inputs'],
    'data/processed/network/rail_geometry/segments.csv': ['city.json#osm_network_inputs'],
    'data/processed/network/rail_geometry/audit.json': ['city.json#osm_network_inputs'],
}


if __name__ == '__main__':
    print('Reading complete native railway geometry', flush=True)
    result = build(city.network_osm_inputs(), city.path('data/processed/network/rail_geometry'), city.crs())
    print(json.dumps(result))
