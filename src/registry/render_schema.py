#!/usr/bin/env python
"""Generate the portable half of the input contract from the reference city.

    python src/registry/render_schema.py            regenerate
    python src/registry/render_schema.py --check    fail if stale

`config/schema/` already said what shape ANY field must be in. It did not say
WHICH fields a city must supply, or which artefacts it must produce - so a city
directory that was half-populated resolved cleanly and failed later, one
`get()` at a time, several hundred lines into a build. These two documents close
that:

    required_fields.json   every field key a city must declare, its units, its
                           value type, and whether it must carry a sweep
    layers.json            every city-relative artefact the FRAMEWORK reads,
                           and the columns the reference city's copy carries

Both are GENERATED, never hand-edited, for the reason CONFIG_REFERENCE.md is:
a hand-kept mirror of the registry drifts, and this repository has already been
bitten by exactly that - `params/C1` was a hand-kept copy of 26 registry values
that reached nothing.

**What `required` means here, stated honestly.** It means the reference city
declares the field and the framework will not run without it. It does NOT mean
every city in the world must have it: a city with no light rail has no use for
`A.lightrail.dwell_fixed_s`. Narrowing the set to what each layer of the model
genuinely needs is real work and is not done - so the contract today is *match
the reference city's field set, and justify any omission*. That is a weaker
claim than it looks, and saying so is the point.

`layers.json` is derived by a different and stronger route: it lists the
artefacts the framework's own source ASKS FOR, found by reading every
`city.path(...)` call under `src/`, rather than by listing what one city
happens to contain.
"""
import argparse
import ast
import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'src'))

import city as _city                                          # noqa: E402
sys.path.insert(0, HERE)
import registry                                               # noqa: E402

SCHEMA_DIR = os.path.join(REPO, 'config', 'schema')
FIELDS_OUT = os.path.join(SCHEMA_DIR, 'required_fields.json')
LAYERS_OUT = os.path.join(SCHEMA_DIR, 'layers.json')

# `source` values that field.schema.json obliges to carry a sweep, a held-fixed
# rule or a derived-from identity. Kept in one place so the two documents cannot
# disagree about it.
SWEPT_SOURCES = registry.SWEPT_SOURCES

TYPES = {bool: 'boolean', int: 'number', float: 'number', str: 'string',
         list: 'array', dict: 'object', type(None): 'null'}

# A tool binding may pin a field to ONE MODE - `modeParams[bike].constant`,
# `teleportedModeParameters[walk].beelineDistanceFactor`. Such a field is
# required only of a city that runs that mode, which is the narrowing this
# document's own caveat says is "not done". It is done for modes now, because
# modes are the one case that can be DERIVED rather than judged: the mode name
# is in the binding. A three-mode city was refused as incomplete for not
# declaring bike parameters it has no bike to apply them to.
TOOL_BINDINGS = ('matsim_param', 'sumo_param', 'pt2matsim_osm_param',
                 'pt2matsim_mapper_param')
_SELECTOR = re.compile(r'\[([^\]]+)\]')


def required_mode(field, modes):
    """The mode a field's binding pins it to, or None if it applies to all."""
    known = set(modes)
    for bind in TOOL_BINDINGS:
        for sel in _SELECTOR.findall(str(field.get(bind) or '')):
            if sel != '*' and sel in known:
                return sel
    return None


# --------------------------------------------------------------------------
# required_fields.json
# --------------------------------------------------------------------------
def tokenise_units(units, desc):
    """One city's currency and base year out of a portable unit string.

    The reference city's registry declares `AUD_per_hour` and
    `AUD_2026_per_hour`; baked into the contract they obliged every city to
    denominate in AUD at base year 2026 (issue #62 B5). The city's declared
    `currency` (city.json, ISO 4217) and `base_year` become `{currency}` and
    `{base_year}` tokens, which check_city.py expands with EACH CANDIDATE
    CITY'S OWN values - so a EUR/2030 registry passes its own contract with
    exactly the same strictness.
    """
    if not isinstance(units, str):
        return units
    currency = desc.get('currency')
    if currency:
        units = re.sub(r'(?<![A-Za-z])%s(?![A-Za-z])' % re.escape(currency),
                       '{currency}', units)
    units = re.sub(r'(?<!\d)%d(?!\d)' % desc['base_year'], '{base_year}', units)
    return units


def build_fields():
    fields, origin = registry.load_registry()
    desc = _city.descriptor()
    modes = desc.get('modes', [])
    out = {}
    for key in sorted(fields):
        f = fields[key]
        value = f.get('value')
        mode = required_mode(f, modes)
        out[key] = {
            'layer': key.split('.')[0],
            'units': tokenise_units(f.get('units'), desc),
            'type': TYPES.get(type(value), 'unknown'),
            'source_in_reference_city': f.get('source'),
            'sweep_required': f.get('source') in SWEPT_SOURCES,
            'unobtained_in_reference_city': f.get('status') == 'unobtained',
            'declared_in': origin[key].split('/')[-1],
        }
        if mode:
            out[key]['required_if_mode'] = mode
    by_layer = {}
    for key, spec in out.items():
        by_layer[spec['layer']] = by_layer.get(spec['layer'], 0) + 1
    return {
        'generated_by': 'src/registry/render_schema.py',
        'generated_from': 'cities/%s/registry' % _city.CITY,
        'contract': ('Every key below must be declared by any city, with the stated '
                     'units and value type. A field whose source is measured, derived, '
                     'literature or assumed MUST additionally carry a sweep, a '
                     'held_fixed rule or a derived_from identity - field.schema.json '
                     'enforces that, and check_city.py tests it. A field that carries '
                     'a sweep MUST say what the sweep is for (sweep_role: answer, '
                     'uncertainty or measurement), and an assumed field with a sweep '
                     'MUST say how the interval was chosen (sweep_basis) - the '
                     'resolver refuses either omission (#134). Unit strings carry '
                     '{currency} and {base_year} tokens where the reference city\'s '
                     'currency or base year appeared: each candidate city\'s own '
                     'city.json values expand them, so a EUR/2030 registry passes '
                     'its own contract (issue #62 B5).'),
        'no_prose': ("Field DESCRIPTIONS are deliberately absent. They are the "
                     "reference city's own wording and would put one city's prose - its "
                     "suburbs, its agencies, its datasets - inside the portable half of "
                     "the contract. What a city must supply is a key, its units and its "
                     "value type; WHY a particular city chose a particular value belongs "
                     "in that city's docs/reference/CONFIG_REFERENCE.md."),
        'caveat': ('`required` means the reference city declares it and the framework '
                   'will not run without it. A field carrying `required_if_mode` is '
                   'required ONLY of a city that runs that mode - the one narrowing '
                   'that can be DERIVED, because the mode name is in the tool binding. '
                   'The rest is not narrowed: an intervention-specific field is still '
                   'listed for a city that has no such intervention, and omitting one '
                   'must be justified rather than assumed.'),
        'n_fields': len(out),
        'n_by_layer': dict(sorted(by_layer.items())),
        'fields': out,
    }


# --------------------------------------------------------------------------
# layers.json
# --------------------------------------------------------------------------
def framework_paths():
    """Every city-relative artefact the FRAMEWORK asks for, read from its source.

    Finds `city.path('...')` / `_city.path('...')` calls under src/ and tests/.
    A path built at run time from a variable cannot be seen this way and is not
    claimed to be - the count of unresolvable calls is reported rather than
    silently dropped.
    """
    found, dynamic = {}, 0
    for root in ('src', 'tests'):
        for dirpath, dirs, names in os.walk(os.path.join(REPO, root)):
            dirs[:] = [d for d in dirs if d != '__pycache__']
            for n in sorted(names):
                if not n.endswith('.py'):
                    continue
                full = os.path.join(dirpath, n)
                rel_src = os.path.relpath(full, REPO).replace(os.sep, '/')
                try:
                    tree = ast.parse(io.open(full, encoding='utf-8').read())
                except SyntaxError:
                    continue
                for node in ast.walk(tree):
                    if not isinstance(node, ast.Call):
                        continue
                    fn = node.func
                    if not (isinstance(fn, ast.Attribute) and fn.attr == 'path'
                            and isinstance(fn.value, ast.Name)
                            and fn.value.id in ('city', '_city')):
                        continue
                    parts = []
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            parts.append(arg.value)
                        else:
                            parts = None
                            break
                    if parts is None:
                        dynamic += 1
                        continue
                    p = '/'.join(parts)
                    found.setdefault(p, set()).add(rel_src)
    return found, dynamic


def _token_sub(text, tokens, placeholder):
    """Replace any of `tokens` (whole, non-alphanumeric-bounded) in `text`."""
    if not tokens:
        return text
    pat = '|'.join(re.escape(t) for t in sorted(tokens, key=len, reverse=True))
    return re.sub(r'(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])' % pat,
                  placeholder, text)


def templated_path(rel_path, desc):
    """A scenario- or day-stamped path to its template form (issue #62 A2).

    `schedules/scenarios/S0.zip` is one city's scenario vocabulary baked into
    the portable contract; the contract row is `schedules/scenarios/
    {scenario}.zip`, instantiated by each city's own `intervention.scenarios`
    (and `{day_type}` by its `day_types`). Longest id first, bounded by
    non-alphanumerics, so `S2` cannot match inside `S2c`.
    """
    out = _token_sub(rel_path,
                     (desc.get('intervention') or {}).get('scenarios') or [],
                     '{scenario}')
    return _token_sub(out, desc.get('day_types') or [], '{day_type}')


def tokenise_columns(cols, desc):
    """One city's identifiers out of a recorded reference header (issue #62 A2).

    The zone-id column ({zone_id}), the projected-coordinate suffix
    ({coord_suffix}), the currency code ({currency}, case-insensitive) and any
    scenario id ({scenario}) become tokens a candidate city expands with its
    own city.json declarations. Not tokenised - and so still the reference
    city's naming: secondary zone levels (SA2_*), lowercase level names inside
    compound columns (home_sa1), and agency vocabulary; the caveat says so.
    """
    zone_id = (desc.get('zone_system') or {}).get('id_column')
    suffix = (desc.get('crs') or {}).get('coord_suffix')
    currency = desc.get('currency')
    scenarios = (desc.get('intervention') or {}).get('scenarios') or []
    out = []
    for c in cols:
        if zone_id and c == zone_id:
            out.append('{zone_id}')
            continue
        if suffix:
            c = re.sub(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])' % re.escape(suffix),
                       '{coord_suffix}', c)
        if currency:
            c = re.sub(r'(?<![A-Za-z0-9])%s(?![A-Za-z0-9])'
                       % re.escape(currency), '{currency}', c, flags=re.I)
        c = _token_sub(c, scenarios, '{scenario}')
        out.append(c)
    return out


def expand_template(path, desc):
    """Every concrete path a template row names for THIS city."""
    outs = [path]
    if '{scenario}' in path:
        outs = [p.replace('{scenario}', s) for p in outs
                for s in (desc.get('intervention') or {}).get('scenarios') or []]
    if '{day_type}' in path:
        outs = [p.replace('{day_type}', d) for p in outs
                for d in desc.get('day_types') or []]
    # a city with no vocabulary for a token has no path to check - report the
    # template itself (absent) rather than vacuous presence
    return outs or [path]


def columns_of(rel_path):
    """The header of the reference city's copy, if it has one and it is tabular."""
    full = _city.path(rel_path)
    if not os.path.isfile(full) or not rel_path.endswith('.csv'):
        return None
    try:
        with io.open(full, encoding='utf-8', errors='replace') as f:
            head = f.readline().strip()
    except OSError:
        return None
    if not head:
        return None
    return [c.strip().lstrip('﻿') for c in head.split(',')]


def build_layers():
    """The artefact contract. MACHINE-INDEPENDENT BY CONSTRUCTION.

    The committed document must regenerate byte-identically on any checkout,
    including one without the gitignored bulk data - CI runs `--check` on
    exactly such a checkout, and the first CI execution of this gate failed
    because the document embedded `present_in_reference_city`, an
    os.path.exists() over data CI does not have. Presence is a REPORT (printed
    by main(), never stored). `kind` and `columns_in_reference_city` are
    recorded from the reference city's own build; where the local checkout
    lacks the bytes to recompute them, the committed record is carried
    forward rather than silently degraded.
    """
    prior = {}
    if os.path.exists(LAYERS_OUT):
        try:
            prior = json.load(io.open(LAYERS_OUT, encoding='utf-8')).get(
                'artefacts', {})
        except Exception:                                  # noqa: BLE001
            prior = {}
    desc = _city.descriptor()
    found, dynamic = framework_paths()

    # Scenario- and day-stamped reads collapse to ONE template row keyed by
    # {scenario}/{day_type}: the row set is generated from the city's declared
    # vocabulary rather than enumerating one city's (issue #62 A2).
    grouped = {}
    for rel_path in sorted(found):
        key = templated_path(rel_path, desc)
        g = grouped.setdefault(key, {'read_by': set(), 'concrete': []})
        g['read_by'] |= found[rel_path]
        g['concrete'].append(rel_path)

    artefacts = {}
    for key in sorted(grouped):
        g = grouped[key]
        prev = prior.get(key, {})
        is_template = key != g['concrete'][0] or len(g['concrete']) > 1
        if any(ch in key for ch in '*?%{'):
            kind = 'pattern'
        elif os.path.exists(_city.path(key)):
            kind = 'directory' if os.path.isdir(_city.path(key)) else 'file'
        else:
            kind = prev.get('kind', 'file')
        entry = {
            'kind': kind,
            'read_by': sorted(g['read_by']),
        }
        if is_template:
            entry['instantiated_by'] = (
                'city.json intervention.scenarios / day_types: one artefact '
                'per {scenario} / {day_type} value')
        cols = None
        for rel_path in g['concrete']:
            cols = columns_of(rel_path)
            if cols:
                break
        if cols:
            entry['columns_in_reference_city'] = tokenise_columns(cols, desc)
        elif prev.get('columns_in_reference_city'):
            entry['columns_in_reference_city'] = prev['columns_in_reference_city']
        artefacts[key] = entry
    return {
        'generated_by': 'src/registry/render_schema.py',
        'generated_from': 'static reads of city.path(...) under src/ and tests/',
        'contract': ('A city must produce every artefact below, at the same '
                     'city-relative path, before the framework can run against it. '
                     'The producing script may be entirely different - that is what a '
                     'jurisdiction adapter is for - but the path and the columns the '
                     'framework reads are the contract. Paths and columns carry '
                     'tokens ({scenario}, {day_type}, {zone_id}, {coord_suffix}, '
                     '{currency}) that each city expands with its OWN city.json '
                     'declarations (intervention.scenarios, day_types, '
                     'zone_system.id_column, crs.coord_suffix, currency) - the '
                     'contract enumerates no city\'s vocabulary (issue #62 A2).'),
        'caveat': ('`columns_in_reference_city` is the header of the reference '
                   'city\'s own copy, not '
                   'a proven minimum: a column here may be incidental. Narrowing it to '
                   'the columns framework code actually reads is not done, and the '
                   'tokenisation is not complete either: secondary zone levels '
                   '(SA2_*), lowercase level names inside compound columns '
                   '(home_sa1) and agency vocabulary are still the reference '
                   'city\'s naming. Recorded '
                   'when the reference artefact is on disk and carried forward from '
                   'the committed document when it is not, so the document '
                   'regenerates identically on a checkout without the bulk data. '
                   'Whether an artefact is PRESENT locally is a report, not part of '
                   'this contract, and is never stored here.'),
        'n_artefacts': len(artefacts),
        'n_paths_built_at_runtime': dynamic,
        'artefacts': artefacts,
    }


# --------------------------------------------------------------------------
def write(path, doc, check):
    text = json.dumps(doc, indent=2, ensure_ascii=False, sort_keys=False) + '\n'
    if check:
        if not os.path.exists(path):
            print('%s is MISSING - regenerate with '
                  'python src/registry/render_schema.py' % path)
            return 1
        current = io.open(path, encoding='utf-8').read()
        if current != text:
            print('%s is stale - regenerate with '
                  'python src/registry/render_schema.py' % path)
            return 1
        print('%s is current' % os.path.basename(path))
        return 0
    with io.open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--check', action='store_true',
                    help='exit non-zero if either document has drifted')
    a = ap.parse_args()

    fields, layers = build_fields(), build_layers()
    rc = write(FIELDS_OUT, fields, a.check) | write(LAYERS_OUT, layers, a.check)
    if not a.check:
        # presence is a local report, never document content (see build_layers).
        # A template row is present when EVERY path it expands to is.
        desc = _city.descriptor()
        present = sum(
            1 for p in layers['artefacts']
            if all(os.path.exists(_city.path(x))
                   for x in expand_template(p, desc)))
        print('required_fields.json: %d fields (%s)'
              % (fields['n_fields'],
                 ', '.join('%s %d' % kv for kv in fields['n_by_layer'].items())))
        print('layers.json: %d artefacts, %d present on THIS checkout, '
              '%d path(s) built at run time and therefore not listed'
              % (layers['n_artefacts'], present,
                 layers['n_paths_built_at_runtime']))
    return rc


if __name__ == '__main__':
    sys.exit(main())
