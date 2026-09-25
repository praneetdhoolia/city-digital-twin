"""One reader for a run's iteration tables, parsed once per process (#182).

Nine scripts under src/analyse/ used to open a run's trips and legs tables
each in their own way, and inside one script the same table was parsed up
to four times - `extract_metrics.py` read `output_trips` four times and
`output_legs` twice, `report_mode_ridership.report()` read the iteration's
trips twice (eighth project report, 11 September 2026, area 3). On a 25 %
arm a table is a multi-GB decoded read on the disk the JVM is writing to,
and the gate watcher pays it at every milestone.

This module owns the two questions every reader asks - WHERE an iteration's
table is, and WHAT its rows are - and answers the second once: a table is
decoded into memory the first time a process asks for it and served from
there after. Rows are the same dicts `csv.DictReader` produced, so every
consumer reads exactly what it read before; only the number of decodes
changes. The cache is per process and is what a gate-watcher subprocess or
a close-out pass holds for the one iteration it reads.

    from iteration_reading import table, table_path
    for r in table(run_dir, 'trips', iteration):     # 'trips' | 'legs'
        ...

`iteration=None` means the FINAL output (`output/output_trips.csv.gz`),
which only a run that reached its last iteration has; an integer means
`output/ITERS/it.N/N.trips.csv.gz`, the milestone table a stopped arm is
citable at. `table_path` says which file that is, or None if it is absent,
so a caller can refuse loudly instead of reading nothing.
"""
import csv
import glob
import gzip
import io
import os
import re

import collections

# Bounded: `--trend` over a 300-iteration arm reads thirty trips tables of
# hundreds of MB each at 25 %, and the gate watcher imports this module for
# the run's lifetime (ninth report, 14 September 2026, finding 23). The
# newest CACHE_TABLES tables stay; a reader that wants two tables of one
# iteration (trips and legs) is inside the bound.
CACHE_TABLES = 6
_CACHE = collections.OrderedDict()


def clear():
    """Forget every cached table (a long-lived process reading many runs)."""
    _CACHE.clear()


def innovation_off_after(first, last, fraction):
    """The iteration after which MATSim creates no new plans.

    MATSim's own arithmetic, `(last - first) * fraction + first`, truncated -
    the formula `citysim.EscortCoherenceListener.innovationOffAfter` and the
    pinned jar's `StrategyManager` both compute. Two Python readers computed
    `fraction * last` and ignored `firstIteration`, which is 0 on a cold arm
    and the resume point on a warm-started one, so a resumed arm (first 300,
    last 600, fraction 0.8) was judged relaxed from 480 while innovation ran
    to 540 (ninth report, 14 September 2026, finding 3).
    """
    if first is None or last is None or fraction is None:
        return None
    first, last, fraction = int(first), int(last), float(fraction)
    return int((last - first) * fraction + first)


def table_path(run_dir, stem, iteration=None):
    """The file holding this table, or None. `stem` is 'trips' or 'legs'."""
    if iteration is None:
        base = os.path.join(run_dir, 'output', 'output_%s' % stem)
    else:
        base = os.path.join(run_dir, 'output', 'ITERS', 'it.%d' % int(iteration),
                            '%d.%s' % (int(iteration), stem))
    for ext in ('.csv.gz', '.csv', '.csv.zst'):
        if os.path.exists(base + ext):
            return base + ext
    return None


def iterations_with(run_dir, stem='trips'):
    """Iterations whose per-iteration `stem` table exists, ascending.

    A run writes its trips and legs tables on the interval its config
    declares (every 10th), so the iteration a stopped arm REACHED usually has
    none; the newest of these at or below it is where the arm is citable.
    """
    found = []
    for d in glob.glob(os.path.join(run_dir, 'output', 'ITERS', 'it.*')):
        try:
            n = int(os.path.basename(d).split('.', 1)[1])
        except (IndexError, ValueError):
            continue
        if table_path(run_dir, stem, n) is not None:
            found.append(n)
    return sorted(found)


_PERSON_ATTR = re.compile(r'<attribute name="([^"]+)"[^>]*>([^<]*)</attribute>')
_PERSON_ID = re.compile(r'<person id="([^"]+)"')


def person_attributes(run_dir, names):
    """{person id: {name: value}} for the attributes `names`, as THIS run carried them.

    From `output/output_persons.csv.gz` when the run reached its end; else from
    the run's own input `plans.xml.gz`, which carries the same person
    attributes - a stopped arm writes no `output_persons`, and the readers
    that required it (measure_bound_trips, mode_by_demographics) could not
    read F36's arm 0 at all (fourteenth report). Values are strings either
    way; a missing attribute is absent from the person's dict.
    """
    names = set(names)
    out = {}
    final = os.path.join(run_dir, 'output', 'output_persons.csv.gz')
    if os.path.exists(final):
        with gzip.open(final, 'rt', encoding='utf-8', newline='') as fh:
            for r in csv.DictReader(fh, delimiter=';'):
                out[r['person']] = {k: r[k] for k in names if r.get(k) not in (None, '')}
        return out
    plans = os.path.join(run_dir, 'plans.xml.gz')
    if not os.path.exists(plans):
        raise FileNotFoundError('%s has neither output_persons nor its input plans' % run_dir)
    pid = None
    in_plan = False
    with gzip.open(plans, 'rt', encoding='utf-8') as fh:
        for line in fh:
            if '<person ' in line:
                pid = _PERSON_ID.search(line).group(1)
                out[pid] = {}
                in_plan = False
            elif '<plan' in line:
                in_plan = True           # plan attributes are not person attributes
            elif '</person>' in line:
                pid = None
            elif pid is not None and not in_plan and '<attribute ' in line:
                m = _PERSON_ATTR.search(line)
                if m and m.group(1) in names:
                    out[pid][m.group(1)] = m.group(2)
    return out


def open_table(path):
    """A text handle on a MATSim table, whatever it was compressed with."""
    if path.endswith('.gz'):
        return gzip.open(path, 'rt', encoding='utf-8', newline='')
    if path.endswith('.zst'):
        try:
            import zstandard                                   # noqa: PLC0415
        except ImportError:
            raise SystemExit(
                '%s is .zst, from a run made before compressionType=gzip was '
                'set, and `zstandard` is not installed. Re-run it, or install '
                'zstandard for this one analysis - it is deliberately not a '
                'declared dependency of this repo.' % path)
        return io.TextIOWrapper(zstandard.ZstdDecompressor().stream_reader(
            open(path, 'rb')), encoding='utf-8')
    return open(path, encoding='utf-8', newline='')


def table(run_dir, stem, iteration=None):
    """The rows of an iteration's table, decoded once per process.

    Returns the cached list; callers iterate it and must not mutate it.
    Raises FileNotFoundError when the table is absent - the caller decides
    whether that is a refusal or a stated gap.
    """
    key = (os.path.abspath(run_dir), stem, None if iteration is None else int(iteration))
    rows = _CACHE.get(key)
    if rows is not None:
        return rows
    path = table_path(run_dir, stem, iteration)
    if path is None:
        raise FileNotFoundError('no %s table for %s at %s' % (
            stem, run_dir, 'the final output' if iteration is None else 'iteration %s' % iteration))
    with open_table(path) as fh:
        rows = list(csv.DictReader(fh, delimiter=';'))
    _CACHE[key] = rows
    while len(_CACHE) > CACHE_TABLES:
        _CACHE.popitem(last=False)
    return rows


# ------------------------------------------------------------------ events
#
# THE EVENTS FILE IS READ BY ONE PARSER. Four readers streamed it with three
# parsers of their own - summarise_run's per-mode accounting and
# frontage_volumes's traversals with ElementTree, report_mode_ridership's
# count-station tally and replay_events's frames with line regexes (twelfth
# report, 16 September 2026). One generator yields every event as
# (type, attributes); `scan_events` runs any number of handlers over one pass,
# so the readers that run together at a close-out pay for one decode.
from xml.sax.saxutils import unescape as _sax_unescape

_re = re
# MATSim escapes a quote inside a value as &quot;; saxutils decodes only
# &amp; &lt; &gt; unless told the others (fourteenth report)
_QUOTES = {'&quot;': '"', '&apos;': "'"}


def _unescape(value):
    return _sax_unescape(value, _QUOTES)


_EVENT_LINE = _re.compile(r'<event\s')
_ATTR = _re.compile(r'(\w+)="([^"]*)"')
_EVENT_TYPE = _re.compile(r'\btype="([^"]*)"')


def events(path, event_types=None, attribute_values=None):
    """Yield (type, attrs) for every <event .../> in a MATSim events file.

    Reads plain, gzip or zstandard XML line by line and parses attributes with one regular
    expression per event: MATSim writes one event per line with every value
    quoted, and it entity-escapes a value that carries `&`, `<` or `"`, which
    is unescaped here so the dict reads what ElementTree would have read.

    An optional type filter avoids decoding every attribute of irrelevant
    events in a large file. Matching uses the decoded event type.
    Optional attribute selectors are conjunctive maps to allowed value sets.
    """
    wanted = None if event_types is None else frozenset(event_types)
    selectors = [(_re.compile(r'\b' + _re.escape(key) + r'="([^"]*)"'), frozenset(values))
                 for key, values in (attribute_values or {}).items()]
    literal_selectors = [tuple(key + '="' + value + '"' for value in values)
                         for key, values in (attribute_values or {}).items()]
    with open_table(str(path)) as f:
        for line in f:
            if not _EVENT_LINE.search(line):
                continue
            # Plain values dominate native link/vehicle IDs. Avoid regex work
            # on irrelevant lines, but retain decoded matching for entities.
            if '&' not in line and any(not any(token in line for token in tokens)
                                       for tokens in literal_selectors):
                continue
            if wanted is not None:
                kind = _EVENT_TYPE.search(line)
                if kind is None or _unescape(kind.group(1)) not in wanted:
                    continue
            if any((match := pattern.search(line)) is None or _unescape(match.group(1)) not in values
                   for pattern, values in selectors):
                continue
            attrs = dict(_ATTR.findall(line))
            if '&' in line:
                attrs = {k: (_unescape(v) if '&' in v else v) for k, v in attrs.items()}
            yield attrs.get('type'), attrs


def scan_events(path, *handlers):
    """One pass of the events file over every handler: each is called with
    (type, attrs) per event, or, when it has an `events` attribute naming the
    types it wants, only for those. Returns the handlers, for chaining."""
    wants = []
    for h in handlers:
        w = getattr(h, 'events', None)
        wants.append(set(w) if w else None)
    for t, attrs in events(path):
        for h, w in zip(handlers, wants):
            if w is None or t in w:
                h(t, attrs)
    return handlers
