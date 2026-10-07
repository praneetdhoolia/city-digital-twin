#!/usr/bin/env python
"""Refuse a credential in a tracked or staged file.

    python tests/check_secrets.py            # every tracked file (the gate)
    python tests/check_secrets.py --staged   # what the next commit would publish (pre-commit)

A tracing API key sat uncommitted in the tracked `.claude/settings.json` on 25
September 2026 (the fourteenth report); nothing would have stopped the next
handoff commit from publishing it. Keys belong in the gitignored `.env` or
`.claude/settings.local.json`, which the code reads by NAME
(`TFNSW_API_KEY`, `OGD_API_KEY`) - so a key-shaped VALUE in a tracked file is
always a leak, never a reference.

The patterns are the published formats of the providers this project touches
or could, plus two shapes of the project's own keys: the TfNSW Open Data key
is a JWT (three base64url segments joined by dots, the first `eyJ`), and a key
pasted into a request URL rides a query string (`apikey=...`) with no quotes
for the assignment pattern to see. A generic `key = "<long token>"` assignment
closes the rest. Rendered reports under docs/reports/ are HTML and are scanned
like everything else: a key in a page is published twice over. A match prints
the file, the line and the provider - never the value.
"""
import argparse
import re
import subprocess
import sys

PATTERNS = (
    ('LangSmith', re.compile(r'lsv2_(?:pt|sk)_[0-9a-f]{32}_[0-9a-f]{10}')),
    ('Anthropic', re.compile(r'sk-ant-[A-Za-z0-9_\-]{20,}')),
    ('OpenAI', re.compile(r'sk-(?:proj-)?[A-Za-z0-9]{32,}')),
    ('GitHub', re.compile(r'(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}')),
    ('AWS', re.compile(r'AKIA[0-9A-Z]{16}')),
    # a JSON Web Token: `{"alg"` or `{"typ"` base64url-encoded begins `eyJ`,
    # and three dot-joined segments of that alphabet is the whole shape
    ('JWT (TfNSW Open Data key)', re.compile(
        r'eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}')),
    # a key riding a query string, unquoted: `?apikey=...`, `&api_key=...`,
    # `&key=...`; 20+ characters so a short lookup key (`key=aadt`) is not one
    ('query-string key', re.compile(
        r'(?i)(?:^|[?&\s"\'])(?:apikey|api[_-]?key|key)=[A-Za-z0-9_\-]{20,}')),
    ('assigned key', re.compile(
        r'''(?i)["']?[a-z_]*(?:api[_-]?key|secret|token)["']?\s*[:=]\s*["'][A-Za-z0-9_\-]{24,}["']''')),
)
# Binary and bulk files are not scanned: a hash or a GTFS id is not a key.
SKIP = re.compile(r'\.(?:gz|zip|pdf|png|jpg|jpeg|parquet|xlsx|pbf|jar|class)$|MANIFEST\.csv$')


def files(staged):
    cmd = (['git', 'diff', '--cached', '--name-only', '--diff-filter=ACM'] if staged
           else ['git', 'ls-files'])
    out = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return [f for f in out.stdout.splitlines() if f and not SKIP.search(f)]


def text(path, staged):
    if staged:
        out = subprocess.run(['git', 'show', ':%s' % path], capture_output=True)
        data = out.stdout
    else:
        try:
            with open(path, 'rb') as fh:
                data = fh.read()
        except OSError:
            return ''
    return data.decode('utf-8', 'replace')


def scan(staged):
    hits = []
    for path in files(staged):
        for n, line in enumerate(text(path, staged).splitlines(), 1):
            for provider, pat in PATTERNS:
                if pat.search(line):
                    hits.append((path, n, provider))
    return hits


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--staged', action='store_true',
                    help='scan what the next commit would publish')
    a = ap.parse_args()
    hits = scan(a.staged)
    for path, n, provider in hits:
        print('%s:%d: a %s credential - move it to .env or .claude/settings.local.json'
              % (path, n, provider))
    print('TOTAL %d credential(s) in %s files.'
          % (len(hits), 'staged' if a.staged else 'tracked'))
    return 1 if hits else 0


if __name__ == '__main__':
    sys.exit(main())
