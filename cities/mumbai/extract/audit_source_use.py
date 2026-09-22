"""Which acquired source is read by what: the package's data-use ledger.

The user's standing goal (21 September 2026) is that nothing acquired is left
unused and nothing unnecessary is kept. The catalogue says what was acquired
and the manifest says what was produced; neither says whether a raw file is
READ. This walks the readers - every `OUTPUT_INPUTS` glob in the city's and
the framework's scripts, every script that names a source id, every
transcription and published observation that cites one, every registry field
whose provenance names one, and the requirements ledger - and gives each
catalogue entry one disposition:

- `consumed`: a script, a transcription or a registry field reads it;
- `discovery`: an index, search, landing, bundle, specification, licence or
  readme page whose purpose was to find or license a data file (the
  provenance of a discovery, kept, never a data input);
- `audited`: only an `audit_*` or `register_*` script reads it - its bytes
  and shape are checked, nothing of its content reaches a model artefact;
- `cited`: a document the requirements ledger cites as evidence, with no
  script, transcription or registry field reading it - a human read it;
- `unread`: a data-bearing acquisition nothing reads - the ledger's work;
- `not_needed`: acquired and judged, in the catalogue entry's own `use`
  block, to bear on none of the twelve modes' simulation (a road-safety
  report, a future line's project report, an earlier epoch of a layer the
  package reads at a later one) - kept as provenance, read by nothing, and
  the reason stated;
- `reference`: a document a person read and whose facts stand in the
  requirements ledger or a registry rationale, declared so in `use`;
- `unusable` and `unobtained`: the inventory's own statuses.

A `discovery` page is recognised by its id or title, never by hand: the
words are listed here so a new page is classified the same way.
"""
import ast
import csv
import fnmatch
import json
import re
from collections import Counter
from pathlib import Path

import city

OUTPUT_INPUTS = {
    'data/processed/acquisition/source_use.json': [
        'extract/sources.json',
        'data/processed/acquisition/source_inventory.json',
        'data/MANIFEST.csv',
        'extract/*.py', 'build/*.py', 'registry/*.json', 'docs/requirements.json',
        'extract/transcriptions/*.json', 'extract/published_observations.json',
        'extract/fare_transcriptions.json', 'extract/jvlr_poster_transcription.json',
        'extract/metro3_fare_chart_layout.json',
    ],
}

# scripts whose mention of a source id is bookkeeping, not reading
BOOKKEEPING = {'acquire_sources.py', 'inventory_sources.py', 'audit_source_use.py',
               'import_browser_acquisition.py', 'harvest.py'}
# the fewest fixed characters a glob needs before it names one family of raw
# files rather than every file (`*.json` matches everything): string matching
# structure, not a modelling value
GLOB_FIXED_CHARS_MIN = 6
# a page that exists to find, describe or license data, by the words in its id
DISCOVERY_WORDS = ('index', 'search', 'catalogue', 'catalog', 'home', 'root', 'bundle',
                   'config', 'component', 'readme', 'licence', 'license', 'spec', 'filters',
                   'indicators', '_ids', 'metadata', 'menu', 'downloads', 'materials',
                   'portal', 'page', 'client', 'documentation', 'directory', 'product',
                   'landing', 'attributes', 'access', 'service_types', 'public_app', 'item')


def string_literals(path):
    """Every string literal in a Python file, read without running it."""
    try:
        tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError):
        return []
    return [node.value for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)]


def output_input_globs(path):
    """The raw-side globs a script declares in OUTPUT_INPUTS, read statically."""
    try:
        tree = ast.parse(Path(path).read_text(encoding='utf-8'))
    except (SyntaxError, UnicodeDecodeError):
        return []
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == 'OUTPUT_INPUTS' for t in node.targets):
            try:
                mapping = ast.literal_eval(node.value)
            except ValueError:
                return []
            return [g for inputs in mapping.values() for g in inputs]
    return []


def literal_reads(literal, raw_path):
    """Whether a string literal names this raw file: its path, its basename,
    or a glob whose fixed part is long enough to mean one family of files
    (`*` and `*.json` name everything and nothing)."""
    if not literal or not raw_path:
        return False
    base = raw_path.rsplit('/', 1)[-1]
    tail = literal.rsplit('/', 1)[-1]
    if any(c in literal for c in '*?['):
        fixed = re.sub(r'[*?\[\]]+', '', tail)
        if len(fixed) < GLOB_FIXED_CHARS_MIN:
            return False
        return fnmatch.fnmatch(raw_path, literal) or fnmatch.fnmatch(base, tail)
    return literal == raw_path or literal == base


def main():
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))['sources']
    inventory_doc = json.loads(Path(city.path('data/processed/acquisition/source_inventory.json')).read_text(encoding='utf-8'))
    inventory = inventory_doc['sources']
    if isinstance(inventory, list):
        inventory = {row['id']: row for row in inventory}
    requirements = json.loads(Path(city.path('docs/requirements.json')).read_text(encoding='utf-8'))
    cited_by = {}
    for requirement in requirements['requirements']:
        for source_id in requirement.get('source_ids', []):
            cited_by.setdefault(source_id, []).append(requirement['id'])

    scripts = sorted(list(Path(city.path('extract')).glob('*.py')) + list(Path(city.path('build')).glob('*.py'))
                     + list(Path(city.REPO, 'src').rglob('*.py')))
    globs, mentions = {}, {}
    for script in scripts:
        rel = script.relative_to(city.REPO).as_posix()
        if script.name in BOOKKEEPING:
            continue
        for pattern in output_input_globs(script):
            if (pattern.startswith('data/raw/')
                    and len(re.sub(r'[*?\[\]]+', '', pattern.rsplit('/', 1)[-1])) >= GLOB_FIXED_CHARS_MIN):
                globs.setdefault(pattern, []).append(rel)
        for literal in string_literals(script):
            mentions.setdefault(literal, set()).add(rel)

    transcriptions = {}
    for path in [*Path(city.path('extract/transcriptions')).glob('*.json'),
                 Path(city.path('extract/published_observations.json')),
                 Path(city.path('extract/fare_transcriptions.json')),
                 Path(city.path('extract/jvlr_poster_transcription.json')),
                 Path(city.path('extract/metro3_fare_chart_layout.json'))]:
        if path.exists():
            transcriptions[path.relative_to(city.REPO).as_posix()] = path.read_text(encoding='utf-8')
    registry = {p.relative_to(city.REPO).as_posix(): p.read_text(encoding='utf-8')
                for p in Path(city.path('registry')).glob('*.json')}

    ledger, counts = [], Counter()
    for entry in catalogue:
        source_id = entry['id']
        row = inventory.get(source_id, {})
        status = row.get('status', 'unobtained')
        readers = {'scripts': set(), 'transcriptions': [], 'registry': []}
        raw_path = row.get('path')
        if raw_path:
            for pattern, owners in globs.items():
                if fnmatch.fnmatch(raw_path, pattern) or fnmatch.fnmatch(raw_path, pattern.replace('**/', '')):
                    readers['scripts'].update(owners)
        for literal, owners in mentions.items():
            if source_id == literal or literal_reads(literal, raw_path):
                readers['scripts'].update(owners)
        pattern = re.compile(r'\b%s\b' % re.escape(source_id))
        readers['transcriptions'] = sorted(p for p, text in transcriptions.items() if pattern.search(text))
        readers['registry'] = sorted(p for p, text in registry.items() if pattern.search(text))
        readers['scripts'] = sorted(readers['scripts'])

        declared = entry.get('use') or {}
        if status == 'unobtained':
            disposition = 'unobtained'
        elif status == 'acquired_unusable':
            disposition = 'unusable'
        elif declared.get('disposition') in ('not_needed', 'reference') and declared.get('reason'):
            disposition = declared['disposition']
        elif readers['transcriptions'] or readers['registry'] or any(
                not Path(s).name.startswith(('audit_', 'register_')) for s in readers['scripts']):
            disposition = 'consumed'
        elif readers['scripts']:
            disposition = 'audited'
        elif entry.get('kind') == 'harvest':
            disposition = 'unread'
        elif any(word in source_id for word in DISCOVERY_WORDS) or entry.get('format') in ('js', 'yaml', 'py', 'md', 'txt'):
            disposition = 'discovery'
        elif source_id in cited_by:
            disposition = 'cited'
        else:
            disposition = 'unread'
        counts[disposition] += 1
        ledger.append({
            'id': source_id, 'category': entry.get('category'), 'format': entry.get('format'),
            'status': status, 'disposition': disposition, 'path': raw_path,
            'readers': readers, 'cited_by': cited_by.get(source_id, []),
            'declared_use': declared.get('reason'),
            'discovered_from': entry.get('discovered_from'),
            'archived_copy_of': entry.get('archived_copy_of'),
        })
    # identical bytes at two URLs are one observation (inventory_sources.py):
    # a twin of a consumed source is consumed
    by_id = {r['id']: r for r in ledger}
    for group in inventory_doc.get('identical_bytes_groups') or []:
        ids = group if isinstance(group, list) else group.get('ids', [])
        if any(by_id.get(i, {}).get('disposition') == 'consumed' for i in ids):
            for i in ids:
                if by_id.get(i, {}).get('disposition') in ('unread', 'cited', 'audited'):
                    counts[by_id[i]['disposition']] -= 1
                    by_id[i]['disposition'] = 'consumed'
                    by_id[i]['readers']['identical_bytes_twin'] = [j for j in ids if j != i]
                    counts['consumed'] += 1
    # a discovery page that led to nothing acquired is a dead end, not evidence
    children = Counter(e.get('discovered_from') for e in catalogue if e.get('discovered_from'))
    for row in ledger:
        row['discovered'] = children.get(row['id'], 0)

    out = {
        'schema_version': 1,
        'purpose': __doc__.strip().splitlines()[0],
        'counts': dict(sorted(counts.items())),
        'by_category': {
            category: dict(Counter(r['disposition'] for r in ledger if r['category'] == category))
            for category in sorted(set(r['category'] for r in ledger))},
        'sources': ledger,
    }
    target = Path(city.path('data/processed/acquisition/source_use.json'))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('data-use ledger:', ' '.join('%s %d' % kv for kv in sorted(counts.items())))
    for row in ledger:
        if row['disposition'] in ('unread', 'cited', 'audited'):
            print('  %-8s %-12s %-6s %s' % (row['disposition'], row['category'], row['format'], row['id']))


if __name__ == '__main__':
    main()
