#!/usr/bin/env python
"""Why a run died, read from the run's own log rather than remembered.

    python src/run/run_failure.py results/aborted_<name>      # what killed it
    python src/run/run_failure.py --backfill                  # fill in the gaps

`_meta.json` recorded THAT a run died - `status: failed`, `rc: 1` - and never
WHY. The cause survived only in whoever was watching, and three 25 August probe
failures reached the next session as run records that could not explain
themselves; their causes existed, but only as narrative in `DECISIONS.md`. A
directory nobody can interpret is a directory nobody can rule out, and the
handover convention (DECISIONS.md 9.66) already says every aborted run carries a
cause-stating record.

**The cause is MEASURED, never composed.** It is the terminating exception MATSim
itself printed, with its `Caused by` chain, quoted from `matsim.log` and carrying
the line it was read from. Nothing here interprets, guesses or attributes: a run
whose log says nothing gets a cause that says the log said nothing.

One definition, two consumers - the harness writes a cause at the moment of
death, and the backfill fills in records written before the harness did.
"""
import io
import os
import re
import sys
import json
import glob
import argparse

# `Exception in thread "main" pkg.Cls: message` - the JVM's own last word. The
# thread is captured because a run can also die on a mobsim worker.
# The separator is `:` for a normal message and `;` for the ones that carry
# their own structured detail (SAXParseException prints `Cls; lineNumber: 11`).
# Requiring a colon dropped exactly the root cause of the crossings-XML failure.
TERMINAL = re.compile(r'^Exception in thread "([^"]+)" '
                      r'([\w.$]+(?:Exception|Error|Throwable))(?:[:;]\s*(.*))?$')
CAUSED_BY = re.compile(r'^Caused by:\s+([\w.$]+(?:Exception|Error|Throwable))'
                       r'(?:[:;]\s*(.*))?$')
LOG_ERROR = re.compile(r'\b(?:ERROR|SEVERE|FATAL)\b\s+(.*)$')
MESSAGE_CHARS = 400
META = '_meta.json'
LOG = 'matsim.log'


def _short(fqcn):
    """`java.lang.RuntimeException` -> `RuntimeException`."""
    return fqcn.rsplit('.', 1)[-1]


def _clip(text):
    text = ' '.join((text or '').split())
    return text if len(text) <= MESSAGE_CHARS else text[:MESSAGE_CHARS] + '...'


def from_log(log_path):
    """The terminating exception and its chain, or None if the log has none.

    The LAST terminal exception wins. A MATSim run logs earlier, survivable
    throwables - the bytecode library's `Unsupported class file major version`
    is in every one of these logs and killed none of them - so the first match
    would name a non-cause with total confidence.
    """
    if not os.path.exists(log_path):
        return None
    with io.open(log_path, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().splitlines()

    start = None
    for i, line in enumerate(lines):
        if TERMINAL.match(line.strip()):
            start = i
    if start is None:
        return None

    m = TERMINAL.match(lines[start].strip())
    chain = []
    for line in lines[start + 1:]:
        c = CAUSED_BY.match(line.strip())
        if c:
            chain.append({'exception': c.group(1), 'message': _clip(c.group(2))})
    root = chain[-1] if chain else {'exception': m.group(2),
                                    'message': _clip(m.group(3))}
    return {
        'cause': '%s: %s' % (_short(root['exception']),
                             root['message'] or '(no message)'),
        'thread': m.group(1),
        'exception': m.group(2),
        'message': _clip(m.group(3)),
        'caused_by': chain,
        'log_line': start + 1,
        'read_from': LOG,
    }


def _last_error(log_path):
    """The last logged ERROR line, for a JVM that died without unwinding."""
    if not os.path.exists(log_path):
        return None
    with io.open(log_path, encoding='utf-8', errors='replace') as fh:
        lines = fh.read().splitlines()
    for i in range(len(lines) - 1, -1, -1):
        m = LOG_ERROR.search(lines[i])
        if m:
            return {'cause': _clip(m.group(1)), 'log_line': i + 1,
                    'read_from': LOG}
    return None


def diagnose(run_dir, status, rc=None):
    """A cause record for a dead run, always. Never None, never invented.

    The three fallbacks are facts about the evidence, not attributions: a
    non-zero return code with no exception in the log is exactly that, and
    saying so is more useful than a plausible story.
    """
    log_path = os.path.join(run_dir, LOG)
    found = from_log(log_path) or _last_error(log_path)
    if found:
        return found
    if not os.path.exists(log_path):
        return {'cause': 'the JVM wrote no %s: it died before, or instead of, '
                         'starting' % LOG, 'read_from': None}
    if status == 'aborted':
        return {'cause': 'ended by the harness or its operator; %s records no '
                         'exception' % LOG, 'read_from': LOG}
    return {'cause': 'exited rc=%s with no exception in %s'
                     % ('?' if rc is None else rc, LOG), 'read_from': LOG}


def apply_to_meta(meta, run_dir, status=None, rc=None):
    """Put a cause on a status card that has none. Returns True if it changed."""
    if meta.get('cause'):
        return False
    status = status or meta.get('status')
    if status not in ('failed', 'aborted'):
        return False
    found = diagnose(run_dir, status, rc if rc is not None else meta.get('rc'))
    meta['cause'] = found.pop('cause')
    detail = {k: v for k, v in found.items() if v not in (None, [], '')}
    if detail:
        meta['cause_detail'] = detail
    return True


# ------------------------------------------------------------------- backfill

def backfill(results_dir, dry_run=False):
    """Every terminal run record missing a cause, filled from its own log."""
    changed = []
    for meta_path in sorted(glob.glob(os.path.join(results_dir, '*', META))):
        run_dir = os.path.dirname(meta_path)
        try:
            with io.open(meta_path, encoding='utf-8') as fh:
                meta = json.load(fh)
        except (OSError, ValueError):
            continue
        if not apply_to_meta(meta, run_dir):
            continue
        changed.append((os.path.basename(run_dir), meta['cause']))
        if dry_run:
            continue
        with io.open(meta_path, 'w', encoding='utf-8', newline='\n') as fh:
            json.dump(meta, fh, indent=2, ensure_ascii=False)
            fh.write('\n')
    return changed


def missing(results_dir):
    """Terminal run records that still cannot say why they died."""
    out = []
    for meta_path in sorted(glob.glob(os.path.join(results_dir, '*', META))):
        try:
            with io.open(meta_path, encoding='utf-8') as fh:
                meta = json.load(fh)
        except (OSError, ValueError):
            continue
        if meta.get('status') in ('failed', 'aborted') and not meta.get('cause'):
            out.append(os.path.basename(os.path.dirname(meta_path)))
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.abspath(os.path.join(here, '..', '..'))
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('run_dir', nargs='?', help='one run directory to diagnose')
    ap.add_argument('--backfill', action='store_true',
                    help='write a cause onto every terminal record missing one')
    ap.add_argument('--check', action='store_true',
                    help='exit 1 if any terminal record has no cause')
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--results', default=os.path.join(repo, 'results'))
    args = ap.parse_args()

    if args.run_dir:
        found = diagnose(args.run_dir, 'failed')
        print(json.dumps(found, indent=2, ensure_ascii=False))
        return 0
    if args.check:
        gaps = missing(args.results)
        for name in gaps:
            print('NO CAUSE %s' % name)
        print('%d terminal run record(s) cannot say why they died' % len(gaps))
        return 1 if gaps else 0

    changed = backfill(args.results, dry_run=args.dry_run)
    for name, cause in changed:
        print('%s%s: %s' % ('would set ' if args.dry_run else '', name, cause))
    print('%d record(s) %s' % (len(changed),
                               'would change' if args.dry_run else 'updated'))
    return 0


if __name__ == '__main__':
    sys.exit(main())
