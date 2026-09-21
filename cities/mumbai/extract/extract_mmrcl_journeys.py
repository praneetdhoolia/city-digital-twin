"""Audit Metro 3 public journey responses without inventing missing run times."""
import csv
from decimal import Decimal
import json
from pathlib import Path

import city
from extract_mmrcl_stations import read

OUTPUT_INPUTS = {
    'data/processed/observed/metro3_journey_segments.csv': [
        'data/raw/transit/mmrcl_journey_*.json', 'data/raw/transit/mmrcl_all_stations_*.json'],
    'data/processed/observed/_metro3_journey_audit.json': [
        'data/raw/transit/mmrcl_journey_*.json', 'data/raw/transit/mmrcl_station_*.json',
        'data/raw/transit/mmrcl_all_stations_*.json'],
}


def distance_m(response):
    number, unit = response['distance'].split()
    if unit != 'km':
        raise ValueError('Undeclared distance unit')
    distance = Decimal(number) * 1000
    if not distance.is_finite() or distance <= 0:
        raise ValueError('Invalid published distance')
    return distance


def route_edges(response):
    if len(response['route']) != 1:
        raise ValueError('Expected one line in this direct journey')
    edges = [tuple(edge.split('-')) for edge in response['route'][0]['map-path']]
    if not edges or any(len(edge) != 2 for edge in edges):
        raise ValueError('Missing or malformed path')
    if any(a[1] != b[0] for a, b in zip(edges, edges[1:])):
        raise ValueError('Disconnected journey path')
    return edges


def main():
    directory, _ = read('mmrcl_all_stations')
    known = {station['code'] for station in directory}
    forward, forward_record = read('mmrcl_journey_aryj_cup_20260918')
    reverse, reverse_record = read('mmrcl_journey_cup_aryj_20260918')
    edges = route_edges(forward)
    station_chain = [edges[0][0]] + [edge[1] for edge in edges]
    if len(station_chain) != len(known) or set(station_chain) != known:
        raise ValueError('Journey does not visit the complete station directory once')
    if forward['stations'] != len(station_chain):
        raise ValueError('Published station count disagrees with journey path')
    if route_edges(reverse) != [(b, a) for a, b in reversed(edges)]:
        raise ValueError('Reverse journey is inconsistent with forward journey')
    rows, missing_from_details = [], []
    for sequence, (origin, destination) in enumerate(edges, start=1):
        source_id = f'mmrcl_journey_{origin.lower()}_{destination.lower()}_20260918'
        response, record = read(source_id)
        if route_edges(response) != [(origin, destination)] or response['stations'] != 2:
            raise ValueError('Adjacent journey contains another station or path')
        # Zero is published even for a positive-distance journey. Retain it as
        # evidence, but never convert it to a usable zero-second running time.
        raw_time = response['total_time']
        rows.append(dict(sequence=sequence, from_station_code=origin,
                         to_station_code=destination, distance_m=str(distance_m(response)),
                         ordinary_fare_inr=response['fare'], source_total_time=raw_time,
                         running_time_s=None, time_status='unvalidated_operator_value',
                         source='observed', source_id=source_id, source_sha256=record['sha256']))
        detail, _ = read('mmrcl_station_' + origin.lower())
        neighbours = {item['next_station']['code']
                      for group in detail['prev_next_stations']
                      for entries in group.values() for item in entries
                      if item.get('next_station')}
        if destination not in neighbours:
            missing_from_details.append([origin, destination])
    output = Path(city.path('data/processed/observed'))
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'metro3_journey_segments.csv').open('w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    total = sum(Decimal(row['distance_m']) for row in rows)
    audit = dict(schema_version=1, source='derived', status='evidence_only',
                 station_chain=station_chain, directed_segments=len(rows),
                 reverse_chain_consistent=True,
                 published_segment_distance_sum_m=str(total),
                 published_end_to_end_distance_m=str(distance_m(forward)),
                 published_reverse_distance_m=str(distance_m(reverse)),
                 distance_difference_m=str(total-distance_m(forward)),
                 missing_in_station_detail_but_present_in_journey=missing_from_details,
                 zero_time_segments=sum(row['source_total_time']=='0:00:00' for row in rows),
                 forward_source_sha256=forward_record['sha256'],
                 reverse_source_sha256=reverse_record['sha256'],
                 limitations=[
                     'Published segment distance is not surveyed alignment geometry.',
                     'The opposite-direction journey validates topology, not equal segment running times.',
                     'Zero duration at positive distance is unusable. No running time has been inferred.',
                     'Adjacent single fares cannot be added to calculate through fares.',
                     'The operator internal line_no is not the public metro line number.',
                     'Responses requested for 18 September 2026 do not establish other dates or timetables.'])
    (output / '_metro3_journey_audit.json').write_text(json.dumps(audit,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
