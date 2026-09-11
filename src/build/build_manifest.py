#!/usr/bin/env python
"""Build the data package manifest: every file, its provenance and its lineage.

Deliverable 2 of the proposal is an open data package with every derived input,
its provenance, licence status and processing lineage. This walks the tree,
hashes everything, counts rows, and merges the per-stage provenance records.
"""
import ast
import io
import os
import re
import csv
import glob
import json
import fnmatch
import hashlib
import datetime
import zipfile
import sys

# The manifest describes ONE CITY. Its paths stay city-relative - `data/...`,
# not `cities/newcastle/data/...` - so the manifest does not repeat the city's
# own name on all 376 of its rows, and a second city's manifest is comparable
# to this one row for row.
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', 'src'))
import city as _city  # noqa: E402

ROOT = _city.CITY_DIR
SCAN = ['data/raw', 'data/processed', 'schedules', 'demand', 'params',
        'scenarios', 'networks/osm', 'networks/matsim']
SKIP_EXT = {'.pyc'}
# Per-stage provenance records: whatever the city's own adapters landed, found
# by convention rather than by a hardcoded list of one city's file names -
# RECURSIVELY under data/raw (#117: five records in subdirectories were never
# read, and 472 of 511 rows carried no licence).
PROVENANCE_FILES = (sorted(glob.glob(os.path.join(ROOT, 'data', 'raw', '**',
                                                  'provenance*.json'),
                                     recursive=True))
                    + sorted(glob.glob(os.path.join(ROOT, 'schedules', 'raw',
                                                    'provenance*.json'))))

# The city's declared sources (city.json `sources`): the licence a raw file
# carries is the licence its DECLARED source carries, resolved by the longest
# `provides` prefix. The record beside the download describes the download;
# the descriptor is canonical for the licence, so one source is never spelt
# three ways across its files.
SOURCES = _city.descriptor().get('sources') or []
# The city's declared licences for DERIVED layers (city.json
# `derived_licences`: city-relative glob -> licence), and the licence of
# everything else it built (`package_licence`). A share-alike source (OSM's
# ODbL) reaches into every layer built from it, and which layers those are is
# a fact about the city's build the city declares - the framework names no
# artefact of any city.
DERIVED_LICENCES = _city.descriptor().get('derived_licences') or {}
PACKAGE_LICENCE = _city.descriptor().get('package_licence') or ''
# The share-alike licence labels THIS CITY declares, taken from the sources it
# marked `share_alike`. The framework names no licence of its own: a city that
# harvests a different share-alike source declares that source's label and the
# lineage check follows it.
SHARE_ALIKE_LICENCES = tuple(sorted(
    {s['licence'] for s in SOURCES if s.get('share_alike') and s.get('licence')}))
# What a provenance record or an acquisition log IS: this package's own record
# of itself. It is not a source that was retrieved from anywhere, and it never
# carries a retrieval date (9.151, #149).
PACKAGE_RECORD = '%s - the provenance record the package keeps of itself' % (
    _city.descriptor().get('name') or _city.CITY)

# Which script produced what, for the lineage graph. THE FRAMEWORK HALF ONLY:
# the generic pipeline scripts under src/build/. Everything a particular city
# acquires or builds for itself is declared by that city - its `adapters` block
# (acquisition) and its `lineage` block (city-owned builders) in city.json -
# and merged in below. No acquisition script and no city build script is named
# here (issue #62 B1).
LINEAGE = {
    'data/processed/network': 'src/build/build_network_layers.py + src/build/attach_gradient.py',
    'data/processed/schedule_extras': 'src/build/build_gtfs_extras.py',
    'data/processed/basemap.json': 'src/analyse/build_basemap.py',
    'data/processed/network/_speed_zone_report.json': 'src/build/attach_speed_zones.py',
    'data/processed/validation/count_station_links.csv': 'src/analyse/map_count_stations.py',
    'demand/population': 'src/build/build_population.py',
    'demand/plans': 'src/build/build_activity_chains.py',
    'demand/plans/matsim': 'src/build/build_matsim_plans.py',
    'params': 'src/build/build_params.py',
    # the measured and calibrated parameter files have their own producers
    # (tests/check_package.py asserts every producer names its artefact)
    'params/C2_network_factors.json': 'src/build/measure_network_factors.py',
    'params/C2_osm_defaults.json': 'src/build/measure_osm_defaults.py',
    'params/C4_mode_constraints.json': 'src/calibrate/measure_mode_constraints.py',
    'params/C5_calibration.json': 'src/calibrate/calibrate.py',
    'params/C6_departure_profile_check.json': 'src/calibrate/measure_departure_constraint.py',
    'scenarios/matsim': 'src/build/build_matsim_run_inputs.py',
    'networks/matsim': 'src/build/build_matsim_network.py (pt2matsim 26.6)',
}


def _city_script(token):
    """A lineage token to its repo-relative form: city-relative scripts gain
    the cities/<city>/ prefix, framework scripts (src/...) pass through."""
    token = token.strip()
    return token if token.startswith('src/') else 'cities/%s/%s' % (_city.CITY, token)


# The city's own `lineage` block: city-relative artefact prefix -> the
# script(s) that build it (`build/...` for that city's builders; a ` + `-joined
# entry names each contributing script, framework ones included).
for _prefix, _entry in (_city.descriptor().get('lineage') or {}).items():
    LINEAGE[_prefix] = ' + '.join(_city_script(t) for t in _entry.split(' + '))

# Every adapter's own `produces` declaration overlays the map above, so an
# adapter that produces a SPECIFIC FILE inside a directory another adapter
# owns (extract_freight_profile.py writing two CSVs into the observed layer)
# is attributed to the script that actually wrote it - longest prefix wins in
# lineage_for().
for _spec in _city.descriptor().get('adapters', {}).values():
    if _spec.get('script'):
        for _prefix in _spec.get('produces', []):
            LINEAGE[_prefix] = _city_script(_spec['script'])

# P2 build intermediates: large, regenerable, and not part of the package.
SKIP_DIRS = ('networks/matsim/_work',)


def sha256(p, limit=None):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        while True:
            b = f.read(1 << 20)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def count_rows(p):
    if p.endswith('.csv'):
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                return max(0, sum(1 for _ in f) - 1)
        except Exception:
            return None
    if p.endswith('.jsonl'):
        try:
            with open(p, encoding='utf-8', errors='replace') as f:
                return sum(1 for _ in f)
        except Exception:
            return None
    if p.endswith('.zip'):
        try:
            z = zipfile.ZipFile(p)
            return len(z.namelist())
        except Exception:
            return None
    return None


def lineage_for(rel):
    best = ''
    for k, v in LINEAGE.items():
        if rel.replace('\\', '/').startswith(k) and len(k) > len(best):
            best = k
    return LINEAGE.get(best, '')


def source_for(rel):
    """The declared source whose `provides` prefix covers the path, or None."""
    best, best_len = None, -1
    for s in SOURCES:
        for prefix in s.get('provides') or []:
            p = prefix.strip('/')
            if (rel == p or rel.startswith(p + '/')) and len(p) > best_len:
                best, best_len = s, len(p)
    return best


def _resolve_record_path(key, here, base):
    """A record's file key to a city-relative path.

    Records name their files three ways: relative to a `base` directory the
    record declares, relative to the directory the record sits in (the dict
    form's `files` map), or relative to the layer root - `data/raw` or
    `schedules/raw` - as the list-form writers do. The candidate that exists
    on disk wins; the first is kept if none does, so an absent file still
    joins its record and the manifest shows what it was.
    """
    key = key.replace('\\', '/').lstrip('./')
    root = 'schedules/raw' if here.startswith('schedules') else 'data/raw'
    cands = []
    if base:
        cands.append('%s/%s' % (base.strip('/'), key))
    cands.append(('%s/%s' % (here, key)) if here not in ('', '.') else key)
    cands.append('%s/%s' % (root, key))
    for c in cands:
        if os.path.exists(os.path.join(ROOT, c)):
            return c
    return cands[0]


def provenance_records():
    """city-relative path -> provenance record, from every record file.

    Two record forms are landed by the adapters: a LIST of per-file dicts
    (`path`, `url`, `licence`, `retrieved`, ...; the GTFS list names `era` and
    `feed` instead of a path), and a DICT with a header (`source`, `licence`,
    `retrieved`, `purpose`) and a `files` map whose entries inherit the header
    and may override it. Both are read; a record that cannot be parsed is
    reported and skipped, never silently dropped (#117).
    """
    prov = {}
    for pf in PROVENANCE_FILES:
        if not os.path.exists(pf):
            continue
        here = os.path.relpath(os.path.dirname(pf), ROOT).replace('\\', '/')
        try:
            doc = json.load(open(pf, encoding='utf-8'))
        except Exception as e:                               # noqa: BLE001
            print('warn: %s (%s)' % (pf, e))
            continue
        if isinstance(doc, list):
            for r in doc:
                if not isinstance(r, dict):
                    continue
                key = r.get('path')
                if not key and r.get('feed'):
                    key = '%s/%s.zip' % (r.get('era', ''), r['feed'])
                if not key:
                    continue
                prov[_resolve_record_path(key, here, r.get('base'))] = r
        elif isinstance(doc, dict):
            header = {k: v for k, v in doc.items() if k != 'files'}
            entries = doc.get('files') or {}
            items = (entries.items() if isinstance(entries, dict)
                     else [(e.get('path'), e) for e in entries if isinstance(e, dict)])
            for name, e in items:
                if not name:
                    continue
                rec = dict(header)
                rec.update(e if isinstance(e, dict) else {})
                if rec.get('harvested'):
                    rec['retrieved'] = rec['harvested']   # per file, not the header's max
                rec.setdefault('description', rec.get('document') or rec.get('note')
                               or header.get('purpose') or header.get('source', ''))
                prov[_resolve_record_path(name, here, doc.get('base'))] = rec
        else:
            print('warn: %s is neither a list nor a dict of records' % pf)
    return prov


# 9.151 (#149): where a DERIVED file's data came from. 420 of the 512 rows
# carried no `source` and no `retrieved` at all, because both columns were
# filled only from a provenance record and only a raw download has one. A
# derived file's source is not a new fact to be typed in - it is the raw
# layers its producing script reads, transitively - so it is RESOLVED here
# from the lineage the manifest already knows, and never declared by hand. A
# hand-written attribution is exactly the kind of number this project cannot
# absorb: it would look observed and be a guess.
_INPUT_RE = re.compile(
    r"""['"]((?:data/raw|data/processed|networks/osm|networks/matsim"""
    r"""|schedules|demand|params|scenarios)[A-Za-z0-9_./\-]*)""")
_RAW_PREFIXES = ('data/raw', 'networks/osm', 'schedules/raw')
# The package's own layer roots - the same set `_INPUT_RE` alternates over, as
# a tuple, so a path built by a `*.path(...)` call is admitted on the same
# terms as one written as a literal.
_LAYER_PREFIXES = ('data/raw', 'data/processed', 'networks/osm',
                   'networks/matsim', 'schedules', 'demand', 'params',
                   'scenarios')
_script_inputs_cache = {}


# #159: OUTPUT-LEVEL LINEAGE. The regex above finds every path a
# producing script mentions, and until now every one of them was credited to
# every file that script writes. A script with one output got a correct
# answer; a script with many got an ancestry as wide as its whole source, and
# 129 rows named an OpenStreetMap ancestor they may never have carried. A
# provenance wider than the truth is still a wrong provenance, and on the
# licence side it decides whether a row is ODbL share-alike or CC-BY.
#
# So a producing script may DECLARE which of its inputs feed which of its
# outputs, in a module-level `OUTPUT_INPUTS` mapping:
#
#     OUTPUT_INPUTS = {
#         'demand/population/B1_households.csv': [
#             'data/processed/landuse/D1_zone_attractions_SA1.csv#SA1_CODE21,population',
#             'data/processed/census'],
#     }
#
# Keys are city-relative output paths (or fnmatch globs); values are the
# city-relative INPUT paths that output descends from. A value may carry a
# `#col,col` selector, which resolves through the input producer's OWN
# declaration for exactly that column subset - the granularity at which a
# mixed-provenance table (ABS columns beside OSM POI counts) stops being one
# undivided ancestor.
#
# WHY A DECLARATION IN THE SCRIPT, and not the two alternatives weighed:
#   - in the script's `_*_report.json`: a report exists only after that script
#     has run, so a fresh clone could determine no row's licence at all; and a
#     gitignored, regenerated file is not somewhere a licence-bearing claim
#     can be reviewed in a diff.
#   - derived from the columns an output carries: cannot decide for the
#     `.xml.gz` and `.gpkg` outputs that are most of the package, and cannot
#     tell an OSM-placed coordinate from an ABS zone centroid.
#   - a table in this file: it would name one city's artefacts inside the
#     framework, which the hard constraint forbids outright.
# The declaration sits beside the code that writes the output, is read
# STATICALLY (never imported, never executed), and moves in the same diff as
# the write it describes.
#
# WHERE NOTHING IS DECLARED the script-level union is still used, but it is
# recorded as such: `lineage_scope` says `script` and the share-alike verdict
# says `undetermined` rather than guessing in either direction. The union is a
# sound OVER-approximation, so one conclusion survives without a declaration:
# a union holding no share-alike source proves the true ancestry holds none.
_OUTPUT_INPUTS_NAME = 'OUTPUT_INPUTS'
_declared_cache = {}
_sole_cache = {}


def _script_path(token):
    """A lineage token to a path on disk, framework or city-owned."""
    token = token.split(' (')[0].strip()
    if os.path.exists(token):
        return token
    cand = os.path.join('cities', _city.CITY, token)
    return cand if os.path.exists(cand) else None


def _city_path_calls(txt):
    """City-relative paths built by a MULTI-ARGUMENT `*.path(...)` call.

    `_city.path('networks', 'matsim', 'schedules')` is invisible to a regex
    over string literals, and the miss is not academic: the charging-dwell
    builder names its only OSM-descended input that way, so the union that
    the share-alike verdict rests on was missing it entirely. The whole
    over-approximation argument for a `no` verdict depends on the extractor
    not missing an input, so the two forms this repository actually uses are
    both read.
    """
    out = set()
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        if not (isinstance(fn, ast.Attribute) and fn.attr == 'path'):
            continue
        parts = []
        for a in node.args:
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                parts.append(a.value.replace(os.sep, '/').strip('/'))
            else:
                break
        if len(parts) > 1:
            out.add('/'.join(parts))
    return out


def _script_inputs(token):
    """The city-relative paths a producing script names in its own source."""
    if token in _script_inputs_cache:
        return _script_inputs_cache[token]
    _script_inputs_cache[token] = out = set()
    p = _script_path(token)
    if p:
        try:
            txt = io.open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            txt = ''
        for m in _INPUT_RE.findall(txt):
            out.add(m.replace(os.sep, '/').rstrip('/'))
        out |= _city_path_calls(txt)
    return {m for m in out if m.startswith(_LAYER_PREFIXES)}


def _script_declarations(token):
    """A producing script's `OUTPUT_INPUTS` mapping, read WITHOUT running it.

    The module is parsed, the module-level assignment is located and its value
    is `ast.literal_eval`ed. A script that does not declare returns {}. A
    declaration that is not a literal mapping of str -> sequence of str is
    reported and ignored, never half-read.
    """
    if token in _declared_cache:
        return _declared_cache[token]
    _declared_cache[token] = out = {}
    p = _script_path(token)
    if not p:
        return out
    try:
        tree = ast.parse(io.open(p, encoding='utf-8', errors='replace').read())
    except (OSError, SyntaxError) as e:                      # noqa: BLE001
        print('warn: %s (%s)' % (p, e))
        return out
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(t, ast.Name) and t.id == _OUTPUT_INPUTS_NAME
                   for t in node.targets):
            continue
        try:
            value = ast.literal_eval(node.value)
        except ValueError:
            print('warn: %s declares a non-literal %s' % (p, _OUTPUT_INPUTS_NAME))
            continue
        if not isinstance(value, dict):
            print('warn: %s declares a non-mapping %s' % (p, _OUTPUT_INPUTS_NAME))
            continue
        for k, v in value.items():
            if (isinstance(k, str) and isinstance(v, (list, tuple))
                    and all(isinstance(x, str) for x in v)):
                out[k.replace(os.sep, '/')] = tuple(v)
    return out


def _declared_inputs(rel, entry, selector=''):
    """(inputs, True) where a producing script declares this output's inputs.

    `selector` is the `#col,col` suffix a consumer asked for; the declaration
    must carry that exact key or the request is undeclared - a column subset
    nobody wrote down is not evidence about which ancestor reached it. Exact
    keys win over globs, and a longer glob over a shorter one.
    """
    want = rel + selector
    best, best_len, found = None, -1, False
    for token in (entry or '').split(' + '):
        decl = _script_declarations(token)
        if not decl:
            continue
        if want in decl:
            return set(decl[want]), True
        if selector:
            continue
        for pat, ins in decl.items():
            if '#' in pat:
                continue
            if fnmatch.fnmatch(rel, pat) and len(pat) > best_len:
                best, best_len, found = set(ins), len(pat), True
    if found:
        return (best or set()), True
    # A consumer that names a DIRECTORY (`data/processed/network`) rather than
    # a file resolves to the union of every declared output under it, which is
    # the widest thing reading that directory could have pulled - and is still
    # output-level, because each of those outputs was declared.
    union, any_under = set(), False
    for token in (entry or '').split(' + '):
        for pat, ins in _script_declarations(token).items():
            if '#' in pat:
                continue
            if pat.startswith(rel.rstrip('/') + '/'):
                union |= set(ins)
                any_under = True
    return (union, True) if any_under else (set(), False)


def index_outputs(paths):
    """Record which producing script writes exactly ONE manifest row.

    Such a script cannot mis-attribute: the union of everything its source
    names IS that one output's ancestry. Called by main() before any row is
    resolved, so the scope of those rows is `output` without a declaration.
    """
    counts = {}
    for rel in paths:
        entry = lineage_for(rel)
        if entry:
            counts.setdefault(entry, []).append(rel)
    _sole_cache.clear()
    for entry, rels in counts.items():
        if len(rels) == 1:
            _sole_cache[entry] = rels[0]


def explicit_share_alike(rel):
    """True where the city EXPLICITLY declares this derived path share-alike.

    `derived_licences` is the city's own reviewed statement that a built layer
    carries the share-alike obligation - the scenario schedules were put there
    on measured evidence (357,893 OSM route link references). Reading such a
    file is therefore proof enough that the obligation reaches the reader,
    without re-deriving the whole chain behind it. The PACKAGE default is not
    such a statement, so only a matching glob counts.
    """
    best = ''
    for pat in DERIVED_LICENCES:
        if fnmatch.fnmatch(rel, pat) and len(pat) > len(best):
            best = pat
    return bool(best) and is_share_alike(DERIVED_LICENCES.get(best) or '')


def ancestry(rel, selector='', _seen=None):
    """(proven, possible, scope) for one manifest path.

    `possible` is every raw layer (or explicitly share-alike derived layer)
    the file MIGHT descend from; `proven` is the subset reached without ever
    falling back to a script-level union. `proven` is always a subset of
    `possible`, and the gap between them is exactly what #159 was hiding.

    scope is `raw` (the file IS a raw download), `output` (every step of the
    resolution was output-level - the producing script declared this output's
    inputs, or it writes this one output), `script` (some step fell back to
    the script-level union), or `none` (no producing script is known).
    """
    _seen = set() if _seen is None else _seen
    if rel in _seen:
        return set(), set(), 'output'
    _seen.add(rel)
    if rel.startswith(_RAW_PREFIXES):
        return {rel}, {rel}, 'raw'
    entry = lineage_for(rel)
    if not entry:
        return set(), set(), 'none'
    deps, declared = _declared_inputs(rel, entry, selector)
    if declared:
        scope = 'output'
    elif selector:
        # the column subset was asked for and nobody declared it: fall back to
        # the whole file, where the imprecision is then recorded
        return ancestry(rel, '', _seen)
    else:
        deps = set()
        for token in entry.split(' + '):
            deps |= _script_inputs(token)
        scope = 'output' if _sole_cache.get(entry) == rel else 'script'
    proven, possible = set(), set()
    for dep in sorted(deps):
        dep, _, sel = dep.partition('#')
        dep = dep.replace(os.sep, '/').rstrip('/')
        if dep == rel:
            continue
        # In the UNDECLARED fallback, skip what this script produces: the
        # regex cannot tell a script's outputs from its inputs, and a string
        # prefix test would also drop `params` for `params/C1.json`. A
        # DECLARATION is the author saying this input feeds this output, so
        # it stands even for a sibling written by the same producer pair -
        # the zone table really is built from the POI table beside it.
        if not declared and lineage_for(dep) == entry:
            continue
        sel_arg = ('#' + sel) if sel else ''
        sub_p, sub_a, _sub_scope = ancestry(dep, sel_arg, _seen)
        # A city's blanket `derived_licences` glob is a statement about a
        # WHOLE file. Where the reader narrowed it to columns and the input's
        # producer declared that subset, the blanket claim is not evidence
        # about what was read - which is the entire point of the selector.
        narrowed = bool(sel_arg) and _declared_inputs(
            dep, lineage_for(dep), sel_arg)[1]
        if explicit_share_alike(dep) and not narrowed:
            sub_p = sub_p | {dep}
            sub_a = sub_a | {dep}
        possible |= sub_a
        if scope == 'output':
            proven |= sub_p
    return proven, possible, scope


def is_share_alike(licence):
    """True where a licence label names a share-alike licence this city
    declares. The labels come from the city's own `sources`, never from a
    list of licence names typed into the framework."""
    return any(lic and lic in (licence or '') for lic in SHARE_ALIKE_LICENCES)


def share_alike_sources(anc):
    """The declared sources with `share_alike` true that cover an ancestor."""
    out = []
    for src in SOURCES:
        if not src.get('share_alike'):
            continue
        for prefix in src.get('provides') or []:
            pfx = prefix.strip('/')
            if any(a == pfx or a.startswith(pfx + '/') for a in anc):
                out.append(src)
                break
    return out


def share_alike_verdict(proven, possible, scope):
    """`yes`, `no` or `undetermined` for one row.

    `yes` needs a PROVEN share-alike ancestor: claiming one from a
    script-level union is exactly the error #159 is about, and it is the
    direction that over-restricts a row.

    `no` may rest on the POSSIBLE set, because that set OVER-approximates in
    the one direction #159 names - a script's whole input list credited to
    each of its outputs - so a union holding no share-alike source proves the
    true ancestry holds none. The residual risk is the opposite one: static
    extraction can MISS an input that is neither a path literal nor a
    `*.path(...)` call. That is not left to trust either. The row's licence is
    an independent, human-reviewed claim, and `check_lineage_licence()` fails
    on any disagreement in EITHER direction - which is how the charging-dwell
    builder's dynamically named input was found in the first place.

    Between the two - a share-alike ancestor that is possible but not proven -
    the row says `undetermined`. It is not a licence, and it is not a guess.
    """
    if scope == 'none':
        return 'undetermined'
    if holds_share_alike(proven):
        return 'yes'
    if holds_share_alike(possible):
        return 'undetermined'
    return 'no'


def holds_share_alike(paths):
    """True where a path set carries the share-alike obligation - either
    through a declared share-alike SOURCE, or through a derived layer the
    city itself declared share-alike."""
    return bool(share_alike_sources(paths)) or any(explicit_share_alike(p)
                                                   for p in paths)


def derived_provenance(rel, prov, anc):
    """(source, source_url, retrieved) for a DERIVED file.

    source/url: the DECLARED sources covering its raw ancestors, in the
    descriptor's own order so one layer reads the same way in every row.
    retrieved: the LATEST retrieval date among those ancestor raw files - the
    vintage of the newest input the layer could embody, an upper bound on how
    old its data is, never a build time.
    """
    if not anc:
        return '', '', ''
    names, urls = [], []
    for src in SOURCES:
        for prefix in src.get('provides') or []:
            pfx = prefix.strip('/')
            if any(a == pfx or a.startswith(pfx + '/') for a in anc):
                if src.get('name') and src['name'] not in names:
                    names.append(src['name'])
                    if src.get('url'):
                        urls.append(src['url'])
                break
    dates = [r.get('retrieved') for path, r in prov.items()
             if r.get('retrieved')
             and any(path == a or path.startswith(a + '/') for a in anc)]
    return ' + '.join(names), ' + '.join(urls), (max(dates) if dates else '')


def record_for(rel, prov):
    """The provenance record covering a raw file.

    Its own, else the nearest ANCESTOR DIRECTORY's - an archive is landed with
    one record and unpacked into many files, and every one of those members
    was retrieved from the same place at the same moment. 9.151 (#149): five
    speed-zone shapefile parts, and the members of every other unpacked
    download, carried no source and no retrieval date for want of this rule.
    """
    if rel in prov:
        return prov[rel]
    parts = rel.split('/')
    for cut in range(len(parts) - 1, 0, -1):
        here = '/'.join(parts[:cut])
        best = None
        for path, rec in prov.items():
            if path.rsplit('/', 1)[0] == here and rec.get('retrieved'):
                if best is None or path < best[0]:
                    best = (path, rec)
        if best:
            return best[1]
    return {}


def licence_for(rel, stage, pr):
    """The licence a manifest row carries, by declaration (#117).

    raw: the declared source's licence where a source covers the path (the
    descriptor is canonical); else the record's own; else, for the package's
    own record files (provenance*.json, the `_`-prefixed logs and listings),
    the package licence. processed: the longest matching `derived_licences`
    glob, else the package licence. A blank is a row nobody declared, and
    tests/check_manifest.py refuses it.
    """
    src = source_for(rel)
    if stage == 'raw':
        if src and src.get('licence'):
            return src['licence']
        if pr.get('licence'):
            return pr['licence']
        name = os.path.basename(rel)
        if name.startswith('provenance') or name.startswith('_'):
            return PACKAGE_LICENCE
        return ''
    best = ''
    for pat in DERIVED_LICENCES:
        if fnmatch.fnmatch(rel, pat) and len(pat) > len(best):
            best = pat
    return DERIVED_LICENCES.get(best) or PACKAGE_LICENCE


def scan_paths():
    """Every city-relative path the manifest will carry, in walk order."""
    out = []
    for base in SCAN:
        base = os.path.join(ROOT, base)
        if not os.path.isdir(base):
            continue
        for dirpath, _, names in os.walk(base):
            for n in sorted(names):
                p = os.path.join(dirpath, n)
                if os.path.splitext(n)[1].lower() in SKIP_EXT \
                        or '__pycache__' in dirpath:
                    continue
                rel = os.path.relpath(p, ROOT).replace('\\', '/')
                if rel.startswith(SKIP_DIRS):
                    continue
                out.append(rel)
    return out


def main():
    prov = provenance_records()
    paths = scan_paths()
    # which producing scripts write exactly one row - resolved before any row,
    # because a sole output's script-level union IS its output-level ancestry
    index_outputs(paths)

    files = []
    for rel in paths:
        p = os.path.join(ROOT, rel.replace('/', os.sep))
        sz = os.path.getsize(p)
        stage = 'raw' if rel.startswith(('data/raw', 'networks/osm', 'schedules/raw')) \
            else 'processed'
        pr = record_for(rel, prov) if stage == 'raw' else prov.get(rel, {})
        src = source_for(rel) if stage == 'raw' else None
        source = (pr.get('description') or pr.get('source')
                  or (src or {}).get('name', ''))
        source_url = (pr.get('url') or pr.get('s3_key')
                      or (src or {}).get('url', ''))
        retrieved = pr.get('retrieved', '')
        name = os.path.basename(rel)
        proven, possible, scope = ancestry(rel)
        if (stage == 'raw' and not source
                and (name.startswith('provenance')
                     or name.startswith('_'))):
            # The package's own record of itself, not acquired data -
            # the same class licence_for() already recognises.
            source = PACKAGE_RECORD
            proven, possible, scope = set(), set(), 'output'
        if stage != 'raw' and not source:
            # 9.151 (#149): a derived file's provenance is its raw
            # ancestry, resolved from the lineage rather than typed in.
            # #159: that ancestry is now OUTPUT-level where the
            # producing script declares it, and says so in `lineage_scope`.
            source, source_url, retrieved = derived_provenance(rel, prov,
                                                               possible)
        files.append(dict(
            path=rel, bytes=sz, rows=count_rows(p),
            # EVERY file is hashed. Three were size-only under a 300 MB cap -
            # two raw downloads the immutability rule protects and the WEEKDAY
            # trip table every plan derives from - so a rebuilt demand of the
            # same byte length passed the gate (eighth project report, 11
            # September 2026). ~1.6 GB more to hash, about ten seconds.
            sha256=sha256(p),
            stage=stage,
            produced_by=lineage_for(rel),
            source=source, source_url=source_url,
            licence=licence_for(rel, stage, pr),
            retrieved=retrieved,
            lineage_scope=scope,
            share_alike_ancestor=share_alike_verdict(proven, possible, scope)))

    total = sum(f['bytes'] for f in files)
    man = dict(
        project=_city.descriptor().get('description') or _city.descriptor()['name'],
        generated=datetime.datetime.now().replace(microsecond=0).isoformat(),
        base_year=_city.base_year(),
        crs=_city.crs_label(),
        n_files=len(files),
        total_bytes=total,
        total_gib=round(total / (1 << 30), 2),
        by_stage={s: sum(1 for f in files if f['stage'] == s) for s in ('raw', 'processed')},
        bytes_by_stage={s: sum(f['bytes'] for f in files if f['stage'] == s)
                        for s in ('raw', 'processed')},
        by_lineage_scope={s: sum(1 for f in files if f['lineage_scope'] == s)
                          for s in ('raw', 'output', 'script', 'none')},
        by_share_alike_ancestor={
            v: sum(1 for f in files if f['share_alike_ancestor'] == v)
            for v in ('yes', 'no', 'undetermined')},
        files=files)
    json.dump(man, open(os.path.join(ROOT, 'data', 'MANIFEST.json'), 'w', newline='\n'), indent=2)
    cols = ['path', 'stage', 'bytes', 'rows', 'produced_by', 'source', 'source_url',
            'licence', 'retrieved', 'lineage_scope', 'share_alike_ancestor',
            'sha256']
    with open(os.path.join(ROOT, 'data', 'MANIFEST.csv'), 'w', newline='',
          encoding='utf-8') as fh:
        # `newline=''` hands the line ending to the csv module, whose default
        # is CRLF on every platform - so the manifest was written with CRLF,
        # git committed it as LF, and the file's own recorded hash stopped
        # matching the bytes in the repository. LF explicitly: a committed
        # artefact must be regenerable byte for byte wherever it is built.
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction='ignore',
                           lineterminator='\n')
        w.writeheader()
        w.writerows(files)
    print('files=%d  total=%.2f GiB' % (len(files), man['total_gib']))
    print('by stage:', man['by_stage'], man['bytes_by_stage'])
    print('lineage scope:', man['by_lineage_scope'])
    print('share-alike ancestor:', man['by_share_alike_ancestor'])
    print('\nlargest 12:')
    for f in sorted(files, key=lambda x: -x['bytes'])[:12]:
        print('  %10.1f MB  %s' % (f['bytes'] / 1e6, f['path']))


if __name__ == '__main__':
    main()
