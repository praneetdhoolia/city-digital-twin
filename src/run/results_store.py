"""The results store: one module owns where a run's bytes live (issue: user
directive, 1 September 2026; DECISIONS.md 9.137).

`results/raw/<run>` holds a run's bulk - matsim.log, events, plans, ITERS -
and is a CACHE with a declared byte budget (`RUN.storage.raw_cap_gb`, GIBIBYTES).
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


def _findings_in_processed(name):
    """Does processed already hold a substantive finding for this run?

    A `_meta.json` alone does NOT count: it carries the run's cause, not its
    readings. What counts is a metrics document or the mode snapshots - the
    things a living document actually cites.
    """
    dest = processed_dir(name)
    return any(os.path.exists(os.path.join(dest, f))
               for f in ('_metrics.json', TREND_TXT, FINAL_JSON))


def process(name, extract=False):
    """Mirror one run's records into processed; optionally extract snapshots.

    Returns whether the findings are now SAFE IN PROCESSED - True when the
    snapshots were written (or none were asked for), False when the extraction
    was attempted and did not produce them. `trim` refuses to delete a bulk
    directory on a False, because deleting it would destroy the only copy of a
    reading rather than reclaim a duplicate of one.
    """
    bulk = resolve(name)
    if bulk is None:
        return False
    mirror(bulk)
    if extract:
        return bool(extract_snapshots(name))
    return True


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


def _record_age_s(run_dir):
    """Seconds since this run's record was last written, or None if unreadable.

    The newest of the record files, not the directory's own mtime: a directory
    is touched by anything that walks it, while a record file is written only
    by the harness that owns the run.
    """
    newest = None
    for fname in RECORD_FILES:
        p = os.path.join(run_dir, fname)
        try:
            m = os.path.getmtime(p)
        except OSError:
            continue
        if newest is None or m > newest:
            newest = m
    return None if newest is None else max(0.0, time.time() - newest)


def trim(cap_gb, log=print, grace_s=None):
    """Delete the oldest raw run dirs until raw is at or under `cap_gb`.

    Findings are extracted into processed before a dir is deleted; a live run
    is never deleted. Every deletion is appended to `processed/_trim_log.json`
    so the cache's history is itself a record.

    `grace_s` is RUN.storage.extract_grace_s - how long a run whose
    `_metrics.json` has not appeared is still presumed to be inside its
    extraction window (9.155). Past it the run is closed out and its bulk is
    reclaimable.
    """
    if grace_s is None:
        raise TypeError(
            'trim() needs RUN.storage.extract_grace_s: pass grace_s='
            "cfg.get('RUN.storage.extract_grace_s'). The store resolves no "
            'declared value itself - its caller supplies them, exactly as it '
            'does for cap_gb (9.155).')
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
        # a run whose metrics are not yet extracted is never deleted (#132):
        # run.py extracts _metrics.json after run() returns, and a concurrent
        # harness's trim could reach the directory first. prune_run.py refuses
        # exactly this case; so does trim.
        #
        # The window is bounded (9.155). run.py writes _metrics.json only when
        # it survives the run; an operator stop or a gate stop kills the
        # harness first, so those runs never get one and the unbounded form of
        # this guard kept them forever - measured 7 Sep 2026 at 13 directories
        # and 72.8 GiB, 16% of a 90%-full cache, every one of them already
        # mirrored into processed. When the cap was hit the store skipped all
        # thirteen and deleted younger COMPLETE runs instead. So the guard now
        # asks what it always meant: is this run still inside its extraction
        # window? Past the grace it is closed out, and close_out() has already
        # mirrored its records and snapshots into processed, which is never
        # trimmed.
        if os.path.exists(os.path.join(d, '_run.json')) \
                and not os.path.exists(os.path.join(d, '_metrics.json')):
            age = _record_age_s(d)
            if age is None or age <= grace_s:
                log('trim: keeping raw/%s - metrics not yet extracted '
                    '(record %s s old, grace %s s)'
                    % (name, 'unreadable' if age is None else int(age), grace_s))
                continue
            log('trim: raw/%s is past its %s s extraction grace and its '
                'findings are in processed; reclaiming the bulk'
                % (name, grace_s))
        # A RUN THAT WAS NEVER CLOSED OUT HAS NEVER HAD ITS FINDINGS MIRRORED.
        #
        # The grace guard above reasons about a run that HAS a `_run.json`: past
        # its window it has been closed out, and close_out() has already put its
        # records and snapshots in processed, which is never trimmed. A run with
        # NO record at all has had none of that happen, and it is not covered by
        # that guard at all - it falls straight through to the delete.
        #
        # The oldest directories in this store are exactly those, because they
        # predate the record contract. Measured 8 Sep 2026:
        # `aborted_20260901T165115_300it_25pct` (173.40 GiB) and
        # `aborted_20260831T165127_300it_25pct` (163.03 GiB) are the 2nd and 7th
        # oldest in a store at 93.4% of its cap, carry no `_run.json`, have no
        # snapshots in processed, and are cited by ELEVEN lines across eight
        # position pages - one of which gives a reproduce command that reads the
        # bulk directly. Oldest-first with no pin would have deleted both on the
        # next launch that found the cap exceeded, and the readings would have
        # gone with them.
        #
        # So: no record, and no findings already in processed, means the bulk is
        # the ONLY copy of whatever it is cited for. Extraction is attempted; if
        # it does not produce the snapshots, the directory stays and says why.
        # The store then sits over its cap, which is a visible problem someone
        # must act on, rather than quietly becoming the place a cited figure
        # used to live.
        if not os.path.exists(os.path.join(d, '_run.json')) \
                and not _findings_in_processed(name):
            if not process(name, extract=True):
                log('trim: KEEPING raw/%s - it carries no run record, so it was '
                    'never closed out and its findings were never mirrored; the '
                    'extraction did not produce them either, so deleting the '
                    'bulk would destroy the reading rather than reclaim a copy '
                    'of it. Extract it by hand, re-aim whatever cites it at '
                    'processed/, then trim.' % name)
                continue
        else:
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


def maintain(cap_gb, log=print, grace_s=None):
    """The one call a harness makes: migrate anything legacy, then trim."""
    moved = migrate()
    if moved:
        log('results store: migrated %d run(s) under results/raw' % len(moved))
    return trim(cap_gb, log=log, grace_s=grace_s)


def reclaim(name, log=print):
    """Reclaim ONE run's bulk on purpose, once its findings are safe (#164).

    `trim` reclaims oldest-first and only while the store is OVER its cap, which
    is the wrong instrument for the case #164 filed: two arms holding 336.4 GiB
    between them in a store at 93.4 % of cap, each of them reclaimable in
    principle and neither reclaimed, because the cap had not yet been crossed.
    Waiting for it to be crossed means the reclaim happens DURING the next long
    arm rather than before it - which is what the issue was about.

    So an operator may reclaim a named run, and the guard is the same one trim
    applies and is not negotiable here either: the findings must already be in
    processed, and the run must not be running. Nothing is deleted from
    `processed/` ever (9.137), so what goes is the re-derivable bulk - the log,
    the events, the plans and the per-iteration tables - and what stays is every
    reading anyone has quoted. A run whose findings are NOT mirrored is refused
    rather than extracted-then-deleted in one step: extraction is a separate,
    checkable act, and fusing them is how a silent extraction failure becomes a
    deletion.
    """
    d = raw_dir(name)
    if not os.path.isdir(d):
        log('reclaim: raw/%s is not in the store (already reclaimed?)' % name)
        return None
    if _is_running(d):
        log('reclaim: REFUSED - raw/%s is running' % name)
        return None
    if not _findings_in_processed(name):
        log('reclaim: REFUSED - raw/%s has no findings in processed. Extract '
            'them first (results_store.process(name, extract=True)), confirm '
            'they carry the readings anything cites, then reclaim.' % name)
        return None
    freed = _dir_bytes(d)
    try:
        shutil.rmtree(d)
    except OSError as e:
        log('reclaim: could not delete raw/%s (%s)' % (name, e))
        return None
    entry = dict(name=name, bytes=freed, reclaimed_by='operator',
                 deleted=time.strftime('%Y-%m-%dT%H:%M:%S'))
    path = os.path.join(PROCESSED, '_trim_log.json')
    history = []
    if os.path.exists(path):
        try:
            with io.open(path, encoding='utf-8') as fh:
                history = json.load(fh)
        except (OSError, ValueError):
            history = []
    history.append(entry)
    with io.open(path, 'w', encoding='utf-8', newline='\n') as fh:
        json.dump(history, fh, indent=1)
    log('reclaim: deleted raw/%s (%.1f GiB); its findings stay in processed/'
        % (name, freed / (1 << 30)))
    return entry


def report(cap_gb=None):
    """What the store holds, and which runs could be reclaimed today.

    The state anyone needs before launching a long arm: how full the cache is,
    and which directories are bulk that is already mirrored. Printed rather
    than returned because it is a thing a person reads.
    """
    size = raw_size_bytes()
    print('results store: raw %.1f GiB%s' % (
        size / (1 << 30),
        '' if cap_gb is None else ' of %g GiB cap (%.1f%%)' % (
            float(cap_gb), 100.0 * size / (float(cap_gb) * (1 << 30)))))
    rows = []
    for name in sorted(os.listdir(RAW) if os.path.isdir(RAW) else []):
        d = raw_dir(name)
        if not os.path.isdir(d):
            continue
        rows.append((_dir_bytes(d), name,
                     os.path.exists(os.path.join(d, '_run.json')),
                     _findings_in_processed(name), _is_running(d)))
    rows.sort(reverse=True)
    print('%10s  %-52s %-8s %-9s %s'
          % ('GiB', 'run', 'record', 'findings', 'reclaimable now'))
    for b, name, rec, found, running in rows[:20]:
        print('%10.1f  %-52s %-8s %-9s %s'
              % (b / (1 << 30), name[:52], 'yes' if rec else 'NO',
                 'yes' if found else 'NO',
                 'RUNNING' if running else ('yes' if found else 'no')))
    if len(rows) > 20:
        print('... and %d more' % (len(rows) - 20))
    return rows


def main(argv=None):
    import argparse  # noqa: PLC0415
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--report', action='store_true',
                    help='what the store holds and what could be reclaimed')
    ap.add_argument('--reclaim', action='append', default=[], metavar='RUN',
                    help='reclaim one run\'s bulk; repeatable. Refused unless '
                         'its findings are already in processed/')
    a = ap.parse_args(argv)
    cap = None
    try:
        sys.path.insert(0, os.path.join(REPO, 'src'))
        import registry as _registry  # noqa: PLC0415
        cap = _registry.load(strict=True).get('RUN.storage.raw_cap_gb')
    except Exception:
        pass
    for name in a.reclaim:
        reclaim(name)
    if a.report or not a.reclaim:
        report(cap)
    return 0


if __name__ == '__main__':
    sys.exit(main())
