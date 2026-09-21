"""Retain railway name/code evidence and scoped Harbour identity proposals.

An inferred label correction is not an observation or a global station-code
alias. The original timetable key survives every join.
"""
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

from pdfminer.high_level import extract_pages
from pypdf import PdfReader
import city
from extract_census_controls import source
from extract_wr_timetable import lines
from match_harbour_station_geometry import compact, mode_status
from manifest_io import manifest_reader

OUTPUT_INPUTS = {
    'data/processed/observed/wr_station_abbreviations.csv': [
        'data/raw/rail/wr_bct_disaster_plan_part1_2025_*.pdf'],
    'data/processed/observed/wr_station_code_reference.csv': [
        'data/raw/rail/wr_disaster_plan_part2_2025_*.pdf'],
    'data/processed/transit/cr_harbour_identity_proposals.csv': [
        'data/processed/geospatial/osm_research.gpkg',
        'data/processed/observed/_transport_points_audit.json',
        'data/processed/acquisition/osm_research_audit.json',
        'data/processed/acquisition/osm_transport_areas_audit.json',
        'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson',
        'data/processed/observed/osm_transport_relations.csv',
        'data/raw/rail/wr_bct_disaster_plan_part1_2025_*.pdf',
        'data/raw/rail/wr_disaster_plan_part2_2025_*.pdf',
        'data/processed/observed/wr_printed_timetable_cells.csv',
        'data/processed/transit/cr_harbour_stop_candidates.csv'],
    'data/processed/acquisition/cr_harbour_identity_evidence_audit.json': [
        'data/processed/geospatial/osm_research.gpkg',
        'data/processed/observed/_transport_points_audit.json',
        'data/processed/acquisition/osm_research_audit.json',
        'data/processed/acquisition/osm_transport_areas_audit.json',
        'data/processed/acquisition/osm_transport_relations_audit.json',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/geospatial/osm_transport_areas.geojson',
        'data/processed/observed/osm_transport_relations.csv',
        'data/raw/rail/wr_bct_disaster_plan_part1_2025_*.pdf',
        'data/raw/rail/wr_disaster_plan_part2_2025_*.pdf',
        'data/processed/observed/wr_printed_timetable_cells.csv',
        'data/processed/transit/cr_harbour_stop_candidates.csv'],
}


def read(path):
    with Path(city.path(path)).open(encoding='utf-8') as stream:
        return list(manifest_reader(stream))


def serial(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def dump(path, rows):
    target = Path(city.path(path))
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def mapped_corridor_identity(by_train, station_key):
    """Resolve a source key only between independently code-anchored route stops."""
    def audit(path):
        return json.loads(Path(city.path(path)).read_text(encoding='utf-8'))
    point_audit = audit('data/processed/observed/_transport_points_audit.json')
    research_audit = audit('data/processed/acquisition/osm_research_audit.json')
    area_audit = audit('data/processed/acquisition/osm_transport_areas_audit.json')
    relation_audit = audit('data/processed/acquisition/osm_transport_relations_audit.json')
    if len({research_audit['source_sha256'],area_audit['source_sha256'],relation_audit['source_pbf_sha256']}) != 1:
        raise ValueError('Point, area and route evidence must share one OSM acquisition')
    with Path(city.path('data/processed/geospatial/osm_research.gpkg')).open('rb') as stream:
        if hashlib.file_digest(stream,'sha256').hexdigest() != point_audit['input_sha256']:
            raise ValueError('Station point evidence references another spatial build')
    points = {r['osm_node_id']: json.loads(r['all_driver_tags_json'])
              for r in read('data/processed/observed/osm_transport_points.csv')}
    features = {'node/'+key: tags for key,tags in points.items()}
    for f in json.loads(Path(city.path('data/processed/geospatial/osm_transport_areas.geojson')).read_text(encoding='utf-8'))['features']:
        features[f['id']] = f['properties']['all_driver_tags']
    feature_codes = {}
    for feature,tags in features.items():
        if tags.get('railway') not in ('station','halt') or mode_status(tags).startswith('excluded_'):
            continue
        codes = {value.strip() for field in ('ref','railway:ref') for value in tags.get(field,'').split(';') if value.strip()}
        if codes:
            feature_codes[feature] = codes
    relations = read('data/processed/observed/osm_transport_relations.csv')
    node_codes = defaultdict(lambda: defaultdict(list))
    for relation in relations:
        if relation['public_transport_tag'] != 'stop_area':
            continue
        members = json.loads(relation['ordered_members_json'])
        station_features = sorted({m['type']+'/'+m['ref'] for m in members} & feature_codes.keys())
        for member in members:
            tags = points.get(member['ref'],{}) if member['type']=='node' else {}
            if not (tags.get('railway')=='stop' or (tags.get('public_transport')=='stop_position' and tags.get('train')=='yes')):
                continue
            if mode_status(tags).startswith('excluded_') or tags.get('bus')=='yes':
                continue
            for feature in station_features:
                for code in sorted(feature_codes[feature]):
                    node_codes[member['ref']][code].append(dict(stop_area_relation_id=relation['osm_relation_id'],
                        station_feature_id=feature, station_source_tags=features[feature]))
    occurrences = []
    neighbour_pairs = set()
    total_occurrences = 0
    for train,rows in sorted(by_train.items()):
        total_occurrences += sum(r['station_key']==station_key for r in rows)
        for a,b,c in zip(rows,rows[1:],rows[2:]):
            if b['station_key'] != station_key:
                continue
            if not all(r['station_key'].startswith('CR_THB_CODE:') for r in (a,c)):
                raise ValueError('Corridor anchors must have observed source station codes')
            pair = (a['station_key'].split(':',1)[1],c['station_key'].split(':',1)[1])
            neighbour_pairs.add(pair)
            occurrences.append(dict(train=train, station_keys=[r['station_key'] for r in (a,b,c)],
                source_references=[json.loads(r['source_references']) for r in (a,b,c)]))
    if not occurrences or len(occurrences)!=total_occurrences:
        raise ValueError('Every scoped identity occurrence needs two corridor anchors')
    if len(neighbour_pairs)<2 or any(pair[::-1] not in neighbour_pairs for pair in neighbour_pairs):
        raise ValueError('The scoped corridor derivation requires both timetable directions')
    matches = []
    codes_by_pair = defaultdict(set)
    for relation in relations:
        tags = json.loads(relation['all_tags_json'])
        if tags.get('route')!='train' or tags.get('public_transport:version')!='2':
            continue
        members = [(order,m) for order,m in enumerate(json.loads(relation['ordered_members_json']),1)
                   if m['type']=='node' and m['role'] in ('stop','stop_entry_only','stop_exit_only')]
        for a,b,c in zip(members,members[1:],members[2:]):
            for before,after in sorted(neighbour_pairs):
                if before not in node_codes[a[1]['ref']] or after not in node_codes[c[1]['ref']]:
                    continue
                middle = node_codes[b[1]['ref']]
                if not middle:
                    raise ValueError('Mapped middle stop has no independent station-code evidence')
                codes_by_pair[(before,after)].update(middle)
                matches.append(dict(osm_route_relation_id=relation['osm_relation_id'], route_source_tags=tags,
                    observed_neighbour_codes=[before,after],
                    ordered_stop_members=[dict(member_order=order, **m, node_source_tags=points.get(m['ref'],{})) for order,m in (a,b,c)],
                    before_station_evidence=node_codes[a[1]['ref']][before],
                    middle_station_code_evidence=middle, after_station_evidence=node_codes[c[1]['ref']][after]))
    if any(len(codes_by_pair[pair])!=1 for pair in neighbour_pairs):
        raise ValueError('Corridor context has missing or conflicting mapped station identities')
    codes = set().union(*(codes_by_pair[pair] for pair in neighbour_pairs))
    if len(codes)!=1:
        raise ValueError('Opposite directions disagree on scoped station identity')
    code = next(iter(codes))
    station_evidence = {serial(item) for match in matches for item in match['middle_station_code_evidence'][code]}
    reference_names = {json.loads(item)['station_source_tags']['name'] for item in station_evidence}
    if len(reference_names)!=1:
        raise ValueError('Mapped station names need additional reconciliation')
    references = sorted({serial(ref) for occurrence in occurrences for refs in occurrence['source_references'] for ref in refs})
    return dict(source='derived_station_identity_proposal', station_key=station_key,
        proposed_reference_name=next(iter(reference_names)), proposed_station_code=code,
        method='scoped_bidirectional_mapped_route_neighbour_identity',
        code_reference=serial(dict(input_path='data/processed/observed/osm_transport_relations.csv',
                                  source_pbf_sha256=relation_audit['source_pbf_sha256'],
                                  station_evidence=[json.loads(v) for v in sorted(station_evidence)])),
        wr_timetable_labels='[]', abbreviation_references='[]', source_timetable_references=serial([json.loads(v) for v in references]),
        matching_wr_grid_triplets='[]', source_neighbour_triplets=serial(occurrences), mapped_route_triplets=serial(matches),
        scope='this_source_station_key_only_not_a_global_name_or_code_alias',
        status='identity_proposal_requires_geometry_branch_and_route_validation')


def main():
    glossary_record, glossary_path = source('wr_bct_disaster_plan_part1_2025', 'rail')
    glossary_pdf = PdfReader(glossary_path)
    glossary = []
    for page_number in (15, 158):
        text = glossary_pdf.pages[page_number-1].extract_text(extraction_mode='layout')
        matches = re.findall(r'^\s*(Jn\.|JOS|MM)\s+([^\r\n]+?)\s*$', text, re.MULTILINE)
        if dict(matches) != {'Jn.': 'Junction', 'JOS': 'Jogeshwari Station', 'MM': 'Mahim Station'}:
            raise ValueError('Railway abbreviation evidence differs from reviewed page')
        if page_number == 15:
            for abbreviation, expansion in matches:
                glossary.append(dict(source='observed_railway_publication', source_id='wr_bct_disaster_plan_part1_2025',
                    source_sha256=glossary_record['sha256'], source_page=page_number,
                    duplicate_source_page=158, printed_abbreviation=abbreviation, printed_expansion=expansion,
                    evidence_scope='repeated_page_is_not_independent_corroboration'))
    record, path = source('wr_disaster_plan_part2_2025', 'rail')
    pages = list(extract_pages(str(path), page_numbers=[38, 39]))
    first = list(lines(pages[0]))
    header = next(l for l in first if l.get_text().strip() == 'Code')
    name_header = next(l for l in first if l.get_text().strip() == 'Name of')
    next_header = next(l for l in first if l.get_text().strip() == 'MTNL')
    centre = lambda line: (line.x0 + line.x1) / 2
    left = (centre(header) + centre(name_header)) / 2
    right = (centre(header) + centre(next_header)) / 2
    selected_names = {'MAHIM', 'JOGESHWARI', 'JOGESHWARI AT', 'RAM MANDIR', 'GOREGAON'}
    codes = []
    for page_number, page in zip((39, 40), pages):
        page_lines = list(lines(page))
        for line in sorted(page_lines, key=lambda l: (-l.y0, l.x0)):
            name = re.sub(r'^\d+\s+', '', ' '.join(line.get_text().split()))
            if name not in selected_names or line.x1 > left:
                continue
            candidates = [l for l in page_lines if left < centre(l) < right
                          and abs(l.y0-line.y0) < min(l.height, line.height)/2
                          and re.fullmatch(r'[A-Z]+', l.get_text().strip())]
            if len(candidates) != 1:
                raise ValueError('Station code column is ambiguous: ' + name)
            code_line = candidates[0]
            codes.append(dict(source='observed_railway_publication', source_id='wr_disaster_plan_part2_2025',
                              source_sha256=record['sha256'], source_page=page_number,
                              printed_station_name=name, printed_station_code=code_line.get_text().strip(),
                              source_name_bbox_pdf_pt=serial(line.bbox), source_code_bbox_pdf_pt=serial(code_line.bbox),
                              evidence_scope='2025_reference_identity_not_current_service_or_capacity'))
    if {r['printed_station_name'] for r in codes} != selected_names or len(codes) != len(selected_names):
        raise ValueError('Selected station-reference rows are incomplete or duplicated')
    by_name = {compact(r['printed_station_name']): r for r in codes}
    stops = read('data/processed/transit/cr_harbour_stop_candidates.csv')
    wr = read('data/processed/observed/wr_printed_timetable_cells.csv')
    by_train = defaultdict(list)
    for row in stops:
        by_train[row['train_number']].append(row)
    triplets = defaultdict(list)
    for train, rows in sorted(by_train.items()):
        rows.sort(key=lambda r: int(r['stop_sequence']))
        for a, b, c in zip(rows, rows[1:], rows[2:]):
            if b['station_key'] == 'CR_HB_LABEL:ramnagar':
                neighbours = {a['station_key'], c['station_key']}
                if neighbours != {'CR_HB_LABEL:jogeshwari', 'CR_HB_LABEL:goregaon'}:
                    raise ValueError('Ramnagar has unexpected timetable neighbours')
                triplets[b['station_key']].append(dict(train=train,
                    station_keys=[r['station_key'] for r in (a, b, c)],
                    source_references=[json.loads(r['source_references']) for r in (a, b, c)]))
    wr_grids = defaultdict(dict)
    for row in wr:
        key = (row['source_id'], row['source_sha256'], row['source_page'])
        order = int(row['station_row_order'])
        name = row['aligned_station_row_label']
        if order in wr_grids[key] and wr_grids[key][order] != name:
            raise ValueError('WR row order has multiple station labels')
        wr_grids[key][order] = name
    wr_triplets = []
    for key, grid in sorted(wr_grids.items()):
        ordered = sorted(grid.items())
        for a, b, c in zip(ordered, ordered[1:], ordered[2:]):
            if [compact(item[1]) for item in (a, b, c)] == ['jogeshwari', 'rammandir', 'goregaon']:
                if [a[0]+1, b[0]+1] != [b[0], c[0]]:
                    raise ValueError('WR reference triplet is not adjacent in printed grid')
                wr_triplets.append(dict(source_id=key[0], source_sha256=key[1], source_page=key[2],
                                        printed_rows=[a, b, c]))
    if not wr_triplets or not triplets['CR_HB_LABEL:ramnagar']:
        raise ValueError('No independent printed-order support for label-correction proposal')
    proposals = []
    specifications = (
        ('CR_HB_LABEL:jogeshwari', 'jogeshwari', 'exact_published_station_name_to_code', []),
        ('CR_HB_LABEL:mahim jn', 'mahim', 'published_code_and_junction_abbreviation', []),
        ('CR_HB_LABEL:ramnagar', 'rammandir', 'inferred_label_correction_from_adjacent_station_order', wr_triplets),
    )
    for key, name, method, supporting_grids in specifications:
        inputs = [r for r in stops if r['station_key'] == key]
        if not inputs:
            raise ValueError('Missing source station key: ' + key)
        evidence = by_name[name]
        wr_labels = sorted({r['aligned_station_row_label'] for r in wr
                            if compact(r['aligned_station_row_label']) in (compact(key.split(':', 1)[1]), name)})
        if not wr_labels:
            raise ValueError('No WR timetable name evidence: ' + key)
        references = sorted({serial(ref) for r in inputs for ref in json.loads(r['source_references'])})
        proposals.append(dict(source='derived_station_identity_proposal', station_key=key,
                               proposed_reference_name=evidence['printed_station_name'],
                               proposed_station_code=evidence['printed_station_code'], method=method,
                               code_reference=serial(evidence), wr_timetable_labels=serial(wr_labels),
                               abbreviation_references=serial([r for r in glossary if r['printed_abbreviation'] == evidence['printed_station_code']
                                                               or (name == 'mahim' and r['printed_abbreviation'] == 'Jn.')]),
                               source_timetable_references=serial([json.loads(v) for v in references]),
                               matching_wr_grid_triplets=serial(supporting_grids),
                               source_neighbour_triplets=serial(triplets.get(key, [])),
                               mapped_route_triplets='[]',
                               scope='this_source_station_key_only_not_a_global_name_or_code_alias',
                               status='identity_proposal_requires_geometry_branch_and_route_validation'))
    corridor_proposal = mapped_corridor_identity(by_train, 'CR_THB_CODE:SNPD')
    proposals.append(corridor_proposal)
    dump('data/processed/observed/wr_station_code_reference.csv', codes)
    dump('data/processed/observed/wr_station_abbreviations.csv', glossary)
    dump('data/processed/transit/cr_harbour_identity_proposals.csv', proposals)
    audit = dict(reference_rows=len(codes), abbreviation_rows=len(glossary), proposals=len(proposals),
                 harbour_neighbour_triplets=len(triplets['CR_HB_LABEL:ramnagar']),
                 wr_named_grid_triplets=len(wr_triplets),
                 scoped_corridor_identity=dict(station_key=corridor_proposal['station_key'],
                     proposed_code=corridor_proposal['proposed_station_code'],
                     timetable_occurrences=len(json.loads(corridor_proposal['source_neighbour_triplets'])),
                     mapped_route_triplets=len(json.loads(corridor_proposal['mapped_route_triplets']))),
                 unresolved_source_keys=[],
                 limitations=[
                     'Ramnagar remains the observed Harbour label; Ram Mandir is a derived correction proposal, not rewritten source text.',
                     'Mahim Jn and Mahim are linked by the junction qualifier; this is a scoped derivation, not an exact-name observation.',
                     'Jogeshwari AT and Jogeshwari share JOS in the reference; the code cannot distinguish Harbour and Western platforms.',
                     'Reference documents have different dates; no schedule time or calendar is copied across vintages.',
                     'Repeated grid pages and duplicated glossary pages are not independent sources or extra observations.',
                     'The timetable SNPD key is linked to the mapped passenger station only in its anchored corridor context; no global car-shed alias is created.',
                     'Opposite mapped route relations share one OSM source and do not independently verify current operation or timetable applicability.',
                 ])
    Path(city.path('data/processed/acquisition/cr_harbour_identity_evidence_audit.json')).write_text(
        json.dumps(audit, indent=2)+'\n', encoding='utf-8', newline='\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
