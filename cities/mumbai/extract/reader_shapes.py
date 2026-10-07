#!/usr/bin/env python
"""Mumbai's reader-shape adapter (config/schema/reader_shapes.json).

One family so far: `residents` - where a synthesised person lives and which
zones are the target area. The population table (build_population.py) keys a
person's home by `geography_id`, the census leaf id `city.json` declares as
the zone system's id column, and the target area is the `core` tier of
`data/processed/zones/mmr_extent.csv` (D13), the notified Mumbai Metropolitan
Region the CTS mode split describes. The census, HTS and count families are
not adapted: this city's demand is synthesised by its own builders and its
targets are derived by build_mode_targets.py.
"""
import city as _city


def residents_shape():
    """The residents map's inputs, in this city's vocabulary (see the schema)."""
    zone = _city.descriptor()['zone_system']['id_column']
    return dict(population='demand/population/B1_synthetic_population.csv',
                person_id='person_id', home_zone=zone,
                zone_areas='data/processed/zones/mmr_extent.csv',
                zone=zone, area='tier', target='core',
                map_columns=('person_id', zone, 'tier'))
