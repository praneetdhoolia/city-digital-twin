"""Two defects that a passing test suite could not see, pinned so they cannot
return in the shape they arrived in.

1. **The HTS purpose map existed twice and the two copies disagreed** (#147).
   The demand builder sent `Serve passenger` to `HX` - its own tour purpose
   since 9.15 - and the run-input assembler sent it to `NHB`, so an escort
   trip was GENERATED as an escort and PRICED as a non-home-based leg. `HX`
   carries 351,645 weekday legs; this was not a rare cell. There is one map
   now, and the test that matters is that there is still only one.

2. **A seeded draw was made in hash order** (#150).
   `EscortCoherenceListener` consumes a seeded RNG while iterating its
   household map. In a `HashMap` the draw sequence is assigned in hash order
   of the key set - and the key set is exactly what changes when the sample
   fraction changes. Seeded, and therefore looking deterministic, while not
   being stable across fractions: a 1 % probe could not predict a 25 % arm on
   this path. Determinism is a hard constraint, so the collection must be
   ordered by a stable key (DECISIONS.md 9.151).
"""
import os
import re

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..'))
LISTENER = os.path.join(REPO, 'src', 'java', 'citysim',
                        'EscortCoherenceListener.java')


def _read(*parts):
    with open(os.path.join(REPO, *parts), encoding='utf-8') as fh:
        return fh.read()


def test_the_purpose_map_is_declared_exactly_once():
    """No second copy of the mapping, anywhere under src/."""
    holders = []
    for root, _dirs, names in os.walk(os.path.join(REPO, 'src')):
        if '__pycache__' in root:
            continue
        for name in names:
            if not name.endswith('.py'):
                continue
            path = os.path.join(root, name)
            with open(path, encoding='utf-8', errors='replace') as fh:
                text = fh.read()
            # A COPY is a literal mapping of the HTS purpose to a model
            # purpose - `'Serve passenger': 'HX'`. A mention in prose is not.
            if re.search(r"""['"]Serve passenger['"]\s*:\s*['"]\w+['"]""", text):
                holders.append(os.path.relpath(path, REPO).replace(os.sep, '/'))
    assert holders == ['src/build/hts_purpose.py'], holders


def test_both_callers_read_that_one_map():
    for module in ('src/build/build_activity_chains.py',
                   'src/build/build_matsim_run_inputs.py'):
        assert 'hts_purpose' in _read(*module.split('/')), module


def test_serve_passenger_is_an_escort_not_a_non_home_based_leg():
    import sys
    import hts_purpose
    assert hts_purpose.HTS_PURPOSE['Serve passenger'] == 'HX'
    assert 'NHB' not in hts_purpose.HTS_PURPOSE.values()


@pytest.mark.skipif(not os.path.exists(LISTENER), reason='listener absent')
def test_the_seeded_draw_iterates_an_ordered_collection():
    """`byHousehold` is drawn from while a seeded RNG advances, so its
    iteration order is part of the model's determinism, not an implementation
    detail. It must be ordered by the household id."""
    text = _read('src', 'java', 'citysim', 'EscortCoherenceListener.java')
    decl = re.search(r'byHousehold\s*=\s*new\s+(\w+)<>\(\)', text)
    assert decl, 'byHousehold is not declared the way this test expects'
    assert decl.group(1) in ('TreeMap', 'LinkedHashMap'), decl.group(1)
