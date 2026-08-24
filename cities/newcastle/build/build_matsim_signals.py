#!/usr/bin/env python
"""Generate the explicit MATSim signal data model for the corridor (issue #73).

Rung 2 of the signalling dossier's ladder: fixed-time signal plans at the 14
corridor intersections, generated FROM THE SAME DECLARED VALUES the retired
SUMO retiming consumed (the A2 table's cycle / split / clearance / offset and
`A.signals.min_green_s`), against each scenario's OWN mapped network - plus
everything the double-count rule demands must land with them:

  * `signal_systems.xml` / `signal_groups.xml` / `signal_control.xml`
    (signals contrib v2.0 data model) per scenario;
  * a saturation-flow RE-CAPACITATION patch for the signalised approaches
    (a conventional link capacity is s x g/C - already metered; an explicit
    signal must meter an s-capacity link, never both: dossier 04 6.1);
  * a derived transit schedule with the implicit per-intersection delay
    REMOVED from the intervention mode's arrival offsets (the other half of
    "one representation per effect", 04 7.5) - derived from the already-
    transformed dwell schedule, never by re-running the mapper (3.5);
  * the per-green discharge check (04 6.2): at a 10-25% sample a short green
    discharges few vehicles; the report states the count per approach per
    green at 1% and 25% so nobody trusts a signal effect the discretisation
    cannot carry.

**Phase structure is stated, not faked.** The A2 split (45|15|30|10 over 4
phases) presumes movement-level control, but observed turn-lane coverage on
the corridor trunk is 16% (46 of 280 edges) - generating turn pockets and
protected-turn lanes from that would be invented geometry. So rung 2 lands at
LINK level: two green phases per intersection - corridor approaches (the
corridor split 45+15) and cross approaches (30+10), each road's turn share
folded into its own approach - with the tram group tied to the corridor phase
(a T-aspect moves with parallel traffic where unconflicted, 02 2). The
movement-level refinement stays OPEN on #73 until turn-lane data exists;
`timing_source=assumed (A2 proxy)` and the structure rule are labelled in the
report exactly as the SUMO build labelled them.

**Controller assignment follows the A2 variant**: `tsp_enabled` rows get
`CitysimTramPriority` (the custom controller, src/java_signals/), the rest run
`DefaultPlanbasedSignalSystemController`. The controller's own parameters are
declared registry fields bound to the `tramPriority` config module.

**Sequencing (9.75):** everything is built INERT - the outputs land under
`networks/matsim/signals/<S>/` and nothing consumes them until the batched
family boundary flips `A.signals.representation` to `explicit_signals`.

    python cities/newcastle/build/build_matsim_signals.py
"""

# This builder encodes THIS CITY's corridor, so it lives with the city.
import os as _os
import sys as _sys
_REPO = _os.path.dirname(_os.path.dirname(_os.path.dirname(
    _os.path.dirname(_os.path.abspath(__file__)))))
_sys.path.insert(0, _os.path.join(_REPO, 'src'))
import city as _city  # noqa: E402
import registry as _registry  # noqa: E402

import csv
import gzip
import json
import math
import os
import xml.etree.ElementTree as ET

CFG = _registry.load()

A2 = _city.path('data/processed/corridor/A2_signal_control_corridor.csv')
E1 = _city.path('scenarios/E1_scenarios.csv')
SCHEDULES = _city.path('networks', 'matsim', 'schedules')
OUT_ROOT = _city.path('networks', 'matsim', 'signals')
OUT_REPORT = os.path.join(OUT_ROOT, '_signals_report.json')

MIN_GREEN_S = CFG.get('A.signals.min_green_s')
JUNCTION_MATCH_M = CFG.get('A.signals.junction_match_m')
SAT_FLOW = CFG.get('A.signals.saturation_flow_veh_h_lane')
DELAY_PER_INT = CFG.get('A.signals.delay_per_intersection_s')
INTERVENTION_MODE = _city.descriptor()['intervention']['mode']
# the discharge check is computed at the declared sample sweep's ends
_fs = CFG.sweep('RUN.sample.fraction')
FRACTION_SWEEP = _fs['interval'] if isinstance(_fs, dict) else _fs

XMLNS = 'http://www.matsim.org/files/dtd'


def read_a2():
    by_variant = {}
    with open(A2, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            by_variant.setdefault(r['scenario_variant_ref'], []).append(r)
    return by_variant


def scenario_variants():
    out = {}
    with open(E1, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[r['scenario_id']] = r['signal_variant_ref']
    return out


def read_network(path):
    nodes, car_links, tram_links = {}, {}, {}
    with gzip.open(path, 'rb') as f:
        for ev, el in ET.iterparse(f, events=('end',)):
            if el.tag == 'node':
                nodes[el.get('id')] = (float(el.get('x')), float(el.get('y')))
                el.clear()
            elif el.tag == 'link':
                modes = (el.get('modes') or '').split(',')
                rec = dict(id=el.get('id'), frm=el.get('from'),
                           to=el.get('to'),
                           capacity=float(el.get('capacity')),
                           lanes=float(el.get('permlanes')))
                if 'car' in modes:
                    car_links[rec['id']] = rec
                if INTERVENTION_MODE in modes:
                    tram_links[rec['id']] = rec
                el.clear()
    return nodes, car_links, tram_links


def project(lon, lat):
    import pyproj
    if not hasattr(project, '_tf'):
        project._tf = __import__('pyproj').Transformer.from_crs(
            'EPSG:4326', _city.crs(), always_xy=True)
    return project._tf.transform(lon, lat)


def intersections(rows, nodes, car_links):
    """Each A2 intersection resolved to its NETWORK node set.

    The A2 cluster ids are OSM traffic-SIGNAL nodes (stop-line markers), and
    the network build simplifies most of them away - measured: 12 of 14
    intersections keep none of their cluster ids as network nodes, while the
    real junction survives as one or more nearby nodes (a dual carriageway is
    two or more). So the intersection is the SET of network nodes that carry
    car links within the declared `A.signals.junction_match_m` of the A2
    point - the same radius, and the same junctions-join semantics, the
    retired SUMO build used. Links BETWEEN nodes of the set are internal to
    the intersection; approaches are links entering the set from outside.
    An intersection that matches nothing is an error, not a skip - a corridor
    with 13 signalised intersections is a different corridor.
    """
    connected = set()
    for l in car_links.values():
        connected.add(l['frm'])
        connected.add(l['to'])
    out = []
    for r in rows:
        cluster = set(c for c in r['osm_node_id'].split(';') if c)
        cx, cy = project(float(r['lon']), float(r['lat']))
        matched = set()
        for nid in connected:
            x, y = nodes[nid]
            if (abs(x - cx) <= JUNCTION_MATCH_M
                    and abs(y - cy) <= JUNCTION_MATCH_M
                    and math.hypot(x - cx, y - cy) <= JUNCTION_MATCH_M):
                matched.add(nid)
        matched |= (cluster & connected)
        if not matched:
            raise SystemExit(
                '%s: no car-carrying network node within %g m of the A2 '
                'point' % (r['intersection_id'], JUNCTION_MATCH_M))
        out.append(dict(row=r, nodes=matched, x=cx, y=cy))
    return out


def corridor_axis(inters, i):
    """The corridor's direction AT intersection i: the bearing between its
    nearest two neighbours along the A2 set (or to its one nearest neighbour
    at the ends). Derived from the intersections themselves - no typed
    bearing."""
    me = inters[i]
    others = sorted((math.hypot(o['x'] - me['x'], o['y'] - me['y']), j)
                    for j, o in enumerate(inters) if j != i)
    a = inters[others[0][1]]
    b = inters[others[1][1]] if len(others) > 1 else me
    dx, dy = a['x'] - b['x'], a['y'] - b['y']
    if dx == dy == 0:
        dx, dy = a['x'] - me['x'], a['y'] - me['y']
    return math.atan2(dy, dx)


def bearing(nodes, link):
    (x1, y1), (x2, y2) = nodes[link['frm']], nodes[link['to']]
    return math.atan2(y2 - y1, x2 - x1)


def angle_diff(a, b):
    d = abs(a - b) % (2 * math.pi)
    d = min(d, 2 * math.pi - d)
    return min(d, math.pi - d)   # direction-agnostic: an axis, not a heading


def classify_approaches(inter, axis, nodes, car_links, tram_links):
    corridor, cross, tram = [], [], []
    for l in car_links.values():
        if l['to'] in inter['nodes'] and l['frm'] not in inter['nodes']:
            if angle_diff(bearing(nodes, l), axis) <= math.pi / 4:
                corridor.append(l)
            else:
                cross.append(l)
    for l in tram_links.values():
        if l['to'] in inter['nodes'] and l['frm'] not in inter['nodes']:
            tram.append(l)
    return corridor, cross, tram


def plan_timing(row, structure):
    """The plan from the A2 declared values - the retimed-TLS arithmetic
    ported from the retired SUMO build: the split taken in order, each road's
    turn share folded into its own approach phase, the clearance between
    phases, greens floored at the declared minimum.

    two_phase: greens = [corridor (split 1+2), cross (split 3+4)].
    midblock_crossing: greens = [all vehicle phases (split 1+2+3),
    pedestrian interruption (split 4, carrying NO car signals - it is red
    time for every car approach)]."""
    cycle = float(row['cycle_time_s'])
    clearance = float(row['ped_clearance_s'])
    split = [float(x) for x in row['phase_split_pct'].split('|')]
    if structure == 'two_phase':
        weights = [split[0] + split[1], split[2] + split[3]]
    else:
        weights = [split[0] + split[1] + split[2], split[3]]
    inter = clearance * len(weights)
    usable = max(cycle - inter, len(weights) * MIN_GREEN_S)
    tot = sum(weights)
    greens = [max(MIN_GREEN_S, usable * w / tot) for w in weights]
    onsets = []
    t = 0.0
    for g in greens:
        onsets.append((int(round(t)), int(round(t + g))))
        t += g + clearance
    realised = t
    return cycle, onsets, greens, clearance, realised


def build_variant(scenario, variant_rows, nodes, car_links, tram_links):
    inters = intersections(variant_rows, nodes, car_links)
    systems = []
    for i, inter in enumerate(inters):
        axis = corridor_axis(inters, i)
        corridor, cross, tram = classify_approaches(
            inter, axis, nodes, car_links, tram_links)
        if not corridor:
            raise SystemExit(
                '%s/%s: no corridor-axis car approach found - the bearing '
                'derivation or the junction match is wrong; refuse rather '
                'than emit a signal facing nothing.'
                % (scenario, inter['row']['intersection_id']))
        # A corridor site with NO cross-street car approach is a MID-BLOCK
        # crossing signal - 8 of the 14 were installed in 2018 for the light
        # rail, two named "light rail crossing" (9.24), and those control
        # pedestrians/tram interaction, not a cross street. Their structure
        # is one car phase interrupted by the pedestrian phase.
        structure = 'two_phase' if cross else 'midblock_crossing'
        systems.append(dict(inter=inter, corridor=corridor, cross=cross,
                            tram=tram, structure=structure))
    return systems


def emit_xml(scenario, variant, systems, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    row0 = systems[0]['inter']['row']
    tsp = row0['tsp_enabled'] == '1'
    controller = ('CitysimTramPriority' if tsp
                  else 'DefaultPlanbasedSignalSystemController')

    sys_root = ET.Element('signalSystems', {'xmlns': XMLNS})
    grp_root = ET.Element('signalGroups', {'xmlns': XMLNS})
    ctl_root = ET.Element('signalControl', {'xmlns': XMLNS})

    for s in systems:
        row = s['inter']['row']
        sid = row['intersection_id']
        system = ET.SubElement(sys_root, 'signalSystem', {'id': sid})
        sigs = ET.SubElement(system, 'signals')
        groups = {'corridor': [], 'cross': [], 'tram': []}
        for kind in ('corridor', 'cross', 'tram'):
            for l in s[kind]:
                sig_id = '%s.%s' % (sid, l['id'])
                ET.SubElement(sigs, 'signal',
                              {'id': sig_id, 'linkIdRef': l['id']})
                groups[kind].append(sig_id)
        gsys = ET.SubElement(grp_root, 'signalSystem', {'refId': sid})
        for kind, name in (('corridor', 'corridor'), ('cross', 'cross'),
                           ('tram', 'tram')):
            if not groups[kind]:
                continue
            g = ET.SubElement(gsys, 'signalGroup', {'id': name})
            for sig_id in groups[kind]:
                ET.SubElement(g, 'signal', {'refId': sig_id})

        cycle, onsets, greens, clearance, realised = plan_timing(
            row, s['structure'])
        csys = ET.SubElement(ctl_root, 'signalSystem', {'refId': sid})
        ctrl = ET.SubElement(csys, 'signalSystemController')
        ET.SubElement(ctrl, 'controllerIdentifier').text = controller
        plan = ET.SubElement(ctrl, 'signalPlan', {'id': '1'})
        ET.SubElement(plan, 'cycleTime', {'sec': str(int(cycle))})
        ET.SubElement(plan, 'offset', {'sec': str(int(float(row['offset_s'])))})
        # midblock: every car approach shares phase 0 (the ped interruption
        # carries no car signals); two_phase: corridor 0, cross 1. The tram
        # always moves along the corridor axis, so its group ties to the
        # corridor phase (T-aspect with parallel traffic, 02 2).
        phase_of = ({'corridor': 0, 'cross': 1, 'tram': 0}
                    if s['structure'] == 'two_phase'
                    else {'corridor': 0, 'cross': 0, 'tram': 0})
        for kind, name in (('corridor', 'corridor'), ('cross', 'cross'),
                           ('tram', 'tram')):
            if not groups[kind]:
                continue
            onset, dropping = onsets[phase_of[kind]]
            gs = ET.SubElement(plan, 'signalGroupSettings', {'refId': name})
            ET.SubElement(gs, 'onset', {'sec': str(onset)})
            ET.SubElement(gs, 'dropping', {'sec': str(dropping)})

    for name, root in (('signal_systems.xml', sys_root),
                       ('signal_groups.xml', grp_root),
                       ('signal_control.xml', ctl_root)):
        ET.indent(root)
        ET.ElementTree(root).write(os.path.join(out_dir, name),
                                   encoding='UTF-8', xml_declaration=True)
    return controller


def capacity_patch(systems, out_dir):
    """The saturation-flow re-capacitation half of the double-count rule."""
    rows = []
    for s in systems:
        for kind in ('corridor', 'cross'):
            for l in s[kind]:
                rows.append(dict(
                    intersection_id=s['inter']['row']['intersection_id'],
                    approach=kind, link=l['id'], lanes=l['lanes'],
                    capacity_metered_veh_h=l['capacity'],
                    capacity_saturation_veh_h=round(SAT_FLOW * l['lanes'], 1)))
    path = os.path.join(out_dir, 'signals_capacity_patch.csv')
    with open(path, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    return rows


def discharge_check(systems, greens_by_system):
    """Vehicles per green per approach at the sample sweep's ends (04 6.2)."""
    lo, hi = FRACTION_SWEEP
    checks = []
    for s, (greens, _cycle) in zip(systems, greens_by_system):
        cross_g = greens[1] if s['structure'] == 'two_phase' else greens[0]
        for kind, g in (('corridor', greens[0]), ('cross', cross_g)):
            for l in s[kind]:
                sat = SAT_FLOW * l['lanes']
                checks.append(dict(
                    intersection_id=s['inter']['row']['intersection_id'],
                    approach=kind, link=l['id'], green_s=round(g, 1),
                    veh_per_green_at_low=round(sat * g / 3600.0 * lo, 2),
                    veh_per_green_at_high=round(sat * g / 3600.0 * hi, 2)))
    return checks


def signal_nodes_between_stops(route, node_to_intersection, node_of_link):
    """How many DISTINCT signalised intersections each inter-stop segment
    crosses, walking the route's own link sequence. An intersection is a SET
    of network nodes (dual carriageways, the junction-match radius), so the
    count is over intersection ids, never over nodes - counting nodes charged
    one crossing several times over."""
    links = [l.get('refId') for l in route.find('route').findall('link')]
    prof = route.find('routeProfile').findall('stop')
    stop_links = [s.get('refId').rsplit('link:', 1)[1] for s in prof]
    counts = []
    seg = -1
    crossed = set()
    for lid in links:
        if seg >= 0:
            iid = node_to_intersection.get(node_of_link.get(lid))
            if iid is not None:
                crossed.add(iid)
        if seg + 1 < len(stop_links) and lid == stop_links[seg + 1]:
            if seg >= 0:
                counts.append(len(crossed))
            crossed = set()
            seg += 1
    return counts


def transform_schedule(scenario, systems, out_dir):
    """Remove the implicit per-intersection delay from the intervention mode's
    arrival offsets - the schedule half of "one representation per effect".

    THE AMOUNT REMOVED IS THE VARIANT'S OWN: each A2 signal variant declares
    `mean_delay_to_tram_s`, which is precisely the per-intersection delay
    `build_scenario_schedules.py` baked into THAT variant's scheduled times
    (S2 24.8 s, S2b 6.2 s after its 75% priority removal, S2c 9.9 s, S0 0).
    Removing the generic A.signals.delay_per_intersection_s everywhere would
    over-subtract from every variant whose schedule already carries a partial
    removal - measured: S2b's segment 2 went negative on exactly that error.

    Input preference: the dwell-transformed schedule (#74), so the explicit
    arm's derived schedule carries native dwell AND no implicit signal delay;
    falls back to the plain mapped schedule with a stated note."""
    sched_dir = os.path.join(SCHEDULES, scenario)
    src = os.path.join(sched_dir, 'transitSchedule_dwell.xml.gz')
    src_note = 'dwell-transformed (#74)'
    if not os.path.exists(src):
        src = os.path.join(sched_dir, 'transitSchedule.xml.gz')
        src_note = 'plain mapped (no dwell variant exists for this scenario)'
    with gzip.open(src, 'rt', encoding='utf-8') as f:
        tree = ET.parse(f)
    root = tree.getroot()

    node_to_intersection = {}
    for s in systems:
        for nid in s['inter']['nodes']:
            node_to_intersection[nid] = s['inter']['row']['intersection_id']
    # the variant's own embedded per-intersection tram delay (constant across
    # the 14 rows of one variant, asserted)
    delays = {float(s['inter']['row']['mean_delay_to_tram_s'])
              for s in systems}
    if len(delays) != 1:
        raise SystemExit('%s: mean_delay_to_tram_s differs across the '
                         'variant rows (%s)' % (scenario, sorted(delays)))
    embedded_delay = delays.pop()

    # node reached at the END of each link, from the scenario network
    net_path = os.path.join(SCHEDULES, scenario, 'network.xml.gz')
    node_of_link = {}
    with gzip.open(net_path, 'rb') as f:
        for ev, el in ET.iterparse(f, events=('end',)):
            if el.tag == 'link':
                node_of_link[el.get('id')] = el.get('to')
                el.clear()

    def parse(t):
        h, m, s2 = t.split(':')
        return int(h) * 3600 + int(m) * 60 + int(s2)

    def fmt(v):
        return '%02d:%02d:%02d' % (v // 3600, (v % 3600) // 60, v % 60)

    routes_touched = 0
    total_removed = 0
    for line in root.iter('transitLine'):
        for route in line.findall('transitRoute'):
            if route.findtext('transportMode') != INTERVENTION_MODE:
                continue
            counts = signal_nodes_between_stops(route, node_to_intersection,
                                                node_of_link)
            prof = route.find('routeProfile').findall('stop')
            if len(counts) != len(prof) - 1:
                raise SystemExit(
                    '%s/%s: segment/stop mismatch (%d segments for %d stops) '
                    '- the route link walk is wrong, refuse to emit.'
                    % (scenario, route.get('id'), len(counts), len(prof)))
            shift = 0
            touched = False
            for k in range(1, len(prof)):
                removed = int(round(embedded_delay * counts[k - 1]))
                arr = parse(prof[k].get('arrivalOffset'))
                dep = parse(prof[k].get('departureOffset'))
                hold = dep - arr
                prev_dep = parse(prof[k - 1].get('departureOffset'))
                shift += removed
                new_arr = arr - shift
                if new_arr <= prev_dep:
                    raise SystemExit(
                        '%s/%s: removing %ds of signal delay leaves segment '
                        '%d with no running time - the implicit delay '
                        'exceeds the scheduled gap; the A2 decomposition and '
                        'the mapped timeline disagree.'
                        % (scenario, route.get('id'), shift, k))
                prof[k].set('arrivalOffset', fmt(new_arr))
                if k < len(prof) - 1:
                    prof[k].set('departureOffset', fmt(new_arr + max(hold, 0)))
                touched = True
            if touched:
                routes_touched += 1
                total_removed = max(total_removed, shift)
    dst = os.path.join(out_dir, 'transitSchedule_signals.xml.gz')
    with gzip.open(dst, 'wt', encoding='utf-8') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE transitSchedule SYSTEM '
                '"http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">\n')
        f.write(ET.tostring(root, encoding='unicode'))
    return dict(source=src_note, routes_touched=routes_touched,
                embedded_delay_per_intersection_s=embedded_delay,
                max_delay_removed_s=total_removed,
                output=_city.rel(dst))


def main():
    os.makedirs(OUT_ROOT, exist_ok=True)
    a2 = read_a2()
    variants = scenario_variants()
    report = dict(
        purpose='explicit MATSim signal data model (issue #73, rung 2+4)',
        timing_source='assumed (A2 proxy) - scats_phasing stays unobtained',
        implicit_delay_per_intersection_s=DELAY_PER_INT,
        schedule_removal_basis='each variant removes ITS OWN embedded '
                               'mean_delay_to_tram_s, not the generic '
                               'A.signals.delay_per_intersection_s above - '
                               'see transform_schedule',
        phase_structure=(
            'link-level two-phase: corridor approaches (A2 split 45+15) vs '
            'cross approaches (30+10), each road\'s turn share folded into '
            'its own approach; the tram group runs with the corridor phase '
            '(T-aspect with parallel traffic, dossier 02 2). Movement-level '
            'lanes DEFERRED: observed turn-lane coverage on the corridor '
            'trunk is 46 of 280 edges (16%) - protected-turn lanes from '
            'that would be invented geometry. Open on #73.'),
        double_count_rule=(
            'both halves land together: signals_capacity_patch.csv re-raises '
            'each signalised approach to saturation flow x lanes, and '
            'transitSchedule_signals.xml.gz removes '
            'A.signals.delay_per_intersection_s per crossed intersection '
            'from the intervention mode\'s arrival offsets. One '
            'representation per effect (dossier 04 6.1/7.5); '
            'A.signals.representation is the switch code checks.'),
        activation='INERT until the batched family boundary flips '
                   'A.signals.representation to explicit_signals',
        scenarios={})
    for scenario, variant in sorted(variants.items()):
        if variant not in a2:
            continue
        net_path = os.path.join(SCHEDULES, scenario, 'network.xml.gz')
        if not os.path.exists(net_path):
            report['scenarios'][scenario] = dict(
                skipped='no mapped network for this scenario')
            continue
        nodes, car_links, tram_links = read_network(net_path)
        systems = build_variant(scenario, a2[variant], nodes, car_links,
                                tram_links)
        out_dir = os.path.join(OUT_ROOT, scenario)
        controller = emit_xml(scenario, variant, systems, out_dir)
        patch = capacity_patch(systems, out_dir)
        greens = []
        for s in systems:
            cycle, onsets, g, clearance, realised = plan_timing(
                s['inter']['row'], s['structure'])
            greens.append((g, cycle))
        checks = discharge_check(systems, greens)
        worst = min(c['veh_per_green_at_high'] for c in checks)
        sched = transform_schedule(scenario, systems, out_dir)
        n_tram = sum(1 for s in systems if s['tram'])
        report['scenarios'][scenario] = dict(
            signal_variant=variant, controller=controller,
            systems=len(systems),
            approaches=sum(len(s['corridor']) + len(s['cross'])
                           for s in systems),
            systems_with_tram_group=n_tram,
            midblock_systems=sum(1 for s in systems
                                 if s['structure'] == 'midblock_crossing'),
            capacity_patch_rows=len(patch),
            discharge_worst_veh_per_green_at_25pct=worst,
            discharge_check=('a green that discharges under ~1 vehicle at '
                             'the run fraction cannot show a signal effect '
                             '(04 6.2); check per-approach values in '
                             'signals_capacity_patch context before '
                             'trusting any explicit-arm result'),
            schedule_transform=sched)
        print('%-4s %-24s %2d systems  %3d approaches  %d tram-grouped  '
              'worst %.2f veh/green@25%%  sched -%ds'
              % (scenario, variant + ' [' + controller + ']', len(systems),
                 report['scenarios'][scenario]['approaches'], n_tram, worst,
                 sched['max_delay_removed_s']))
    with open(OUT_REPORT, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print('report -> %s' % OUT_REPORT)


if __name__ == '__main__':
    main()
