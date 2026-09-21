"""Find traceable station/stop geometry candidates without merging rail modes."""
from collections import Counter, defaultdict
import csv
import hashlib
import json
from pathlib import Path
import unicodedata

import city
from manifest_io import manifest_reader

OUTPUT_INPUTS = {
    'data/processed/transit/cr_harbour_geometry_candidates.csv': [
        'data/processed/transit/cr_harbour_identity_proposals.csv',
        'data/processed/transit/cr_harbour_stop_candidates.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson'],
    'data/processed/transit/cr_harbour_station_geometry_coverage.csv': [
        'data/processed/transit/cr_harbour_identity_proposals.csv',
        'data/processed/transit/cr_harbour_stop_candidates.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson'],
    'data/processed/acquisition/cr_harbour_station_geometry_audit.json': [
        'data/processed/transit/cr_harbour_identity_proposals.csv',
        'data/processed/transit/cr_harbour_stop_candidates.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson'],
}


def compact(value):
    # Formatting equivalence only: no edit distance, token deletion or synonyms.
    return ''.join(c for c in unicodedata.normalize('NFKC', value).casefold() if c.isalnum())


def names(tags):
    return [(key, value) for key in ('name', 'name:en', 'official_name', 'short_name', 'alt_name')
            for value in tags.get(key, '').split(';') if value]


def mode_status(tags):
    if tags.get('station') == 'monorail' or tags.get('monorail') == 'yes':
        return 'excluded_explicit_monorail'
    if tags.get('station') == 'subway' or tags.get('subway') == 'yes':
        return 'excluded_explicit_metro'
    # Preserve source qualifiers; a light_rail tag alone is not used to reject
    # a feature also explicitly labelled with the suburban railway network.
    if tags.get('train') == 'yes' or tags.get('network') in (
            'IR', 'CR', 'Indian Railways', 'Mumbai Suburban Railway',
            'Mumbai Suburban Railway Network', 'Mumbai Suburban Rail Network'):
        return 'source_tags_support_railway_network'
    return 'mode_not_established_by_these_tags'


def main():
    paths = {key: Path(city.path(key)) for key in (
        'data/processed/transit/cr_harbour_identity_proposals.csv',
        'data/processed/transit/cr_harbour_stop_candidates.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson')}
    with paths['data/processed/transit/cr_harbour_stop_candidates.csv'].open(encoding='utf-8') as stream:
        stops = list(csv.DictReader(stream))
    with paths['data/processed/transit/cr_harbour_identity_proposals.csv'].open(encoding='utf-8') as stream:
        identity_rows = list(manifest_reader(stream))
    identities = {r['station_key']: r for r in identity_rows}
    if len(identities) != len(identity_rows):
        raise ValueError('Conflicting identity proposals require review')
    station_keys = sorted({row['station_key'] for row in stops})
    features = []
    with paths['data/processed/observed/osm_transport_points.csv'].open(encoding='utf-8') as stream:
        for row in csv.DictReader(stream):
            features.append(dict(id='node/'+row['osm_node_id'], tags=json.loads(row['all_driver_tags_json']),
                                 geometry_type='Point', longitude_deg=row['longitude_deg'], latitude_deg=row['latitude_deg'],
                                 geometry_status='source_point', input_path='data/processed/observed/osm_transport_points.csv'))
    for feature in json.loads(paths['data/processed/geospatial/osm_transport_areas.geojson'].read_text(encoding='utf-8'))['features']:
        p = feature['properties']
        features.append(dict(id=feature['id'], tags=p['all_driver_tags'],
                             geometry_type=feature['geometry']['type'] if feature['geometry'] else 'None',
                             longitude_deg='', latitude_deg='', geometry_status=p['geometry_status'],
                             input_path='data/processed/geospatial/osm_transport_areas.geojson'))
    # This inventory covers rail stations, on-track stops and platforms; a bus
    # stop with the same name is not a railway geometry candidate.
    features = [f for f in features if f['tags'].get('railway') in ('station', 'halt', 'stop', 'platform') or
                (f['tags'].get('public_transport') == 'stop_position' and f['tags'].get('train') == 'yes')]
    if len({f['id'] for f in features}) != len(features):
        raise ValueError('Repeated OSM feature identity across geometry inputs')
    features.sort(key=lambda f: f['id'])
    candidates, coverage = [], []
    feature_keys = defaultdict(set)
    for station_key in station_keys:
        namespace, suffix = station_key.split(':', 1)
        observed_code = suffix if namespace in ('CR_THB_CODE', 'CR_EXTERNAL_CODE') else None
        proposal = identities.get(station_key)
        code = proposal['proposed_station_code'] if proposal else observed_code
        base_names = {compact(suffix)} if observed_code is None else set()
        # Only names on a directly code-matched station can expand a code key.
        # Platform numbers and stop-position refs are not station alpha codes.
        expansions = defaultdict(list)
        for feature in features:
            tags = feature['tags']
            if code is not None and tags.get('railway') in ('station', 'halt') and not mode_status(tags).startswith('excluded_'):
                if code in tags.get('ref', '').split(';') or code in tags.get('railway:ref', '').split(';'):
                    for field, value in names(tags):
                        expansions[compact(value)].append(dict(osm_feature=feature['id'], name_field=field, name=value))
        count = Counter()
        for feature in features:
            tags = feature['tags']
            reasons = []
            if code is not None and tags.get('railway') in ('station', 'halt'):
                for field in ('ref', 'railway:ref'):
                    if code in tags.get(field, '').split(';'):
                        reasons.append(dict(method='exact_source_code', field=field, value=code))
            for field, value in names(tags):
                key = compact(value)
                if key in base_names:
                    reasons.append(dict(method='case_space_punctuation_equivalence', field=field, value=value))
                if key in expansions:
                    reasons.append(dict(method='name_from_code_matched_station', field=field, value=value,
                                        station_evidence=expansions[key]))
            if not reasons:
                continue
            if proposal:
                reasons.append(dict(method='scoped_identity_proposal',
                                    input_path='data/processed/transit/cr_harbour_identity_proposals.csv',
                                    station_key=station_key, derivation=proposal['method'],
                                    proposed_station_code=proposal['proposed_station_code'],
                                    code_reference=json.loads(proposal['code_reference'])))
                for reason in reasons:
                    if reason['method'] == 'exact_source_code':
                        reason['method'] = 'code_from_scoped_identity_proposal'
            status = mode_status(tags)
            kind = 'stop' if tags.get('public_transport') == 'stop_position' and tags.get('train') == 'yes' else tags.get('railway', '')
            eligible = not status.startswith('excluded_') and feature['geometry_status'] in ('valid', 'source_point')
            count['all_matches'] += 1
            if eligible:
                count['retained_candidates'] += 1
                count[kind] += 1
                feature_keys[feature['id']].add(station_key)
            else:
                count['excluded_candidates'] += 1
            candidates.append(dict(source='derived_osm_identity_candidate', station_key=station_key,
                                   osm_feature_id=feature['id'], geometry_input=feature['input_path'],
                                   geometry_type=feature['geometry_type'], geometry_status=feature['geometry_status'],
                                   longitude_deg=feature['longitude_deg'], latitude_deg=feature['latitude_deg'],
                                   osm_name=tags.get('name', ''), osm_ref=tags.get('ref', ''),
                                   railway_tag=tags.get('railway', ''), public_transport_tag=tags.get('public_transport', ''),
                                   train_tag=tags.get('train', ''), evidence_feature_kind=kind, station_tag=tags.get('station', ''),
                                   network_tag=tags.get('network', ''), operator_tag=tags.get('operator', ''),
                                   mode_evidence_status=status, retain_for_identity_review=eligible,
                                   match_evidence=json.dumps(reasons, sort_keys=True, ensure_ascii=False),
                                   assignment_status='not_a_selected_boarding_point_or_track_link'))
        coverage.append(dict(station_key=station_key, matched_features=count['all_matches'],
                             retained_candidates=count['retained_candidates'], excluded_candidates=count['excluded_candidates'],
                             station_or_halt_candidates=count['station']+count['halt'],
                             stop_position_candidates=count['stop'], platform_candidates=count['platform'],
                             status='candidates_need_identity_and_track_review' if count['retained_candidates'] else 'unmatched_requires_source_alias_or_additional_geometry'))
    directory = Path(city.path('data/processed/transit'))
    directory.mkdir(parents=True, exist_ok=True)
    for name, rows in (('cr_harbour_geometry_candidates.csv', candidates), ('cr_harbour_station_geometry_coverage.csv', coverage)):
        with (directory/name).open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
            writer.writeheader()
            writer.writerows(rows)
    audit = dict(input_sha256={key: hashlib.sha256(path.read_bytes()).hexdigest() for key, path in paths.items()},
                 station_keys=len(station_keys), candidate_rows=len(candidates),
                 keys_with_candidates=sum(bool(r['retained_candidates']) for r in coverage),
                 unmatched_keys=[r['station_key'] for r in coverage if not r['retained_candidates']],
                 scoped_identity_proposal_keys=sorted(identities),
                 mode_evidence_counts=dict(sorted(Counter(r['mode_evidence_status'] for r in candidates).items())),
                 features_shared_by_source_station_keys={key: sorted(values) for key, values in sorted(feature_keys.items()) if len(values)>1},
                 limitations=[
                     'No fuzzy matching is performed; declared scoped identity proposals retain their evidence and are not observed aliases.',
                     'Suburban, metro and monorail features with the same name remain separate; explicit metro/monorail candidates are excluded.',
                     'A retained feature with unspecified mode still needs independent network or relation evidence.',
                     'A station point and its polygon may describe the same facility; neither is a capacity or passenger-count unit.',
                     'Polygon coordinates are not replaced by a centroid or invented boarding point.',
                     'Stop-position/platform refs may be platform numbers; they are not used as station alpha codes.',
                     'Platform allocation, direction, native track membership, accessibility and current operation remain unresolved.',
                 ])
    Path(city.path('data/processed/acquisition/cr_harbour_station_geometry_audit.json')).write_text(
        json.dumps(audit, indent=2, ensure_ascii=False)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('station_keys', 'candidate_rows', 'keys_with_candidates', 'unmatched_keys', 'mode_evidence_counts')}))


if __name__ == '__main__':
    main()
