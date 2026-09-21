"""Which census leaves the notified Mumbai Metropolitan Region takes (D13, 9.204).

The package holds the four Census 2011 districts Mumbai, Mumbai Suburban,
Thane (with today's Palghar) and Raigad - the acquisition's overcoverage. The
user's decision D13 (21 September 2026) makes the notified MMR the CORE and
the four-district remainder the EXTERNAL tier. This step derives, leaf by
leaf, which tier each of the 4,813 census leaves belongs to, from the public
lists that state the region's membership, and writes the derivation with its
evidence:

  * `greater_mumbai`      every ward of Greater Mumbai (M Corp.), the two
                          districts 518 and 519 - the region's core by every
                          notification;
  * `wri_municipality`    a ward of a municipal corporation or council the
                          public MMR GIS names (WRI layers 3 and 2), matched
                          on the normalised town name with the declared
                          spelling aliases (A.extent.municipal_name_aliases);
  * `wri_village_code`    a village or census town whose 2011 code appears in
                          the public MMR GIS villages layer (WRI layer 5,
                          F2011_ID) - an exact code join, never a name;
  * `ena_2024_village`    a village named, with its taluka, in the MMR
                          extended-notified-area SPA notification of 9 July
                          2024 - a normalised name match inside the taluka,
                          every match and every miss listed;
  * `external`            everything else in the four districts.

A leaf that carries a source polygon is also tested against the public MMR
boundary polygon (WRI layer 1): the audit reports, per rule, how many
centroids fall inside it. That is a CHECK on the lists, not a rule - the
polygon is evidence-only (arcgis_boundary_audit.json) and omits Palghar.

Nothing is apportioned: a leaf is wholly core or wholly external, as the
census publishes it. The 2019 extension notification itself is a scanned PDF
whose village list has not been transcribed; the 2024 SPA list is the later
statement of the same extended area and is what this step reads.
"""
from collections import Counter, defaultdict
import csv
import glob
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import zipfile

import geopandas as gpd
import pyogrio
import shapely

import city
import registry

# the sibling adapter that verifies a raw source against its provenance record,
# reached by path so the module imports wherever the caller runs from
_spec = importlib.util.spec_from_file_location(
    'extract_census_controls', Path(__file__).with_name('extract_census_controls.py'))
_controls = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_controls)
source = _controls.source

OUTPUT_INPUTS = {
    'data/processed/zones/mmr_extent.csv': [
        'data/processed/observed/census_2011_leaf_controls.csv',
        'data/processed/geospatial/census_2011_geographies.gpkg',
        'data/processed/observed/mmr_ena_villages_2024.csv',
        'data/raw/boundaries/wri_mmr_layer_1_*.json',
        'data/raw/boundaries/wri_mmr_layer_2_*.json',
        'data/raw/boundaries/wri_mmr_layer_3_*.json',
        'data/raw/boundaries/wri_mmr_layer_5_*.json',
        'data/raw/boundaries/iitb_boundary_*.zip',
        'registry/A_extent.json'],
    'data/processed/acquisition/mmr_extent_audit.json': [
        'data/processed/observed/census_2011_leaf_controls.csv',
        'data/processed/geospatial/census_2011_geographies.gpkg',
        'data/processed/observed/mmr_ena_villages_2024.csv',
        'data/raw/boundaries/wri_mmr_layer_1_*.json',
        'data/raw/boundaries/wri_mmr_layer_2_*.json',
        'data/raw/boundaries/wri_mmr_layer_3_*.json',
        'data/raw/boundaries/wri_mmr_layer_5_*.json',
        'data/raw/boundaries/iitb_boundary_*.zip',
        'registry/A_extent.json'],
}
CONTROLS = 'data/processed/observed/census_2011_leaf_controls.csv'
GEOGRAPHIES = 'data/processed/geospatial/census_2011_geographies.gpkg'
ENA = 'data/processed/observed/mmr_ena_villages_2024.csv'
OUT = 'data/processed/zones/mmr_extent.csv'
AUDIT = 'data/processed/acquisition/mmr_extent_audit.json'
GREATER_MUMBAI_DISTRICTS = ('518', '519')     # Mumbai City and Mumbai Suburban, Census 2011


def normal(value):
    """Only case, punctuation and whitespace; never a fuzzy substitution."""
    return re.sub(r'[^a-z0-9]', '', str(value).lower())


def town_name(leaf_name):
    """The census town a ward row belongs to, without its printed type suffix."""
    name = leaf_name.split(' WARD NO.')[0]
    name = re.sub(r'\((CT|M Cl|M Corp\.?|N\.?V\.?|Part)\)', '', name, flags=re.I)
    return name.strip()


def digest(path):
    with open(path, 'rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def wri(layer, records):
    sid = 'wri_mmr_layer_%d_features' % layer
    record, path = source(sid, 'boundaries')
    records.append(dict(source_id=sid, sha256=record['sha256']))
    payload = json.loads(path.read_text(encoding='utf-8'))
    if 'error' in payload or payload.get('exceededTransferLimit'):
        raise ValueError('Incomplete feature query: ' + sid)
    return payload


def taluka_names(records):
    """subdistrict code -> taluka name, from the IIT Bombay district layers."""
    names = {}
    for zip_path in sorted(glob.glob(city.path('data/raw/boundaries/iitb_boundary_*.zip'))):
        prov = Path(zip_path).parent / ('provenance_%s.json' % Path(zip_path).stem.rsplit('_', 1)[0])
        if not prov.exists():
            continue
        record = json.loads(prov.read_text(encoding='utf-8'))['files'][0]
        if digest(zip_path) != record['sha256']:
            raise ValueError('Source hash mismatch: ' + zip_path)
        for member in zipfile.ZipFile(zip_path).namelist():
            if not member.endswith('.shp'):
                continue
            frame = pyogrio.read_dataframe('zip://%s!%s' % (zip_path, member), read_geometry=False)
            if 'taluka_cod' not in frame.columns:
                continue
            records.append(dict(source_id=Path(zip_path).stem.rsplit('_', 1)[0], sha256=record['sha256']))
            for code, name in zip(frame['taluka_cod'], frame['taluka_nam']):
                names[str(code).zfill(5)] = normal(name)
    if not names:
        raise SystemExit('no taluka layer with taluka_cod/taluka_nam under data/raw/boundaries')
    return names


def main():
    cfg = registry.load()
    aliases = {normal(k): normal(v) for k, v in cfg.get('A.extent.municipal_name_aliases').items()}
    records = []
    leaves = list(csv.DictReader(open(city.path(CONTROLS), encoding='utf-8')))
    records.append(dict(source_id='census_2011_leaf_controls', sha256=digest(city.path(CONTROLS))))

    # the public GIS's named municipalities (layers 3 and 2) and its villages by code (layer 5)
    municipal = {}
    for layer, kind in ((3, 'municipal_corporation'), (2, 'municipal_council')):
        for f in wri(layer, records)['features']:
            name = normal(f['attributes']['Name'])
            municipal[aliases.get(name, name)] = kind
    village_codes = {}
    for f in wri(5, records)['features']:
        a = f['attributes']
        village_codes[str(a['F2011_ID'])] = dict(name=a['NAME'].strip(), taluka=a['SUB_DIST'])
    # the public MMR boundary polygon, for the check only
    boundary_payload = wri(1, records)
    rings = boundary_payload['features'][0]['geometry']['rings']
    boundary = shapely.MultiPolygon([shapely.Polygon(r) for r in rings]) if len(rings) > 1 \
        else shapely.Polygon(rings[0])
    boundary = gpd.GeoSeries([shapely.make_valid(boundary)], crs=4326).to_crs(city.crs()).iloc[0]

    # the 2024 extended-area village list, by normalised (taluka, name)
    talukas = taluka_names(records)
    ena_rows = list(csv.DictReader(open(city.path(ENA), encoding='utf-8')))
    records.append(dict(source_id='mmr_ena_villages_2024', sha256=digest(city.path(ENA))))
    village_aliases = {tuple(k.split('/', 1)): normal(v)
                       for k, v in cfg.get('A.extent.village_name_aliases').items()}
    ena = defaultdict(list)
    for r in ena_rows:
        # the notification prints the census type suffix ((CT), (N.V.)) as the census does
        key = (normal(r['taluka_name']), normal(town_name(r['village_name'])))
        key = (key[0], village_aliases.get(key, key[1]))      # the declared transliterations
        ena[key].append(r['serial_number'])

    # centroids of the leaves that carry a polygon
    geo = pyogrio.read_dataframe(city.path(GEOGRAPHIES), layer='census_leaves',
                                 columns=['geography_id'])
    geo = geo[geo.geometry.notna() & ~geo.geometry.is_empty]
    inside = dict(zip(geo['geography_id'], geo.geometry.representative_point().within(boundary)))

    rows = []
    rule_counts = Counter()
    persons = Counter()
    check = defaultdict(Counter)
    ena_matched = set()
    for leaf in leaves:
        code = leaf['town_village_code']
        rule, evidence = 'external', 'in the four districts, named by no MMR list'
        if leaf['district_code'] in GREATER_MUMBAI_DISTRICTS:
            rule, evidence = 'greater_mumbai', 'Census 2011 district %s' % leaf['district_code']
        elif leaf['level'] == 'WARD' and normal(town_name(leaf['name'])) in municipal:
            key = normal(town_name(leaf['name']))
            rule, evidence = 'wri_municipality', '%s %r (WRI layer %s)' % (
                municipal[key], town_name(leaf['name']), '3' if municipal[key] == 'municipal_corporation' else '2')
        elif code in village_codes:
            rule, evidence = 'wri_village_code', 'F2011_ID %s %r, %s (WRI layer 5)' % (
                code, village_codes[code]['name'], village_codes[code]['taluka'])
        else:
            key = (talukas.get(leaf['subdistrict_code'], ''), normal(town_name(leaf['name'])))
            if key in ena:
                rule, evidence = 'ena_2024_village', 'serial %s of the 9 July 2024 SPA notification' % (
                    ','.join(ena[key]))
                ena_matched.add(key)
        key = (talukas.get(leaf['subdistrict_code'], ''), normal(town_name(leaf['name'])))
        if key in ena:
            ena_matched.add(key)          # named by the list, whichever rule reached it first
        tier = 'external' if rule == 'external' else 'core'
        rows.append(dict(geography_id=leaf['geography_id'], district_code=leaf['district_code'],
                         subdistrict_code=leaf['subdistrict_code'], level=leaf['level'],
                         name=leaf['name'], tier=tier, rule=rule, evidence=evidence,
                         persons_count=leaf['persons_count'], households_count=leaf['households_count']))
        rule_counts[rule] += 1
        persons[tier] += int(leaf['persons_count'])
        persons[rule] += int(leaf['persons_count'])
        if leaf['geography_id'] in inside:
            check[rule]['inside_public_boundary' if inside[leaf['geography_id']] else 'outside_public_boundary'] += 1
        else:
            check[rule]['no_polygon'] += 1

    # an unmatched notification name is listed with the census names in its
    # taluka that resemble it - CANDIDATES for a person to confirm against the
    # village directory, never a match this step makes
    import difflib                                                # noqa: PLC0415
    by_taluka = defaultdict(list)
    for leaf in leaves:
        by_taluka[talukas.get(leaf['subdistrict_code'], '')].append(normal(town_name(leaf['name'])))
    ena_unmatched = [dict(taluka=k[0], name=k[1], serials=v,
                          census_name_candidates=difflib.get_close_matches(k[1], by_taluka.get(k[0], []), n=3, cutoff=0.8))
                     for k, v in sorted(ena.items()) if k not in ena_matched]
    # the lists and the polygon disagree: named by no list, centroid inside the public boundary
    disagree = [dict(geography_id=r['geography_id'], name=r['name'], persons=r['persons_count'])
                for r in rows if r['rule'] == 'external' and inside.get(r['geography_id'])]
    # ENA villages already inside by another rule are matched by name for the report
    already = Counter()
    for r in rows:
        key = (talukas.get(r['subdistrict_code'], ''), normal(town_name(r['name'])))
        if key in ena and r['rule'] != 'ena_2024_village':
            already[r['rule']] += 1

    out = Path(city.path(OUT))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    audit = dict(
        source='derived', decision='D13 (21 September 2026): the notified MMR as the core, the four-district envelope as the external tier',
        leaves=len(rows), tiers={t: sum(1 for r in rows if r['tier'] == t) for t in ('core', 'external')},
        persons_by_tier={t: persons[t] for t in ('core', 'external')},
        rules={k: dict(leaves=v, persons=persons[k]) for k, v in sorted(rule_counts.items())},
        public_boundary_check={k: dict(v) for k, v in sorted(check.items())},
        public_boundary_note='WRI layer 1 is the public GIS boundary (evidence only; omits the 2019 Palghar '
                             'extension): a core leaf outside it is expected under ena_2024_village, and an '
                             'external leaf inside it is a name the lists and the polygon disagree on',
        ena_villages_listed=len(ena), ena_villages_matched_by_name=len(ena_matched),
        ena_villages_already_core_by_another_rule=dict(already),
        ena_villages_unmatched=ena_unmatched,
        external_leaves_inside_public_boundary=disagree,
        municipal_names=sorted(municipal), village_codes=len(village_codes),
        sources=records,
        limitations=[
            'A leaf is wholly core or wholly external; no census count is apportioned across the boundary.',
            'The 2019 extension notification is a scanned PDF whose village list is not transcribed; the '
            '2024 SPA list is the later statement of the extended area and is what is read.',
            'An ENA village that matches no census leaf by normalised name within its taluka is listed, '
            'not guessed; a village renamed or merged since 2011 stays unmatched until a crosswalk is acquired.',
            'The public boundary polygon confirms the lists where they overlap; it decides nothing.'])
    Path(city.path(AUDIT)).write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n',
                                      encoding='utf-8', newline='\n')
    print(json.dumps({k: audit[k] for k in ('leaves', 'tiers', 'persons_by_tier', 'rules',
                                            'ena_villages_matched_by_name', 'ena_villages_listed')}, indent=1))
    print('unmatched ENA villages:', len(ena_unmatched))
    return 0


if __name__ == '__main__':
    sys.exit(main())
