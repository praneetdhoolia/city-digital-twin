"""The results store: one module owns where a run's bytes live (issue: user
directive, 1 September 2026; DECISIONS.md 9.137).

`results/raw/<run>` holds a run's bulk - matsim.log, events, plans, ITERS -
and is a CACHE with a declared byte budget (`RUN.storage.raw_cap_gb`).
`results/processed/<run>` holds the run's FINDINGS - the record files and the
mode-ridership snapshots - and is never trimmed. Every consumer resolves a run
through this module, the way `src/city.py` is the only module that knows where
a city lives; nothing else may compose a `results/...` path.

The store is automatic end to end: the runner creates raw dirs, mirrors every
record transition into processed, extracts the reading snapshots at run end,
and trims raw oldest-first back under budget at every harness start and run
end. Deleting from raw is THIS module's call and nobody else's - the 9.65 rule
that the harness never deletes a run directory is superseded by the 1 Sep 2026
user directive (9.137): findings are kept forever in processed, bulk is a
budgeted cache. A person never renames, deletes or edits anything under
`results/` by hand.
"""
import glob
import io
import json
import os
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
RESULTS = os.path.join(REPO, 'results')
RAW = os.path.join(RESULTS, 'raw')
PROCESSED = os.path.join(RESULTS, 'processed')

# The record and summary files that ARE a run's findings, mirrored verbatim.
# Bulk (matsim.log, events, plans, ITERS, output/) stays in raw and dies with
# it; a reading someone will quote must live in a record or a snapshot below.
RECORD_FILES = ('_meta.json', '_run.json', '_config.json', '_progress.json',
                '_metrics.json', '_summary.json', '_fit.json',
                '_gate_stop.json', 'SUMMARY.md', 'config.xml')
# Reading snapshots extracted from the bulk before it can be trimmed: the
# twelve-mode trend across every readable iteration, and the newest readable
# iteration's table as JSON. Extraction failures are logged into the processed
# dir, never raised - the store must keep working unattended.
TREND_TXT = 'modes_trend.txt'
FINAL_JSON = 'modes_final.json'
PROCESS_LOG = '_process_log.txt'


def raw_dir(name):
    return os.path.join(RAW, name)


def processed_dir(name):
    return os.path.join(PROCESSED, name)


def resolve(name_or_path):
    """A run's BULK directory from a name or any legacy path, else None.

    Accepts an absolute or relative path that exists (handed back as is), a
    bare run name under raw/, or a legacy `results/<name>` spelling. Returns
    None when only processed findings remain (the bulk was trimmed).
    """
    if os.path.isdir(name_or_path):
        return os.path.abspath(name_or_path)
    name = os.path.basename(os.path.normpath(name_or_path))
    for candidate in (raw_dir(name), os.path.join(RESULTS, name)):
        if os.path.isdir(candidate):
            return candidate
    legacy = resolve_legacy_name(name)
    if legacy is not None and os.path.isdir(raw_dir(legacy)):
        return raw_dir(legacy)
    return None


_LEGACY = {}


def resolve_legacy_name(name):
    """The runner-named directory a HAND-NAMED run lives in, or None (#137).

    Runs before 9.65 were named by hand (`phys1000a_25pct`); the runner then
    renamed every directory to its launch stamp and the hand name survived
    only as `name` inside the run's own `_run.json`. Records that cite the
    hand name - C5_calibration.json's best_tag, the calibration report -
    resolve through it here, scanning processed (findings are permanent) and
    raw once and remembering the answer.
    """
    if name in _LEGACY:
        return _LEGACY[name]
    found = None
    for root in (PROCESSED, RAW):
        if not os.path.isdir(root):
            continue
        for entry in sorted(os.listdir(root)):
            rec = os.path.join(root, entry, '_run.json')
            if not os.path.exists(rec):
                continue
            try:
                with io.open(rec, encoding='utf-8') as fh:
                    doc = json.load(fh)
            except (OSError, ValueError):
                continue
            if doc.get('name') == name or doc.get('tag') == name:
                found = entry
                break
        if found:
            break
    _LEGACY[name] = found
    return found


def resolve_records(name_or_path):
    """The directory holding a run's RECORD files: raw while it exists,
    processed after a trim. None only when the run is unknown entirely."""
    bulk = resolve(name_or_path)
    if bulk is not None:
        return bulk
    name = os.path.basename(os.path.normpath(name_or_path))
    p = processed_dir(name)
    if os.path.isdir(p):
        return p
    legacy = resolve_legacy_name(name)
    if legacy is not None and os.path.isdir(processed_dir(legacy)):
        return processed_dir(legacy)
    return None


def run_names():
    """Every run name the store knows - raw and processed united, deduped."""
    names = set()
    for root in (RAW, PROCESSED):
        if os.path.isdir(root):
            names.update(n for n in os.listdir(root)
                         if os.path.isdir(os.path.join(root, n)))
    # legacy top-level dirs (pre-migration); _launch and the two store roots
    # are not runs
    if os.path.isdir(RESULTS):
        names.update(n for n in os.listdir(RESULTS)
                     if os.path.isdir(os.path.join(RESULTS, n))
                     and n not in ('raw', 'processed', '_launch'))
    return sorted(names)


def _log(name, message):
    os.makedirs(processed_dir(name), exist_ok=True)
    line = '%s %s\n' % (time.strftime('%Y-%m-%dT%H:%M:%S'), message)
    with io.open(os.path.join(processed_dir(name), PROCESS_LOG), 'a',
                 encoding='utf-8') as fh:
        fh.write(line)


def mirror(run_dir):
    """Copy the record files of one raw run into its processed dir.

    Called at every record transition and harmless to repeat; copies are
    byte-identical so re-mirroring an unchanged file is a no-op in effect.
    """
    name = os.path.basename(os.path.normpath(run_dir))
    dest = processed_dir(name)
    os.makedirs(dest, exist_ok=True)
    for fname in RECORD_FILES:
        src = os.path.join(run_dir, fname)
        if os.path.exists(src):
            try:
                shutil.copy2(src, os.path.join(dest, fname))
            except OSError as e:
                _log(name, 'mirror failed for %s: %s' % (fname, e))


def rename(old_name, new_name):
    """Follow a raw rename (aborted_<name>) in processed, keeping one home."""
    old_p, new_p = processed_dir(old_name), processed_dir(new_name)
    if os.path.isdir(old_p) and not os.path.exists(new_p):
        try:
            os.rename(old_p, new_p)
        except OSError as e:
            _log(new_name, 'processed rename %s -> %s failed: %s'
                 % (old_name, new_name, e))


def extract_snapshots(name):
    """Write the mode-ridership snapshots for one run into processed.

    Runs the twelve-mode reporter on the raw bulk: `--trend` across every
    readable iteration, and the newest iteration's table as JSON. Requires the
    bulk; failures are logged, never raised.
    """
    bulk = resolve(name)
    if bulk is None:
        _log(name, 'extract skipped: no raw bulk to read')
        return False
    dest = processed_dir(name)
    os.makedirs(dest, exist_ok=True)
    reporter = os.path.join(REPO, 'src', 'analyse', 'report_mode_ridership.py')
    ok = True
    try:
        out = subprocess.run(
            [sys.executable, reporter, '--run', bulk, '--trend'],
            capture_output=True, text=True, timeout=3600, cwd=REPO)
        if out.returncode == 0 and out.stdout.strip():
            with io.open(os.path.join(dest, TREND_TXT), 'w',
                         encoding='utf-8') as fh:
                fh.write(out.stdout)
        else:
            ok = False
            _log(name, 'trend extract rc=%s: %s'
                 % (out.returncode, (out.stderr or out.stdout)[-400:]))
    except (OSError, subprocess.SubprocessError) as e:
        ok = False
        _log(name, 'trend extract failed: %s' % e)
    try:
        out = subprocess.run(
            [sys.executable, reporter, '--run', bulk,
             '--json', os.path.join(dest, FINAL_JSON)],
            capture_output=True, text=True, timeout=1800, cwd=REPO)
        if out.returncode != 0:
            ok = False
            _log(name, 'final-json extract rc=%s: %s'
                 % (out.returncode, (out.stderr or out.stdout)[-400:]))
    except (OSError, subprocess.SubprocessError) as e:
        ok = False
        _log(name, 'final-json extract failed: %s' % e)
    return ok


def process(name, extract=False):
    """Mirror one run's records into processed; optionally extract snapshots."""
    bulk = resolve(name)
    if bulk is not None:
        mirror(bulk)
        if extract:
            extract_snapshots(name)


def reconcile_names():
    """A raw `aborted_<name>` whose processed twin still carries `<name>`
    is renamed in processed too, so a run keeps ONE name.

    `rename()` follows a raw rename at the moment it happens; when that
    rename loses to a directory lock - or happened before the store existed -
    the processed twin keeps the old name and the run index lists the arm
    twice (the F23 gate arm, 3 Sep 2026). Idempotent; a twin that exists
    under both names is left for a person to compare, and said so.
    """
    fixed = []
    if not os.path.isdir(RAW) or not os.path.isdir(PROCESSED):
        return fixed
    for entry in sorted(os.listdir(RAW)):
        if not entry.startswith('aborted_') or not os.path.isdir(raw_dir(entry)):
            continue
        base = entry[len('aborted_'):]
        old_p, new_p = processed_dir(base), processed_dir(entry)
        if not os.path.isdir(old_p):
            continue
        if os.path.isdir(new_p):
            _log(entry, 'processed twin exists under both %s and %s; not merged'
                 % (base, entry))
            continue
        try:
            os.rename(old_p, new_p)
            fixed.append((base, entry))
            _log(entry, 'processed rename %s -> %s (reconciled)' % (base, entry))
        except OSError as e:
            _log(entry, 'processed rename %s -> %s failed: %s' % (base, entry, e))
    return fixed


def migrate():
    """Move legacy `results/<run>` dirs under raw/ and seed processed.

    Idempotent; skips `_launch`, the store roots and loose files. A move that
    loses to a directory lock is reported and retried at the next call. Also
    reconciles a processed twin left under a run's pre-abort name.
    """
    os.makedirs(RAW, exist_ok=True)
    os.makedirs(PROCESSED, exist_ok=True)
    moved = []
    reconcile_names()
    if not os.path.isdir(RESULTS):
        return moved
    for entry in sorted(os.listdir(RESULTS)):
        src = os.path.join(RESULTS, entry)
        if entry in ('raw', 'processed', '_launch') or not os.path.isdir(src):
            continue
        dest = raw_dir(entry)
        if os.path.exists(dest):
            _log(entry, 'migrate skipped: %s already exists under raw' % entry)
            continue
        try:
            os.rename(src, dest)
            moved.append(entry)
        except OSError as e:
            print('migrate: could not move %s under raw/ (%s); will retry '
                  'next invocation' % (entry, e), flush=True)
            continue
        mirror(dest)
    return moved


def _dir_bytes(path):
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def raw_size_bytes():
    return _dir_bytes(RAW) if os.path.isdir(RAW) else 0


def _pid_alive(pid):
    if os.name == 'nt':
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = k32.OpenProcess(0x00100000, 0, int(pid))     # SYNCHRONIZE
        if not handle:
            return False
        rc = k32.WaitForSingleObject(handle, 0)
        k32.CloseHandle(handle)
        return rc == 0x102
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def _is_running(run_dir):
    meta = os.path.join(run_dir, '_meta.json')
    try:
        with io.open(meta, encoding='utf-8') as fh:
            doc = json.load(fh)
    except (OSError, ValueError):
        return False
    return doc.get('status') == 'running' and doc.get('pid') \
        and _pid_alive(doc['pid'])


def _launch_stamp(name):
    """Order key: the launch stamp, ignoring the aborted_ label."""
    base = name[len('aborted_'):] if name.startswith('aborted_') else name
    return base


def trim(cap_gb, log=print):
    """Delete the oldest raw run dirs until raw is at or under `cap_gb`.

    Findings are extracted into processed before a dir is deleted; a live run
    is never deleted. Every deletion is appended to `processed/_trim_log.json`
    so the cache's history is itself a record.
    """
    if not os.path.isdir(RAW):
        return []
    cap = float(cap_gb) * (1 << 30)
    size = raw_size_bytes()
    if size <= cap:
        return []
    entries = sorted((n for n in os.listdir(RAW)
                      if os.path.isdir(raw_dir(n))), key=_launch_stamp)
    deleted = []
    for name in entries:
        if size <= cap:
            break
        d = raw_dir(name)
        if _is_running(d):
            continue
        # a completed run whose metrics are not yet extracted is never
        # deleted (#132): run.py extracts _metrics.json after run() returns,
        # and a concurrent harness's trim could reach the directory first.
        # prune_run.py refuses exactly this case; so does trim now.
        if os.path.exists(os.path.join(d, '_run.json')) \
                and not os.path.exists(os.path.join(d, '_metrics.json')):
            log('trim: keeping raw/%s - completed, metrics not yet extracted'
                % name)
            continue
        process(name, extract=True)
        freed = _dir_bytes(d)
        try:
            shutil.rmtree(d)
        except OSError as e:
            log('trim: could not delete %s (%s); skipping' % (name, e))
            continue
        size -= freed
        deleted.append(dict(name=name, bytes=freed,
                            deleted=time.strftime('%Y-%m-%dT%H:%M:%S')))
        log('trim: deleted raw/%s (%.1f GiB); raw now %.1f GiB'
            % (name, freed / (1 << 30), size / (1 << 30)))
    if deleted:
        path = os.path.join(PROCESSED, '_trim_log.json')
        history = []
        if os.path.exists(path):
            try:
                with io.open(path, encoding='utf-8') as fh:
                    history = json.load(fh)
            except (OSError, ValueError):
                history = []
        history.extend(deleted)
        with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(history, fh, indent=1)
    return deleted


def maintain(cap_gb, log=print):
    """The one call a harness makes: migrate anything legacy, then trim."""
    moved = migrate()
    if moved:
        log('results store: migrated %d run(s) under results/raw' % len(moved))
    return trim(cap_gb, log=log)
