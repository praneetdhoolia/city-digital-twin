#!/usr/bin/env python
"""Convert the OSM extracts and every GTFS feed into a MATSim network + schedules.

Runs pt2matsim 26.6 (see `src/setup/bootstrap_toolchain.py`) in three stages:

  1. merge the road, railway and footway OSM extracts into one multimodal
     file, since pt2matsim reads a single .osm and the P1 extracts are themed;
  2. `Osm2MultimodalNetwork` -> the base MATSim network in EPSG:28356, using the
     capacity and speed defaults recorded in DECISIONS.md 3.2 rather than
     pt2matsim's own, so the MATSim and SUMO corridors share one set of numbers;
     the footway classes (`A.network.path_modes_by_class`) become walk- and
     bike-capable links, then each way's own foot=/bicycle= tag overrides its
     class default (`A.network.path_access_overrides`, #183);
  3. `Gtfs2TransitSchedule` + `PublicTransitMapper` for each of the 5 era feeds
     and 10 scenario feeds -> mapped schedules and their networks.

The four E1 road variants are applied as **link-attribute patches** over the one
base network, from `data/processed/network/A1_road_variant_patches.csv`. They are
not four independent conversions: the variants differ only in lane count and
kerbside use on corridor edges, never in topology, so building them as deltas is
what makes 'scenario networks differ only where E1 says they should' a structural
property rather than a diff assertion after the fact.

Determinism: the OSM merge preserves source file order, the configs are written
from the tables in this file, and Java's GZIPOutputStream stamps MTIME=0, so a
rebuilt network hashes identically to the one in data/MANIFEST.csv.

Usage:
    python src/build/build_matsim_network.py                # everything
    python src/build/build_matsim_network.py --stage network
    python src/build/build_matsim_network.py --stage schedules --only S2,base2026
    python src/build/build_matsim_network.py --workers 3
"""

import city as _city
import os
import re
import csv
import json
import gzip
import time
import hashlib
import shutil
import zipfile
import argparse
import subprocess
import collections
import glob
import concurrent.futures as futures

import bootstrap_toolchain as tc
import registry as _registry
from registry import param_config as _param_config


def fwd(path):
    return path.replace(os.sep, '/')

OUT = _city.path('networks/matsim')

# Which of this script's inputs feed which of its outputs (#159), read
# statically by src/build/build_manifest.py. pt2matsim converts the Overpass
# road, rail and signal extracts into the MATSim network and maps each GTFS
# era and scenario feed onto it in the same pass, so every file under
# networks/matsim that this script writes - base, variants and the mapped
# schedules - descends from all of them. The signals, crossings and
# charging-dwell subtrees are other scripts' outputs and carry their own
# lineage entries.
#
# EXCEPT the vehicles (#165). pt2matsim writes transitVehicles.xml.gz in the
# same pass, but that file is not mapped onto anything: it carries the GTFS
# vehicle types and their published capacities, one vehicle per departure, and
# NO link id, node id, coordinate or osm reference (measured over all 15 of
# them, DECISIONS.md 9.159). The assembler downstream already declares its own
# copy against the schedules alone, so the package labelled the DERIVED copy
# CC-BY while its own SOURCE was ODbL - a file cannot be freer than what it was
# cut from, and the contradiction was the blanket glob's, not the assembler's.
OUTPUT_INPUTS = {
    'networks/matsim/*': [
        'networks/osm/roads.osm',
        'networks/osm/railways.osm',
        'networks/osm/signals.osm',
        'networks/osm/footways.osm',
        'data/processed/network/A1_road_variant_patches.csv',
        'scenarios/E1_road_variants.csv',
        'schedules'],
    'networks/matsim/schedules/*/transitVehicles.xml.gz': ['schedules'],
}

WORK = os.path.join(OUT, '_work')
CRS = _city.crs()
PATCHES = _city.path('data/processed/network/A1_road_variant_patches.csv')
E1_ROAD_VARIANTS = _city.path('scenarios/E1_road_variants.csv')
JAVA_XMX = '-Xmx6g'

# The signals extract is merged for its `type=restriction` relations - the road
# extract carries none, so without it pt2matsim writes no `disallowedNextLinks`
# and every banned turn on the corridor would silently vanish from the network.
# The footway extract (#183) carries the 40,203 footway, path, cycleway, steps,
# track, pedestrian, bridleway and corridor ways - and 830 road ways it shares
# with the road extract, which the merge keeps once, from the road extract.
# Footways meet the roads at their shared OSM nodes (26,615 of them, measured
# 12 September 2026): a crossing way ends on the road node it crosses, which
# is what makes the walk graph one graph rather than a road graph plus islands.
OSM_INPUTS = [_city.path('networks/osm/roads.osm'),
              _city.path('networks/osm/railways.osm'),
              _city.path('networks/osm/signals.osm'),
              _city.path('networks/osm/footways.osm')]

# EVERY GTFS BUNDLE THE CITY HOLDS IS A FEED TO MAP - the era feeds under
# schedules/ and the scenario variants under schedules/scenarios/. The list
# was fifteen of one city's feed names typed into the framework (eighth
# project report, 11 September 2026); a second city inherited them. Derived
# from what is on disk, sorted so the build order is the same on every
# machine.
FEEDS = collections.OrderedDict(sorted(
    [(os.path.splitext(os.path.basename(z))[0], z)
     for pattern in ('schedules/*.zip', 'schedules/scenarios/*.zip')
     for z in glob.glob(_city.path(pattern))]))

# All three day types are converted into a single schedule ("all"). The era and
# scenario feeds namespace their trip ids by day type (WEEKDAY./SAT./SUN., see
# DECISIONS.md 11), so a run selects its day type by prefix without needing three
# separate mapped schedules - and the route set that PublicTransitMapper has to
# map is nearly identical across day types anyway.
GTFS_DAY_PARAM = 'all'

def log(msg):
    print('%s  %s' % (time.strftime('%H:%M:%S'), msg), flush=True)


def java(args, tag):
    j, jar = tc.require()   # (java, pt2matsim jar) since the SUMO retirement (47f63c7)
    cmd = [j, JAVA_XMX, '-cp', jar] + args
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    dt = time.time() - t0
    logdir = os.path.join(WORK, 'logs')
    os.makedirs(logdir, exist_ok=True)
    with open(os.path.join(logdir, tag + '.log'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(p.stdout or '')
        f.write('\n---- stderr ----\n')
        f.write(p.stderr or '')
    if p.returncode != 0:
        tail = '\n'.join((p.stderr or p.stdout or '').strip().splitlines()[-25:])
        raise SystemExit('pt2matsim failed (%s, exit %d)\n%s' % (tag, p.returncode, tail))
    return dt


# ---------------------------------------------------------------------------
# stage 1: merge the themed OSM extracts
# ---------------------------------------------------------------------------
def merge_osm(dest):
    """One .osm carrying the road and railway extracts, elements in OSM order.

    Written by hand rather than with an OSM tool so the pipeline keeps its P1
    dependency footprint (lxml only) and so the merge order - and therefore the
    output digest - is fixed by this function, not by a library's iteration.
    """
    from lxml import etree
    # the cached merge is reused only for the SAME inputs: a harvest added to
    # OSM_INPUTS (the footways, #183) or a re-harvested extract must re-merge,
    # and a file that merely exists cannot say what it was merged from
    inputs_key = [dict(path=_city.rel(p), bytes=os.path.getsize(p),
                       sha256=_sha256(p)) for p in OSM_INPUTS]
    key_path = dest + '.inputs.json'
    if os.path.exists(dest) and os.path.exists(key_path):
        with open(key_path, encoding='utf-8') as f:
            if json.load(f) == inputs_key:
                log('   merged OSM already present (%s, %.0f MB) from these inputs'
                    % (dest, os.path.getsize(dest) / 1e6))
                return dest
        log('   merged OSM present but from other inputs - re-merging')
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    seen = {'node': set(), 'way': set(), 'relation': set()}
    counts = collections.Counter()
    tmp = dest + '.part'
    with open(tmp, 'wb') as out:
        out.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        out.write(b'<osm version="0.6" generator="build_matsim_network.py">\n')
        for kind in ('node', 'way', 'relation'):
            for src in OSM_INPUTS:
                ctx = etree.iterparse(src, events=('end',), tag=(kind,))
                for _, el in ctx:
                    i = el.get('id')
                    if i in seen[kind]:
                        el.clear()
                        continue
                    seen[kind].add(i)
                    counts[kind] += 1
                    out.write(etree.tostring(el, encoding='utf-8'))
                    el.clear()
                    while el.getprevious() is not None:
                        del el.getparent()[0]
                del ctx
                log('   %-8s after %s: %d' % (kind, os.path.basename(src), counts[kind]))
        out.write(b'</osm>\n')
    os.replace(tmp, dest)
    with open(key_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(inputs_key, f, indent=2)
    log('   merged -> %s (%.0f MB) %s' % (dest, os.path.getsize(dest) / 1e6, dict(counts)))
    return dest


def _sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# stage 2: base network
# ---------------------------------------------------------------------------
def way_defaults(cfg):
    """The pt2matsim wayDefaultParams, DERIVED from the declared class tables.

    These were a 54-number table in this module, and the comment above it said
    it was kept here "so that the MATSim network, the SUMO corridor and
    A1_road_edges.csv cannot drift apart". They had drifted: six road classes
    carried a different free speed from `A.road.speed_default`, in both
    directions - motorway 100 against 110, trunk 80 against 60, and
    motorway_link, primary_link, secondary_link and service besides. Nothing
    compared them, because a second copy with no `legacy_symbol` is invisible to
    `check_legacy_drift.py`.

    There is one copy now. Road classes come from `A.road.*_default`, which is
    what `A1_road_edges.csv` and the SUMO corridor already read; railway classes
    come from `A.network.railway_*`, because a railway is not a road and folding
    it into a road table is what allowed the drift to hide.
    """
    lanes = cfg.get('A.road.lanes_default')
    speed = cfg.get('A.road.speed_default')
    capacity = cfg.get('A.road.capacity_default')
    rail_speed = cfg.get('A.network.railway_speed_default_kmh')
    rail_capacity = cfg.get('A.network.railway_lane_capacity_veh_h')
    oneway = cfg.get('A.network.way_default_oneway')
    subnets = cfg.get('A.network.routable_subnetworks')
    # the footway classes (#183): walk- and bike-capable links at the two
    # declared mode speeds, one lane, uncongested by definition, two-way
    # unless the way's own oneway tag says otherwise (pt2matsim reads it)
    path_modes = cfg.get('A.network.path_modes_by_class')
    path_capacity = cfg.get('A.network.path_lane_capacity_veh_h')
    walk_ms = float(cfg.get('A.transit.walk_speed_ms'))
    bike_ms = float(cfg.get('B.bike.speed_ms'))

    # Which subnetwork admits a class decides the modes written beside it, so
    # the two cannot disagree: a busway that admitted `bus` here but sat outside
    # the bus subnetwork would carry routes the router cannot reach.
    modes_of = {}
    for value in list(speed) + list(rail_speed):
        if value in rail_speed:
            modes_of[value] = ['rail'] if value == 'rail' else ['light_rail']
        elif value == 'busway':
            modes_of[value] = sorted(set(subnets.get('bus', ['car'])))
        else:
            modes_of[value] = ['car']

    out = {}
    for value in sorted(set(speed) | set(rail_speed)):
        if value in path_modes:
            raise SystemExit('%s is both a road/railway class and a path class '
                             '(A.network.path_modes_by_class) - one table must own it' % value)
        is_rail = value in rail_speed
        kmh = rail_speed[value] if is_rail else speed[value]
        out[value] = dict(
            osmKey='railway' if is_rail else 'highway',
            lanes=float(1 if is_rail else lanes.get(value, 1)),
            # pt2matsim reads free speed in metres per second; the registry
            # declares km/h, because km/h is the unit the speed instrument and
            # every road class table are written in.
            freespeed=round(float(kmh) / 3.6, 6),
            laneCapacity=float(rail_capacity if is_rail
                               else capacity.get(value, 0.0)),
            oneway=bool(oneway.get(value, False)),
            allowedTransportModes=modes_of[value])
    for value in sorted(path_modes):
        modes = list(path_modes[value])
        ms = bike_ms if 'bike' in modes else walk_ms
        out[value] = dict(
            osmKey='highway', lanes=1.0, freespeed=round(ms, 6),
            laneCapacity=float(path_capacity), oneway=False,
            allowedTransportModes=modes)
    return out


def config_runtime_osm(cfg, osm_file, network_out):
    """Paths, the city's projection, and the derived way defaults."""
    runtime = {
        'OsmConverter.osmFile': (fwd(osm_file), 'path', 'merged OSM extract'),
        'OsmConverter.outputNetworkFile': (fwd(network_out), 'path', 'base network'),
        'OsmConverter.outputCoordinateSystem': (_city.crs(), 'identity',
                                                'city.json crs.epsg'),
    }
    identity = ('A.road.lanes_default / A.road.speed_default / '
                'A.road.capacity_default for a highway class, '
                'A.network.railway_speed_default_kmh and '
                'A.network.railway_lane_capacity_veh_h for a railway class, '
                'A.network.path_modes_by_class with A.transit.walk_speed_ms or '
                'B.bike.speed_ms and A.network.path_lane_capacity_veh_h for a '
                'path class; free speed converted km/h -> m/s')
    for param in ('osmKey', 'lanes', 'freespeed', 'laneCapacity', 'oneway',
                  'allowedTransportModes'):
        runtime['OsmConverter.wayDefaultParams[*].%s' % param] = (
            {v: d[param] for v, d in way_defaults(cfg).items()}, 'derived', identity)
    return runtime


def write_osm_config(path, osm_file, network_out, cfg=None):
    """Emit the pt2matsim OsmConverter config from the registry."""
    cfg = cfg if cfg is not None else _registry.load()
    runtime = config_runtime_osm(cfg, osm_file, network_out)
    leaks = _param_config.closure('pt2matsim_osm', cfg, runtime)
    if leaks:
        raise SystemExit('the OSM converter config carries %d parameter(s) from '
                         'neither a field nor a declared role: %s' % (len(leaks), leaks))
    return _param_config.write(path, 'pt2matsim_osm', cfg, runtime)


def build_base_network():
    os.makedirs(os.path.join(OUT, 'base'), exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    osm = merge_osm(os.path.join(WORK, 'multimodal.osm'))
    net = os.path.join(OUT, 'base', 'network.xml.gz')
    cfg = write_osm_config(os.path.join(WORK, 'osm_converter.xml'), osm, net)
    log('Osm2MultimodalNetwork -> %s' % net)
    dt = java(['org.matsim.pt2matsim.run.Osm2MultimodalNetwork', cfg], 'osm2network')
    log('   done in %.0f s, %.0f MB' % (dt, os.path.getsize(net) / 1e6))
    build_base_network.access_report = apply_path_access_tags(net)
    return net


PATH_HIGHWAY_RE = re.compile(r'name="osm:way:highway"[^>]*>([^<]+)<')


def osm_access_tags(keys):
    """way id -> {access key: value} over every merged OSM input, for the keys
    the override declares. Read from the harvest itself: pt2matsim keeps a
    fixed subset of tags as `osm:way:*` link attributes (highway, name,
    footway, lanes, oneway, access, ...) and foot= and bicycle= are not in it
    (measured on the 12 September 2026 base network)."""
    from lxml import etree
    out = {}
    for src in OSM_INPUTS:
        for _, el in etree.iterparse(src, events=('end',), tag='way'):
            tags = {t.get('k'): (t.get('v') or '').strip()
                    for t in el.iter('tag') if t.get('k') in keys}
            if tags:
                out.setdefault(el.get('id'), tags)      # first extract wins, as in the merge
            el.clear()
            while el.getprevious() is not None:
                del el.getparent()[0]
    return out


def apply_path_access_tags(net_path, cfg=None):
    """A path link's own access tags override its class default (#183).

    pt2matsim writes every path-class link with the modes its class admits
    (`A.network.path_modes_by_class`) and reads no access tag itself. This
    pass does: `A.network.path_access_overrides` maps each OSM access key to
    the mode it governs (`all` for the general access= key) and says which
    values grant and which deny; keys apply in the declared order, so a
    specific foot= or bicycle= tag overrides a general access= tag, as the
    OSM access hierarchy says it should. A cycleway tagged foot=no loses
    walk, a footway tagged bicycle=yes gains bike, a private track loses
    both, and a link whose override strips its last mode is dropped from the
    network with its count reported - a link with no mode is one nothing can
    use. Road links are left alone: their walk/bike rule is the class-based
    one applied at run-input assembly.

    Rewritten in place with a zero-header gzip so the base network stays
    byte-reproducible.
    """
    cfg = cfg if cfg is not None else _registry.load()
    classes = set(cfg.get('A.network.path_modes_by_class'))
    ov = cfg.get('A.network.path_access_overrides')
    keys, grant, deny = ov['keys'], set(ov['grant']), set(ov['deny'])
    tags_of = osm_access_tags(set(keys))
    with gzip.open(net_path, 'rt', encoding='utf-8') as f:
        xml = f.read()
    counts = collections.Counter()

    def rewrite(m):
        s = m.group(0)
        hw = PATH_HIGHWAY_RE.search(s)
        if not hw or hw.group(1).strip() not in classes:
            return s
        counts['path_links'] += 1
        head_end = s.index('>')
        head, tail = s[:head_end], s[head_end:]
        mm = re.search(r'modes="([^"]*)"', head)
        modes = [x for x in mm.group(1).split(',') if x]
        wid = WAY_ID_RE.search(tail)
        tags = tags_of.get(wid.group(1), {}) if wid else {}
        before = list(modes)
        for key, mode in keys.items():
            v = tags.get(key)
            if v is None:
                continue
            governed = list(before) if mode == 'all' else [mode]
            for g in governed:
                if v in grant and g not in modes and mode != 'all':
                    modes.append(g)
                    counts['%s=%s grants %s' % (key, v, g)] += 1
                elif v in deny and g in modes:
                    modes.remove(g)
                    counts['%s=%s denies %s' % (key, v, g)] += 1
        if modes == before:
            return s
        if not modes:
            counts['links_dropped_no_mode_left'] += 1
            return ''
        counts['links_rewritten'] += 1
        return head[:mm.start()] + 'modes="%s"' % ','.join(sorted(modes)) + head[mm.end():] + tail

    body = LINK_BLOCK_RE.sub(rewrite, xml)
    with open(net_path, 'wb') as fh:
        g = gzip.GzipFile(fileobj=fh, mode='wb', mtime=0)
        g.write(body.encode('utf-8'))
        g.close()
    log('   access tags over %d path links: %s' % (
        counts.pop('path_links', 0), dict(counts) or 'no override fired'))
    return dict(counts)


# ---------------------------------------------------------------------------
# stage 3: E1 road variants as link-attribute patches
# ---------------------------------------------------------------------------
LINK_BLOCK_RE = re.compile(r'<link\b.*?</link>', re.S)
ATTR_RE = re.compile(r'(\w[\w:]*)="([^"]*)"')
WAY_ID_RE = re.compile(r'name="osm:way:id"[^>]*>(\d+)<')
DISALLOWED_RE = re.compile(
    r'\s*<attribute name="disallowedNextLinks".*?</attribute>\n?', re.S)


def apply_variants(base_net):
    """Write one network per E1 road variant by rewriting link attributes.

    A MATSim link carries its OSM way id as the nested attribute `osm:way:id`,
    and one OSM way becomes several links, so a patch row fans out over every
    link derived from that way. Lane count moves `permlanes`; capacity moves with
    it at the same per-lane rate; kerbside use is not a MATSim link field so it is
    carried as a link attribute for the SUMO corridor and the parking layer.

    The full-capacity counterfactual additionally drops `disallowedNextLinks`
    from corridor links - E1 specifies 'no banned turns' for the network without
    the tram, and those restrictions are exactly what pt2matsim wrote there.
    """
    variants = list(csv.DictReader(open(E1_ROAD_VARIANTS, encoding='utf-8')))
    patches = list(csv.DictReader(open(PATCHES, encoding='utf-8')))
    by_variant = collections.defaultdict(dict)
    for p in patches:
        by_variant[p['road_variant_ref']][p['edge_id'][1:]] = p   # strip the 'w'

    with gzip.open(base_net, 'rt', encoding='utf-8') as f:
        xml = f.read()

    report = {}
    for v in variants:
        ref = v['road_variant_ref']
        out_dir = os.path.join(OUT, 'variants', ref)
        os.makedirs(out_dir, exist_ok=True)
        dest = os.path.join(out_dir, 'network.xml.gz')
        pat = by_variant.get(ref, {})
        drop_turns = v['banned_turn_movements'] == '0'
        applied = collections.Counter()

        if not pat:
            # The as-built variant departs from OSM nowhere, so it *is* the base
            # network. Writing it as a copy keeps the per-variant path contract.
            body = xml
        else:
            def patch_link(m):
                s = m.group(0)
                wid = WAY_ID_RE.search(s)
                p = pat.get(wid.group(1)) if wid else None
                if not p:
                    return s
                head_end = s.index('>')
                head, tail = s[:head_end], s[head_end:]
                a = dict(ATTR_RE.findall(head))
                changed = p['fields_changed'].split(';')

                if 'num_lanes_per_dir' in changed and p['field_num_lanes_per_dir_to']:
                    new_lanes = float(p['field_num_lanes_per_dir_to'])
                    old_lanes = float(a.get('permlanes') or 1)
                    cap = float(a.get('capacity') or 0)
                    per_lane = (cap / old_lanes) if old_lanes else float(
                        p['capacity_veh_hr_lane'])
                    head = re.sub(r'permlanes="[^"]*"',
                                  'permlanes="%.1f"' % new_lanes, head)
                    head = re.sub(r'capacity="[^"]*"',
                                  'capacity="%.1f"' % (per_lane * new_lanes), head)
                    applied['num_lanes_per_dir'] += 1

                if 'kerbside_use' in changed and p['field_kerbside_use_to']:
                    # the SAME attribute name the run network carries
                    # (`osm:way:kerbside`, build_matsim_run_inputs); it was
                    # `kerbsideUse` here and `osm:way:kerbside` there, and no
                    # Java class reads either - so it is counted as an unread
                    # attribute, never as a link whose physics changed
                    # (eighth project report, 11 September 2026)
                    tail = tail.replace(
                        '</attributes>',
                        '\t<attribute name="osm:way:kerbside" class="java.lang.String">'
                        '%s</attribute>\n\t\t\t</attributes>'
                        % p['field_kerbside_use_to'], 1)
                    applied['kerbside_use_attribute_unread_by_any_run'] += 1

                if drop_turns and 'disallowedNextLinks' in tail:
                    tail = DISALLOWED_RE.sub('', tail)
                    applied['banned_turns_removed'] += 1

                return head + tail
            body = LINK_BLOCK_RE.sub(patch_link, xml)

        with open(dest, 'wb') as fh:
            g = gzip.GzipFile(fileobj=fh, mode='wb', mtime=0)
            g.write(body.encode('utf-8'))
            g.close()
        report[ref] = dict(patch_rows=len(pat), links_touched=dict(applied),
                           identical_to_base=not pat,
                           banned_turns_dropped=drop_turns,
                           bytes=os.path.getsize(dest))
        log('   %-42s %5d patch rows -> links %s'
            % (ref, len(pat), dict(applied) or 'none (= base)'))
    return report


# ---------------------------------------------------------------------------
# stage 4: GTFS -> unmapped schedule -> mapped schedule
# ---------------------------------------------------------------------------
def write_mapper_config(path, network, schedule, out_net, out_sched, out_street,
                        threads, cfg=None):
    """Emit the pt2matsim PublicTransitMapping config from the registry."""
    cfg = cfg if cfg is not None else _registry.load()
    runtime = {
        'PublicTransitMapping.inputNetworkFile': (fwd(network), 'path', 'base network'),
        'PublicTransitMapping.inputScheduleFile': (fwd(schedule), 'path',
                                                   'unmapped schedule'),
        'PublicTransitMapping.outputNetworkFile': (fwd(out_net), 'path', 'mapped network'),
        'PublicTransitMapping.outputScheduleFile': (fwd(out_sched), 'path',
                                                    'mapped schedule'),
        'PublicTransitMapping.outputStreetNetworkFile': (fwd(out_street), 'path',
                                                         'street-only network'),
        'PublicTransitMapping.numOfThreads': (threads, 'derived',
                                              'RUN.machine.threads for this build'),
    }
    leaks = _param_config.closure('pt2matsim_mapper', cfg, runtime)
    if leaks:
        raise SystemExit('the schedule mapper config carries %d parameter(s) from '
                         'neither a field nor a declared role: %s' % (len(leaks), leaks))
    return _param_config.write(path, 'pt2matsim_mapper', cfg, runtime)


def unpack_feed(name, zip_path):
    """pt2matsim reads a GTFS folder, not a zip."""
    d = os.path.join(WORK, 'gtfs', name)
    if os.path.isdir(d) and os.path.exists(os.path.join(d, 'stop_times.txt')):
        return d
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        for n in sorted(z.namelist()):
            if n.endswith('/'):
                continue
            with z.open(n) as src, open(os.path.join(d, os.path.basename(n)), 'wb') as dst:
                shutil.copyfileobj(src, dst)
    return d


def build_schedule(name, zip_path, base_net, threads):
    out_dir = os.path.join(OUT, 'schedules', name)
    os.makedirs(out_dir, exist_ok=True)
    unmapped = os.path.join(WORK, 'unmapped', '%s_schedule.xml.gz' % name)
    vehicles = os.path.join(out_dir, 'transitVehicles.xml.gz')
    os.makedirs(os.path.dirname(unmapped), exist_ok=True)

    folder = unpack_feed(name, zip_path)
    t0 = time.time()
    if not os.path.exists(unmapped):
        java(['org.matsim.pt2matsim.run.Gtfs2TransitSchedule',
              folder, GTFS_DAY_PARAM, CRS, unmapped, vehicles], 'gtfs_%s' % name)
    t_gtfs = time.time() - t0

    mapped_sched = os.path.join(out_dir, 'transitSchedule.xml.gz')
    mapped_net = os.path.join(out_dir, 'network.xml.gz')
    street_net = os.path.join(WORK, 'street', '%s_street.xml.gz' % name)
    os.makedirs(os.path.dirname(street_net), exist_ok=True)
    cfg = write_mapper_config(os.path.join(WORK, 'ptmap_%s.xml' % name),
                             base_net, unmapped, mapped_net, mapped_sched,
                             street_net, threads)
    t1 = time.time()
    java(['org.matsim.pt2matsim.run.PublicTransitMapper', cfg], 'ptmap_%s' % name)
    t_map = time.time() - t1

    stats = schedule_stats(mapped_sched)
    stats.update(feed=_city.rel(zip_path), gtfs_seconds=round(t_gtfs, 1),
                 mapping_seconds=round(t_map, 1),
                 network_bytes=os.path.getsize(mapped_net),
                 schedule_bytes=os.path.getsize(mapped_sched))
    log('   %-30s %5.0f s map | %d stops, %d routes, %d unmapped-link stops'
        % (name, t_map, stats['stop_facilities'], stats['transit_routes'],
           stats['stops_without_link']))
    return stats


STOP_LINK_RE = re.compile(r'<stopFacility id="([^"]+)"[^>]*?linkRefId="([^"]+)"')
ROUTE_RE = re.compile(r'<transitRoute id="([^"]+)".*?</transitRoute>', re.S)


def schedule_stats(path):
    """Counts straight off the mapped schedule: the mapping's own report.

    Also records two fingerprints, because PublicTransitMapper is not
    reproducible run to run (DECISIONS.md 3.5):

      stop_link_fingerprint   sha256 over the sorted stop -> link assignment.
                              Measured stable across repeated builds, so
                              tests/check_package.py asserts it exactly.
      route_link_fingerprint  sha256 over the sorted route link sequences. This
                              one moves between builds; it identifies the build
                              of record rather than constraining a rebuild.
    """
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        xml = f.read()
    facilities = re.findall(r'<stopFacility\b[^>]*>', xml)
    linked = sum(1 for s in facilities if 'linkRefId="' in s)
    routes = xml.count('<transitRoute ')
    lines = xml.count('<transitLine ')
    departures = xml.count('<departure ')
    route_links = re.findall(r'<link\s+refId="([^"]+)"', xml)
    artificial = sum(1 for l in route_links if l.startswith('pt_'))
    modes = collections.Counter(re.findall(r'<transportMode>([^<]+)</transportMode>', xml))

    stop_link = sorted('%s\t%s' % (a, b) for a, b in STOP_LINK_RE.findall(xml))
    route_seq = sorted('%s\t%s' % (m.group(1),
                                   ','.join(re.findall(r'<link refId="([^"]+)"', m.group(0))))
                       for m in ROUTE_RE.finditer(xml))
    return dict(stop_facilities=len(facilities),
                stops_with_link=linked,
                stops_without_link=len(facilities) - linked,
                transit_lines=lines, transit_routes=routes, departures=departures,
                route_link_refs=len(route_links),
                artificial_link_refs=artificial,
                artificial_share_pct=round(100.0 * artificial / max(len(route_links), 1), 2),
                stop_link_fingerprint=hashlib.sha256(
                    '\n'.join(stop_link).encode('utf-8')).hexdigest(),
                route_link_fingerprint=hashlib.sha256(
                    '\n'.join(route_seq).encode('utf-8')).hexdigest(),
                modes=dict(modes))


def compare_builds(name, base_net, threads):
    """Re-map one feed and report how far the second build drifts from the first.

    The drift is a property of pt2matsim, not of this pipeline, so it is measured
    and published rather than asserted away.
    """
    out_dir = os.path.join(OUT, 'schedules', name)
    tmp = os.path.join(WORK, 'determinism')
    os.makedirs(tmp, exist_ok=True)
    keep = {n: os.path.join(tmp, '%s_first_%s' % (name, n))
            for n in ('transitSchedule.xml.gz', 'network.xml.gz')}
    for n, k in keep.items():
        shutil.copyfile(os.path.join(out_dir, n), k)
    build_schedule(name, FEEDS[name], base_net, threads)

    def load(p):
        with gzip.open(p, 'rt', encoding='utf-8') as f:
            return f.read()
    A, B = load(keep['transitSchedule.xml.gz']), \
        load(os.path.join(out_dir, 'transitSchedule.xml.gz'))
    fa, fb = dict(STOP_LINK_RE.findall(A)), dict(STOP_LINK_RE.findall(B))
    shared = set(fa) & set(fb)
    same_link = sum(1 for k in shared if fa[k] == fb[k])

    def routes(x):
        return {m.group(1): tuple(re.findall(r'<link refId="([^"]+)"', m.group(0)))
                for m in ROUTE_RE.finditer(x)}
    ra, rb = routes(A), routes(B)
    rshared = set(ra) & set(rb)
    same_route = sum(1 for k in rshared if ra[k] == rb[k])
    # restore the build of record: the check must not become the artefact
    for n, k in keep.items():
        shutil.copyfile(k, os.path.join(out_dir, n))
    return dict(
        feed=name,
        stop_facilities=[len(fa), len(fb)],
        stop_link_assignment_identical_pct=round(100.0 * same_link / max(len(shared), 1), 3),
        transit_routes=[len(ra), len(rb)],
        route_link_sequence_identical_pct=round(100.0 * same_route / max(len(rshared), 1), 3))


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage', choices=['all', 'network', 'variants', 'schedules'],
                    default='all')
    ap.add_argument('--only', default='', help='comma-separated feed names')
    ap.add_argument('--workers', type=int, default=2,
                    help='feeds mapped concurrently (each uses --threads threads)')
    ap.add_argument('--threads', type=int, default=2, help='PublicTransitMapper threads')
    ap.add_argument('--determinism-check', default='',
                    help='comma-separated feeds to re-map and compare (DECISIONS 3.5)')
    a = ap.parse_args()

    tc.require()
    os.makedirs(OUT, exist_ok=True)
    report_path = os.path.join(OUT, '_matsim_build_report.json')
    report = json.load(open(report_path, encoding='utf-8')) \
        if os.path.exists(report_path) else {}

    base_net = os.path.join(OUT, 'base', 'network.xml.gz')
    if a.stage in ('all', 'network') or not os.path.exists(base_net):
        base_net = build_base_network()
        report['base_network'] = network_stats(base_net)
        report['base_network']['path_access_overrides'] = build_base_network.access_report

    if a.stage in ('all', 'variants'):
        log('applying E1 road variants')
        report['road_variants'] = apply_variants(base_net)

    if a.stage in ('all', 'schedules'):
        want = [k for k in FEEDS if not a.only or k in a.only.split(',')]
        log('mapping %d feed(s) with %d worker(s) x %d thread(s)'
            % (len(want), a.workers, a.threads))
        sched = report.get('schedules', {})
        with futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
            fut = {ex.submit(build_schedule, k, FEEDS[k], base_net, a.threads): k
                   for k in want}
            for f in futures.as_completed(fut):
                k = fut[f]
                sched[k] = f.result()
        report['schedules'] = {k: sched[k] for k in FEEDS if k in sched}

    if a.determinism_check:
        log('determinism check: re-mapping %s' % a.determinism_check)
        drift = [compare_builds(k, base_net, a.threads)
                 for k in a.determinism_check.split(',') if k in FEEDS]
        report['determinism_check'] = drift
        for d in drift:
            log('   %-30s stop->link %.3f%% identical, route link seq %.3f%% identical'
                % (d['feed'], d['stop_link_assignment_identical_pct'],
                   d['route_link_sequence_identical_pct']))

    report['toolchain'] = {c['component']: c['version']
                           for c in (tc.load_manifest() or {}).get('components', [])}
    report['crs'] = CRS
    report['gtfs_day_param'] = GTFS_DAY_PARAM
    with open(report_path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(report, f, indent=2, sort_keys=True)
        f.write('\n')
    log('report -> %s' % report_path)


def network_stats(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        xml = f.read()
    nodes = xml.count('<node ')
    links = re.findall(r'<link\b[^>]*>', xml)
    modes = collections.Counter()
    length = 0.0
    for s in links:
        m = re.search(r'modes="([^"]*)"', s)
        if m:
            for mode in m.group(1).split(','):
                modes[mode.strip()] += 1
        m = re.search(r'length="([^"]*)"', s)
        if m:
            length += float(m.group(1))
    return dict(nodes=nodes, links=len(links), km=round(length / 1000, 1),
                links_by_mode=dict(modes), bytes=os.path.getsize(path))


if __name__ == '__main__':
    # this builder's own wall time, for cities/<city>/data/_build_timing.json (build_timing.py)
    import sys as _sys_t, os as _os_t  # noqa: E401
    import build_timing as _timing  # noqa: E402
    _timing.start(__file__)
    main()
