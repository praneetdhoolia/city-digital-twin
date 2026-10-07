#!/usr/bin/env python
"""A city's recorded debt against a framework rule, under a ceiling that only falls.

Two gates refuse a hole unless the city has recorded it: tests/check_manifest.py
(manifest rows that fail a provenance rule) and src/registry/check_hardcoding.py
(values decided in a city's own scripts). A second city brought hundreds of
each on the day it was built, and a gate that is red for a month teaches people
to skim past it - so the framework states the rules and each city states, in
`cities/<city>/tests/<ledger>.json`, the exact items that fail each rule today.
The two ledgers share one shape and one set of rules about the shape, written
once here so the manifest ledger and the hardcoding ledger cannot drift apart:

    {"description": "...",
     "rules": {"<rule>": {"ceiling": N,
                          "<items>": ["...", ...],          # paths or keys
                          "reason": "what the rule catches and when it was measured",
                          "ceiling_log": [{"date": "YYYY-MM-DD", "ceiling": N,
                                           "reason": "...", "raised": true}]}}}

The rules about the shape, which `check_ceilings` enforces:

  - the ceiling equals the number of listed items, so an item added without
    the ceiling raised fails and an item fixed without the ceiling lowered
    fails - the list, not the number, is the debt;
  - the newest `ceiling_log` entry states the current ceiling, and every entry
    carries a date and a reason;
  - against origin/main (when the ref is in the checkout) the ceiling of a
    rule the base ledger carries may only FALL. A rise is refused unless the
    newest log entry carries `"raised": true` beside its reason: an explicit,
    dated, reasoned raise, never one that a new log line happened to
    accompany (sixteenth report). A rule origin/main does not carry is being
    measured for the first time, and its first entry is the measurement.

`check_recorded` then judges the items: a failing item outside the list is a
new hole and fails; a listed item that no longer fails must be deleted, so the
list can only shrink. A city with no ledger carries no debt and every hole fails.
"""
import json
import os
import subprocess

import city as _city


def ledger_path(parts, city_dir=None):
    """The ledger file beside the city's other test expectations."""
    return os.path.join(city_dir or _city.CITY_DIR, *parts)


def load(parts, city_dir=None, path=None):
    """{rule: {ceiling, items, ceiling_log, ...}} for one city ({} if none)."""
    path = path or ledger_path(parts, city_dir)
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8') as f:
        return json.load(f).get('rules') or {}


def base(parts, city_dir=None):
    """The same ledger on origin/main, or None where that ref is not here (a
    shallow CI checkout). Read from the LOCAL ref; nothing is fetched."""
    city_dir = city_dir or _city.CITY_DIR
    rel = os.path.relpath(os.path.join(city_dir, *parts), _city.REPO).replace(os.sep, '/')
    try:
        p = subprocess.run(['git', 'show', 'origin/main:' + rel], cwd=_city.REPO,
                           capture_output=True, text=True, encoding='utf-8')
    except OSError:
        return None
    if p.returncode != 0:
        ok = subprocess.run(['git', 'rev-parse', '--verify', '-q', 'origin/main'],
                            cwd=_city.REPO, capture_output=True, text=True).returncode == 0
        return {} if ok else None      # the ref is here but the file is new: no base
    return (json.loads(p.stdout).get('rules') or {})


def check_ceilings(ledger, base_ledger, rules, items_key='paths'):
    """The count beside each list, and the rule that it may only fall.

    - a rule's `ceiling` equals the number of listed items: an item added
      without raising the ceiling fails, and an item removed without lowering
      it fails;
    - the ceiling equals the newest `ceiling_log` entry, and every entry
      carries a date and a reason - so a raise cannot be made silently;
    - against origin/main (when the ref is here), a ceiling that ROSE is
      refused unless the newest `ceiling_log` entry is new in this change and
      carries `"raised": true` beside its reason.
    """
    out = []
    for rule, entry in sorted(ledger.items()):
        if rule not in rules:
            out.append('debt names an unknown rule %r (known: %s)'
                       % (rule, ', '.join(rules)))
            continue
        items = entry.get(items_key) or []
        ceiling = entry.get('ceiling')
        log = entry.get('ceiling_log') or []
        if not isinstance(ceiling, int):
            out.append('%s: the debt carries no integer ceiling' % rule)
            continue
        if len(set(items)) != len(items):
            out.append('%s: the debt lists an item twice' % rule)
        if len(items) > ceiling:
            out.append('%s: %d item(s) listed above the ceiling of %d - a new '
                       'entry needs the ceiling raised in the same change, '
                       'with a dated ceiling_log entry carrying "raised": true '
                       'and the reason' % (rule, len(items), ceiling))
        elif len(items) < ceiling:
            out.append('%s: %d item(s) listed under a ceiling of %d - the debt '
                       'shrank; lower the ceiling to %d and log it'
                       % (rule, len(items), ceiling, len(items)))
        if not log or log[-1].get('ceiling') != ceiling:
            out.append('%s: the newest ceiling_log entry must state the '
                       'current ceiling (%d)' % (rule, ceiling))
        for item in log:
            if not str(item.get('date') or '').strip() or not str(item.get('reason') or '').strip():
                out.append('%s: every ceiling_log entry carries a date and a '
                           'reason' % rule)
                break
        # A rule origin/main carries may only fall. A rule it does not carry
        # is being measured for the first time: its first entry is the
        # measurement, not a raise (a rule removed and re-added with a
        # higher ceiling would have to do it across two changes, in review).
        if base_ledger is not None and rule in base_ledger:
            was = base_ledger[rule] or {}
            was_ceiling = was.get('ceiling', 0)
            if ceiling > was_ceiling:
                new_entry = log and len(log) > len(was.get('ceiling_log') or [])
                if not new_entry or log[-1].get('raised') is not True:
                    out.append('%s: the ceiling rose from %d (origin/main) to %d; '
                               'a ceiling may only fall unless the newest '
                               'ceiling_log entry is new in this change and '
                               'carries "raised": true with the reason'
                               % (rule, was_ceiling, ceiling))
    return out


def check_recorded(judged, debt, where):
    """Refuse each hole, except the items recorded as debt - which may only SHRINK.

    `judged` is a list of (rule, failing items, what they are, seen): `seen`
    is None when every listed item can be judged, else the set of items this
    checkout can judge (a listed drift path absent from a CI checkout is not
    judged either way). `debt` maps a rule to the items recorded as its debt;
    `where` names the ledger file in the message. Returns (failures,
    {rule: (failing, recorded)}).
    """
    failures, counts = [], {}
    for rule, failing, what, seen in judged:
        failing = set(failing)
        allowed = set(debt.get(rule, ()))
        new = sorted(failing - allowed)
        fixed = sorted(p for p in allowed - failing if seen is None or p in seen)
        counts[rule] = (len(failing), len(allowed))
        if new:
            failures.append('%d %s outside the recorded debt: %s%s'
                            % (len(new), what, ', '.join(new[:6]),
                               ' ...' if len(new) > 6 else ''))
        if fixed:
            failures.append('%d item(s) in the recorded %s debt no longer fail '
                            'it - delete them from %s and lower its ceiling: '
                            '%s%s'
                            % (len(fixed), rule, where, ', '.join(fixed[:6]),
                               ' ...' if len(fixed) > 6 else ''))
    return failures, counts
