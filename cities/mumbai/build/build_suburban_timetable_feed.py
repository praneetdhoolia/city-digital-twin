"""The suburban rail services from the printed timetables, as a GTFS feed.

Until 22 September 2026 every suburban train in the feed was generated: an OSM
route relation's stops run at an assumed headway inside an assumed window
(build_baseline_transit_feed.py), 31 patterns and 4,278 departures a day
against the 3,234 the operators run (suburban_service_counts_202604.csv).
The operators publish the timetable, and the package holds its cells:
`wr_printed_timetable_cells.csv` and `cr_printed_timetable_cells.csv`, one row
per (train, station row, printed clock) read by position from the PDFs. This
builder turns those cells into trips - the real timetable, which GOAL.md
requirement 1 asks for - and `build_baseline_transit_feed.py` takes them in
place of the generated patterns when `A.baseline_transit.suburban_timetable`
= `printed_timetables`.

For every timetable sheet the registry lists (`A.baseline_transit.printed_timetables`:
the sheet's line and whether it is a primary table or a supplement flagging
AC or 15-car trains) and every train number on it:

  * the printed cells become the train's stops in the order the sheet prints
    the stations; the direction is read from the times (increasing down the
    sheet's rows is the sheet's own direction, decreasing the reverse), a
    clock that steps back over midnight gains a day, and a train whose times
    are not monotonic in either reading is refused into the audit, never
    guessed;
  * a printed station label resolves to an OSM station node: first among the
    stop members of the line's own route relations, then among the extract's
    railway stations by name, through the alias table
    `extract/transcriptions/suburban_station_labels.json` (printed
    abbreviations and codes expanded, each with the source it was read from);
    an unresolved label refuses the build;
  * a train on a supplement (AC, 15-car) and on the primary sheet keeps the
    primary's times and takes the flag; one only on the supplement is added;
  * trips of one line, direction and stopping pattern share a GTFS route,
    named for the pattern, so the mapper routes each pattern once; the AC and
    15-car trains sit on their own routes so the fleet builder can give them
    their own profile.

Output: `schedules/baseline_suburban_timetable.zip` (stops, routes, trips,
stop_times - the calendar and agency are the bus feed's) and the audit
`data/processed/acquisition/baseline_suburban_timetable.json`, which counts
the trains per sheet against the operators' published daily services. The
sheets are of different dates (WR September 2026, CR main 2024, harbour May
2026, trans-harbour January 2024, port December 2025); each trip carries its
sheet's id, and the audit says so.
"""
from collections import Counter, defaultdict
import csv
import io
import json
from pathlib import Path
import re
import zipfile

import city
import registry
from build.extract_osm_network import fingerprint

csv.field_size_limit(10 ** 9)

OUTPUT_INPUTS = {
    'schedules/baseline_suburban_timetable.zip': [
        'data/processed/observed/wr_printed_timetable_cells.csv',
        'data/processed/observed/cr_printed_timetable_cells.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/observed/osm_transport_relations.csv',
        'extract/transcriptions/suburban_station_labels.json',
        'registry/A_baseline_services.json'],
    'data/processed/acquisition/baseline_suburban_timetable.json': [
        'data/processed/observed/wr_printed_timetable_cells.csv',
        'data/processed/observed/cr_printed_timetable_cells.csv',
        'data/processed/observed/osm_transport_points.csv',
        'data/processed/observed/osm_transport_relations.csv',
        'extract/transcriptions/suburban_station_labels.json',
        'registry/A_baseline_services.json'],
}
OUT = 'schedules/baseline_suburban_timetable.zip'
AUDIT = 'data/processed/acquisition/baseline_suburban_timetable.json'
DAY_S = 24 * 3600


def rows(relative):
    with Path(city.path(relative)).open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def normalise(label):
    """A printed station label or an OSM name to its comparable form: letters
    and digits only, lower case, junction and road suffixes kept."""
    text = label.casefold().replace('&', ' and ')
    text = re.sub(r'\(.*?\)', ' ', text)              # (West), (Suburban), (L)
    text = re.sub(r'[^a-z0-9]+', ' ', text)
    return ' '.join(text.split())


def clock_to_s(hhmm):
    h, m = map(int, hhmm.split(':'))
    return h * 3600 + m * 60


def clock(seconds):
    h, rest = divmod(int(seconds), 3600)
    m, s = divmod(rest, 60)
    return '%02d:%02d:%02d' % (h, m, s)


def sequence_times(cells):
    """(stops in travel order, direction) from a train's cells, or (None, why).

    `cells` are (row_order, label, seconds) sorted by row order. The sheet's
    own direction reads the rows top to bottom; the reverse reads them bottom
    up. A time that steps back by more than half a day gains a day. The
    reading whose times never decrease is the train's; both or neither is a
    refusal."""
    def read(seq):
        out, last, offset = [], None, 0
        for order, label, s in seq:
            t = s + offset
            if last is not None and t < last:
                if last - t > DAY_S / 2:
                    offset += DAY_S
                    t += DAY_S
                else:
                    return None
            out.append((order, label, t))
            last = t
        return out
    forward = read(cells)
    backward = read(list(reversed(cells)))
    if forward and not backward:
        return forward, 'sheet'
    if backward and not forward:
        return backward, 'reverse'
    if forward and backward:
        return (forward, 'sheet') if len(cells) < 3 else (None, 'ambiguous_direction')
    return None, 'non_monotonic_times'


def station_index(points, relations, aliases, lines):
    """For each line: normalised name -> OSM node id, from the line's own
    relations' stop members first, then every railway station point."""
    by_node = {r['osm_node_id']: r for r in points}
    station_points = {}
    for r in points:
        tags = json.loads(r['selected_tags_json'])
        # a station, a halt, or a stop position on the track (a new station
        # the extract holds only as its stop nodes, e.g. Targhar)
        if (tags.get('railway') in ('station', 'halt', 'stop') and r['name']
                and tags.get('station') not in ('subway', 'light_rail', 'monorail')):
            station_points.setdefault(normalise(r['name']), []).append(r['osm_node_id'])
    line_index = {}
    for line, spec in lines.items():
        own = {}
        for rel in relations:
            if rel['osm_relation_id'] in spec['relations']:
                for member in json.loads(rel['ordered_members_json']):
                    if member['role'].startswith('stop') and member['ref'] in by_node and by_node[member['ref']]['name']:
                        own.setdefault(normalise(by_node[member['ref']]['name']), member['ref'])
        line_index[line] = (own, station_points)
    return line_index, by_node


def resolve(label, line, line_index, aliases, unresolved):
    """The OSM node a printed label names on this line, or None (recorded)."""
    own, everywhere = line_index[line]
    if label in aliases.get('skipped', {}):
        unresolved[('skipped', label)] += 1
        return None
    key = normalise(label)
    candidates = [key]
    alias = aliases['labels'].get(label) or aliases['labels'].get(label.strip().casefold())
    if alias:
        candidates.insert(0, normalise(alias))
    for cand in candidates:
        if cand in own:
            return own[cand]
        for name, node in own.items():          # 'mahim' vs 'mahim junction'
            if name.startswith(cand + ' ') or cand.startswith(name + ' '):
                return node
    for cand in candidates:
        nodes = everywhere.get(cand)
        if nodes:                 # the two stop positions of one station: either sits on its track
            return sorted(set(nodes))[0]
    unresolved[(line, label)] += 1
    return None


def main():
    cfg = registry.load()
    sheets = cfg.get('A.baseline_transit.printed_timetables')
    lines = cfg.get('A.baseline_transit.suburban_lines')
    aliases = json.loads(Path(city.path('extract/transcriptions/suburban_station_labels.json')).read_text(encoding='utf-8'))
    dwell = cfg.get('A.baseline_transit.stop_dwell_s')['train']
    points = rows('data/processed/observed/osm_transport_points.csv')
    relations = rows('data/processed/observed/osm_transport_relations.csv')
    line_index, by_node = station_index(points, relations, aliases, lines)
    cells = rows('data/processed/observed/wr_printed_timetable_cells.csv') + rows('data/processed/observed/cr_printed_timetable_cells.csv')
    by_sheet_train = defaultdict(list)
    for c in cells:
        if c['source_id'] in sheets:
            by_sheet_train[(c['source_id'], c['train_number'])].append(c)
    unresolved = Counter()
    trains = {}                      # (line, train_number) -> dict
    refused = []
    counts = Counter()
    # every sheet's reading of every train, then the trains assembled per line
    readings = defaultdict(list)     # (line, number) -> [(sheet, stops, direction)]
    for (sheet, number), group in sorted(by_sheet_train.items()):
        spec = sheets[sheet]
        line = spec['line']
        # one train's cells across the sheet's pages: a continuation page
        # prints the same train again with later stations; rows are ordered
        # within a page and pages follow each other
        group.sort(key=lambda c: (int(c['source_page']), int(c['station_row_order'])))
        seq = []
        for c in group:
            node = resolve(c['aligned_station_row_label'], line, line_index, aliases, unresolved)
            if node is None:
                continue
            if seq and seq[-1][1] == node:      # a repeated label row (arrival then departure)
                continue
            seq.append(((int(c['source_page']), int(c['station_row_order'])), node, clock_to_s(c['printed_local_hhmm']), c['aligned_station_row_label']))
        if len(seq) < 2:
            # one printed time (the pocket sheet's Virar arrival of a Dahanu
            # Road train it prints in full elsewhere): kept aside, refused only
            # when no other sheet reads the train
            readings[(line, number)].append((sheet, [(node, s) for _, node, s, _ in seq], 'single_cell'))
            continue
        if spec.get('order') == 'printed_clock':
            # a sheet whose station rows the reader could not order (two tables
            # side by side): the train's stops in clock order, a clock before
            # noon after one past noon reading as the next day
            times = [s for _, _, s, _ in seq]
            if max(times) - min(times) > DAY_S / 2:
                seq = [(o, n, s + (DAY_S if s < DAY_S / 2 else 0), l) for o, n, s, l in seq]
            seq.sort(key=lambda x: x[2])
            ordered, direction = [(o, n, s) for o, n, s, _ in seq], 'printed_clock'
            if any(b[2] < a[2] for a, b in zip(ordered, ordered[1:])):
                ordered = None
        else:
            ordered, direction = sequence_times([(o, n, s) for o, n, s, _ in seq])
        if ordered is None:
            refused.append(dict(sheet=sheet, train=number, reason=direction, cells=len(group)))
            counts['refused'] += 1
            continue
        readings[(line, number)].append((sheet, [(node, s) for _, node, s in ordered], direction))
        counts['readings'] += 1
    for (line, number), reads in sorted(readings.items()):
        full = [r for r in reads if len(r[1]) >= 2]
        if not full:
            refused.append(dict(sheet=reads[0][0], train=number, reason='fewer_than_two_resolved_stops'))
            counts['refused'] += 1
            continue
        primaries = [r for r in full if sheets[r[0]].get('role', 'primary') == 'primary']
        supplements = [r for r in full if sheets[r[0]].get('role', 'primary') != 'primary']
        flags = {sheets[r[0]]['flag'] for r in supplements}
        if primaries:
            # a train printed on two primary sheets of one line continues from
            # one onto the other (the harbour line's Panvel-Goregaon trains
            # print their Panvel-Vadala leg on the up sheet and their
            # Vadala-Goregaon leg on the down sheet): the legs chain in time
            primaries.sort(key=lambda r: r[1][0][1])
            stops = list(primaries[0][1])
            chained = True
            for sheet, leg, _ in primaries[1:]:
                if leg[0][1] < stops[-1][1] - 60 or leg[0][1] - stops[-1][1] > 1800:
                    chained = False
                    break
                stops.extend(leg[1:] if leg[0][0] == stops[-1][0] else leg)
            if not chained:
                # two sheets print the same run (the Dahanu Road sheet prints a
                # train's whole Churchgate-Dahanu Road run, the pocket sheet
                # its Churchgate-Virar part): the fuller reading, when its
                # stops contain the other's
                longest = max(primaries, key=lambda r: len(r[1]))
                if all({n for n, _ in r[1]} <= {n for n, _ in longest[1]} for r in primaries):
                    stops = list(longest[1])
                    primaries = [longest]
                else:
                    refused.append(dict(sheet=primaries[1][0], train=number, reason='train_number_on_two_primary_sheets_not_chaining',
                                        other=primaries[0][0]))
                    counts['refused'] += 1
                    continue
            trains[(line, number)] = dict(line=line, number=number, sheet='+'.join(r[0] for r in primaries),
                                          role='primary', stops=stops, direction=primaries[0][2], flags=flags)
        else:
            sheet, stops, direction = supplements[0]
            trains[(line, number)] = dict(line=line, number=number, sheet=sheet, role='supplement',
                                          stops=stops, direction=direction, flags=flags)
        counts['trains_read'] += 1
    skipped = {label: n for (line, label), n in unresolved.items() if line == 'skipped'}
    unresolved = Counter({k: v for k, v in unresolved.items() if k[0] != 'skipped'})
    if unresolved:
        listing = '\n'.join('  %s: %r x%d' % (line, label, n) for (line, label), n in sorted(unresolved.items()))
        raise SystemExit('printed station labels no OSM station resolves (add them to '
                         'extract/transcriptions/suburban_station_labels.json):\n' + listing)
    # GTFS: a route per (line, direction, flag set, stopping pattern)
    stops_out, routes, trips, stop_times = {}, {}, [], []
    pattern_ids = {}
    with zipfile.ZipFile(city.path('schedules/baseline_bus.zip')) as bus:
        calendar = list(csv.DictReader(io.StringIO(bus.read('calendar.txt').decode('utf-8-sig'))))
    service_id = calendar[0]['service_id']
    per_line = Counter()
    per_sheet = Counter()
    for (line, number), t in sorted(trains.items()):
        nodes = tuple(n for n, _ in t['stops'])
        first_t, last_t = t['stops'][0][1], t['stops'][-1][1]
        towards = by_node[nodes[-1]]['name']
        flags = ''.join(sorted(t['flags']))
        pattern_key = (line, nodes, flags)
        if pattern_key not in pattern_ids:
            pattern_ids[pattern_key] = 'BASE_TT_%s_%s%s_P%d' % (line, normalise(towards).replace(' ', '')[:12],
                                                             ('_' + flags) if flags else '', len(pattern_ids) + 1)
            routes[pattern_ids[pattern_key]] = dict(
                route_id=pattern_ids[pattern_key], agency_id='BASELINE',
                route_short_name=lines[line]['short_name'] + ((' ' + flags) if flags else ''),
                route_long_name='%s to %s (%d stops%s)' % (by_node[nodes[0]]['name'], towards, len(nodes),
                                                          (', ' + flags) if flags else ''),
                route_type=lines[line]['route_type'])
        rid = pattern_ids[pattern_key]
        tid = 'BASE_TT_%s_%s' % (line, number)
        trips.append(dict(route_id=rid, service_id=service_id, trip_id=tid,
                          direction_id=0 if t['direction'] == 'sheet' else 1,
                          trip_short_name=number, timetable_sheet=t['sheet']))
        for index, (node, seconds) in enumerate(t['stops']):
            sid = 'BASE_OSM_' + node
            p = by_node[node]
            stops_out[sid] = dict(stop_id=sid, stop_name=p['name'] or sid,
                                  stop_lon=float(p['longitude_deg']), stop_lat=float(p['latitude_deg']))
            arrival = seconds if index else seconds
            departure = seconds + (dwell if 0 < index < len(t['stops']) - 1 else 0)
            stop_times.append(dict(trip_id=tid, arrival_time=clock(arrival), departure_time=clock(departure),
                                   stop_id=sid, stop_sequence=index))
        per_line[line] += 1
        per_sheet[t['sheet']] += 1
    def table(items, fields):
        out = io.StringIO(newline='')
        w = csv.DictWriter(out, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(items)
        return out.getvalue().encode('utf-8')
    content = {
        'stops.txt': table(sorted(stops_out.values(), key=lambda s: s['stop_id']), ['stop_id', 'stop_name', 'stop_lon', 'stop_lat']),
        'routes.txt': table(sorted(routes.values(), key=lambda r: r['route_id']), ['route_id', 'agency_id', 'route_short_name', 'route_long_name', 'route_type']),
        'trips.txt': table(trips, ['route_id', 'service_id', 'trip_id', 'direction_id', 'trip_short_name', 'timetable_sheet']),
        'stop_times.txt': table(stop_times, ['trip_id', 'arrival_time', 'departure_time', 'stop_id', 'stop_sequence']),
    }
    output = Path(city.path(OUT))
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, data in sorted(content.items()):
            entry = zipfile.ZipInfo(name)
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    published = {r['operator']: int(r['daily_services_count']) for r in rows('data/processed/observed/suburban_service_counts_202604.csv')
                 if r['category'] == 'All EMU local services'}
    by_operator = Counter()
    for (line, _), t in trains.items():
        by_operator[lines[line]['operator']] += 1
    audit = dict(
        source='published_timetable_cells_as_trips',
        sheets={s: dict(spec, trains=per_sheet.get(s, 0)) for s, spec in sheets.items()},
        trains=len(trains), routes=len(routes), stops=len(stops_out), stop_times=len(stop_times),
        trains_by_line=dict(per_line), trains_by_operator=dict(by_operator),
        published_daily_services=published,
        flagged=dict(Counter(f for t in trains.values() for f in t['flags'])),
        refused=refused, refused_count=len(refused),
        stops_skipped_no_osm_station={label: dict(cells=n, reason=aliases['skipped'][label]) for label, n in skipped.items()},
        output_sha256=fingerprint(output),
        limitations=[
            'The sheets are of different dates: each trip carries its sheet; no calendar exception (Sunday, holiday, '
            'block) is applied - every printed train runs on the modelled weekday.',
            'A printed time is a departure; the arrival is the same clock and the declared dwell is added at intermediate stops.',
            'A station label resolves to one OSM node; a station with separate platforms per line (Dadar, Kurla) takes '
            'the node the line\'s own relation names.',
            'The path between two stops is the mapper\'s (pt2matsim on the rail links), not the harbour-line path evidence.',
        ])
    Path(city.path(AUDIT)).write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: audit[k] for k in ('trains', 'routes', 'stops', 'trains_by_operator', 'published_daily_services', 'flagged', 'refused_count')}, indent=1))
    if refused:
        for r in refused[:12]:
            print('  refused', r)


if __name__ == '__main__':
    main()
