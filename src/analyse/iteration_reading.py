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
import gzip
import io
import os

_CACHE = {}


def clear():
    """Forget every cached table (a long-lived process reading many runs)."""
    _CACHE.clear()


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
    return rows
