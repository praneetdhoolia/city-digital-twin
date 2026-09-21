#!/usr/bin/env python
"""Deterministic population subsample, with the transit fleet scaled to match.

Three properties matter and none is free.

**Whole households.** The sampling UNIT is the household, not the person
(`RUN.sample.unit`, DECISIONS.md 9.45). It was the person until then, and the
cost was invisible because nothing in the model was household-coupled: a sample
drawn per person keeps each member independently, so a household of size n
retains on average f*n of its members and the chance a given person keeps ANY
co-member is 1-(1-f)^(n-1) - about 0.14 at f=0.10 and 0.32 at f=0.25 here. Every
household mechanism was therefore being decided by the sampler, and decided
DIFFERENTLY at each fraction, which is the one thing a sample fraction must not
do. Measured on the two completed pilot arms: the share of `ride` legs whose
household drives at all was 32.6% at 10% and 43.1% at 25%. The price, stated
rather than hidden, is that a household-clustered sample carries more variance
at a given size than a person-wise one.

**Nested.** A unit is kept if a hash of its id falls below the fraction, so the
1% sample is a strict subset of the 10% sample. Three fractions are then three
views of one population rather than three independent draws, and a difference
between them is a sample-size effect rather than a sampling one. Hashing the
HOUSEHOLD id nests exactly as hashing the person id did.

**Fleet scaled with it.** MATSim enforces seated and standing capacity at
boarding. Both components scale by the population fraction. Each nonzero
component retains the declared `RUN.sample.transit_capacity_floor`; a component
that was zero stays zero. Integer rounding and this floor still require
validation when a service carries few sampled passengers.

Nothing here reads a validation target, let alone a holdout one.
"""
import argparse
import gzip
import hashlib
import math
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET


def _lxml():
    """lxml is the sampler's dependency, not the harness's: a launch needs it,
    importing run_matsim (and every unit test that does) must not."""
    from lxml import etree
    return etree

from det_io import gzip_writer
import registry

# The registry is read ON FIRST USE, not at import (#126). This module is
# imported by run_matsim.py, which run.py imports unconditionally, so a
# module-level `registry.load()` here made `run.py --stop` and `--list` need
# a fully valid registry: while anyone was mid-edit of a layer file the one
# sanctioned way to stop a running arm was unavailable. run_matsim.py passes
# every value explicitly; these defaults serve a standalone invocation only.
_CFG = None


def _cfg():
    global _CFG
    if _CFG is None:
        _CFG = registry.load()
    return _CFG


def default_seed():
    """RUN.machine.seed - NOT a literal here. It resolves from the registry,
    so there is one copy of it and changing it is a declared change - two
    copies of a number is the drift this package cannot absorb
    (DECISIONS.md 15)."""
    return _cfg().get('RUN.machine.seed')


def capacity_floor():
    """RUN.sample.transit_capacity_floor. It was a literal `1` here while the
    registry declared the field and swept it 1-4, so the sweep moved a number
    the code never read - a declared parameter reaching nothing, the issue 21
    defect class (issue 12)."""
    return _cfg().get('RUN.sample.transit_capacity_floor')


def sample_unit():
    """RUN.sample.unit - declared, not typed in. `person` retains the
    person inclusion rule from before DECISIONS.md 9.45. XML serialisation
    is structural and need not reproduce an older file's whitespace."""
    return _cfg().get('RUN.sample.unit')


CAPACITY_FLOOR_DOC = None
# DECISIONS.md 9.60: a lift binding couples TWO households. Sampled
# independently, the pair survives intact with probability fraction^2 - the
# 9.45 defect class again, with the coupling one level up - so households
# joined by a binding are unioned into one sampling cluster hashed on a
# canonical representative: the pair is kept or dropped TOGETHER, each
# household's inclusion probability stays exactly the fraction, and the
# stated price is the same as 9.45's (a clustered sample carries more
# variance at fixed size).
# DECISIONS.md 9.127: the shared-ride drivers' households, a subset of
# liftHousehold that the binder bound under the sampler's own unit-hash rule
# and that must therefore NOT be unioned into clusters.


def population_elements(src):
    """Stream the root declaration and complete top-level XML elements.

    Memory holds one person, not the population. No DTD or external entity is
    fetched. Internal entity declarations are refused rather than losing their
    definitions when the population is serialised.
    """
    XML = _lxml()
    with gzip.open(src, 'rb') as stream:
        context = XML.iterparse(stream, events=('start', 'end'), load_dtd=False,
                                no_network=True, resolve_entities=False)
        _, root = next(context)
        if XML.QName(root).localname != 'population':
            raise ValueError('plans root must be population')
        info = root.getroottree().docinfo
        if info.internalDTD is not None and info.internalDTD.entities():
            raise ValueError('population entity declarations are unsupported')
        yield 'root', (root.tag, dict(root.attrib), dict(root.nsmap), info.doctype)
        for event, element in context:
            if event == 'end' and element.getparent() is root:
                yield XML.QName(element).localname, element
                element.clear()
                while element.getprevious() is not None:
                    del root[0]


def sampling_attributes(person):
    """Read person attributes independently of layout and declaration order."""
    attributes = {}
    for element in person.findall('./{*}attributes/{*}attribute'):
        name = element.get('name')
        if name not in ('householdId', 'liftHousehold', 'sharedDriverHousehold'):
            continue
        if name in attributes:
            raise ValueError('duplicate sampling attribute: ' + name)
        if len(element):
            raise ValueError('sampling attribute must be scalar: ' + name)
        attributes[name] = element.text or ''
    hid = attributes.get('householdId')
    if hid is not None and not hid.strip():
        raise ValueError('householdId is empty; omit it for a household-less person')
    lifts = [value.strip() for value in attributes.get('liftHousehold', '').split(',') if value.strip()]
    shared = {value.strip() for value in attributes.get('sharedDriverHousehold', '').split(',') if value.strip()}
    return hid, lifts, shared


def validate_sampling(fraction, unit):
    if isinstance(fraction, bool) or not math.isfinite(fraction) or not 0 < fraction <= 1:
        raise ValueError('population sample fraction must be finite and in (0, 1]')
    if unit not in ('person', 'household'):
        raise ValueError('population sample unit must be person or household')


def keep(person_id, fraction, seed=None, household_id=None, unit=None):
    """Uniform in [0,1) from the sampling unit's id, so the sample nests.

    The unit is the household where the agent has one and `RUN.sample.unit`
    says so, and the person otherwise - which covers the external and through
    boundary tiers, household-less by construction. The person key is
    UNCHANGED from before 9.45, so `unit = person` reproduces the old sample
    exactly; the household key is namespaced so a household id and a person id
    that happen to be the same integer are still two independent draws.
    """
    unit = sample_unit() if unit is None else unit
    validate_sampling(fraction, unit)
    if seed is None:
        seed = default_seed()
    if unit == 'household' and household_id is not None:
        key = 'household|%s|%d' % (household_id, seed)
    else:
        key = '%s|%d' % (person_id, seed)
    h = hashlib.blake2b(key.encode(), digest_size=8)
    return int.from_bytes(h.digest(), 'big') / 2 ** 64 < fraction


def lift_cluster_map(src):
    """Household -> canonical representative, over the lift couplings (9.60).

    Union-find over (householdId, liftHousehold) pairs read from the plans
    themselves, so the sampler can never disagree with what the population
    actually carries. Empty when no binding exists, which restores the 9.45
    inclusion decisions. Since 9.127 the shared-ride drivers' households
    are excluded from the unions: a directed closure over them was measured
    to pull the 10% sample to 17.65% of persons, and a union to make it half
    of what it should be; the binder's unit-hash rule needs neither.
    """
    parent = {}

    def find(x):
        while parent.get(x, x) != x:
            parent[x] = parent.get(parent[x], parent[x])
            x = parent[x]
        return x

    # 9.127: a person's liftHousehold now also carries the households of the
    # SHARED-RIDE drivers (9.124). Those are NOT unioned: the binder bound
    # them under the unit-hash rule, so a shared driver is kept whenever its
    # passenger is, and unioning them makes the sampling unit a giant
    # component (the first F18 arm kept 31,262 persons at 10% against
    # 62,134). The plans name them in `sharedDriverHousehold`; the person's
    # block is read whole so the exclusion is known before the unions.
    for kind, element in population_elements(src):
        if kind != 'person':
            continue
        hid, lifts, shared = sampling_attributes(element)
        if hid is not None:
            for lift_hh in lifts:
                if lift_hh in shared:
                    continue
                a, b = find(hid), find(lift_hh)
                if a != b:
                    lo, hi = sorted((a, b), key=lambda v: (len(v), v))
                    parent[hi] = lo
    return {h: find(h) for h in list(parent)}


def subsample_plans(src, dst, fraction, seed=None, unit=None, kept_ids=None):
    """Write the sampled plans; `kept_ids`, when a set is passed, receives
    every person id written, so the launcher can record the run's own
    residents beside its inputs (#213)."""
    n_in = n_out = n_no_household = 0
    if seed is None:
        seed = default_seed()
    if unit is None:
        unit = sample_unit()
    validate_sampling(fraction, unit)
    if Path(src).resolve() == Path(dst).resolve():
        raise ValueError('sample output must not replace its source population')
    # 9.60 clusters over the lift couplings; 9.127: the shared-ride drivers
    # are excluded from them (see lift_cluster_map) because the binder keeps
    # them by the unit-hash rule, so the clusters stay small
    cluster = lift_cluster_map(src) if unit == 'household' else {}
    seen, retained = set(), set() if kept_ids is not None else None
    # A malformed late person must not replace an existing valid run input.
    with tempfile.TemporaryDirectory(prefix='sample-population-', dir=Path(dst).parent) as temporary:
        staged = Path(temporary, 'plans.xml.gz')
        elements = population_elements(src)
        XML = _lxml()
        try:
            _, (tag, attributes, namespaces, doctype) = next(elements)
            with gzip_writer(staged, text=False) as stream, XML.xmlfile(stream, encoding='utf-8') as writer:
                writer.write_declaration()
                if doctype:
                    writer.write_doctype(doctype)
                with writer.element(tag, attributes, nsmap=namespaces):
                    for kind, element in elements:
                        if kind != 'person':
                            writer.write(element)
                            continue
                        pid = element.get('id')
                        if not pid or pid in seen:
                            raise ValueError('missing or duplicate person id: ' + str(pid))
                        seen.add(pid)
                        n_in += 1
                        hid, _, _ = sampling_attributes(element)
                        if hid is None:
                            n_no_household += 1
                        if keep(pid, fraction, seed, cluster.get(hid, hid), unit):
                            writer.write(element)
                            n_out += 1
                            if retained is not None:
                                retained.add(pid)
        finally:
            elements.close()
        os.replace(staged, dst)
    if kept_ids is not None:
        kept_ids.update(retained)
    return n_in, n_out, n_no_household


def scale_transit_capacity(src, dst, fraction, floor=None, scale_pce=False):
    """Scale seated and standing places in MATSim v1 and v2 vehicle XML.

    Parse the XML structure: a regex consuming the start of a capacity tag
    matched only its first attribute and left standing places at full size.
    Return each component's old and new value for the launch audit.

    With `scale_pce` (RUN.sample.transit_pce_scaling, 9.206) every vehicle
    type's passenger-car equivalent is multiplied by the fraction too: the
    vehicles run at full frequency on links whose flow capacity is scaled,
    and at their full PCE a bus took a hundred times its real share of a
    1 % lane. No floor - the PCE is a real number, and a bus at 0.028 on a
    lane of 18 an hour is the bus at 2.8 on a lane of 1,800.
    """
    if not math.isfinite(fraction) or not 0 < fraction <= 1:
        raise ValueError('transit sample fraction must be finite and in (0, 1]')
    if floor is None:
        floor = capacity_floor()
    if isinstance(floor, bool) or not isinstance(floor, int) or floor < 1:
        raise ValueError('transit capacity floor must be a positive integer')
    with gzip.open(src, 'rb') as f:
        tree = ET.parse(f)
    scaled = []

    def shrink(element, attribute, component):
        before = int(element.attrib[attribute])
        if before < 0:
            raise ValueError('negative transit capacity: %s' % component)
        after = max(floor, int(round(before * fraction))) if before else 0
        scaled.append((component, before, after))
        element.set(attribute, str(after))

    for capacity in tree.getroot().iter():
        if capacity.tag.rsplit('}', 1)[-1] != 'capacity':
            continue
        found = set()
        for component in ('seats', 'standingRoomInPersons'):
            if component in capacity.attrib:
                shrink(capacity, component, component)
                found.add(component)
        for child in capacity:
            component = child.tag.rsplit('}', 1)[-1]
            if component not in ('seats', 'standingRoom'):
                continue
            name = 'standingRoomInPersons' if component == 'standingRoom' else component
            if name in found:
                raise ValueError('duplicate transit capacity component: %s' % name)
            shrink(child, 'persons', name)
            found.add(name)
        if not found:
            raise ValueError('transit capacity has no recognised passenger components')
    if scale_pce:
        for element in tree.getroot().iter():
            if element.tag.rsplit('}', 1)[-1] != 'passengerCarEquivalents':
                continue
            before = float(element.attrib['pce'])
            if not math.isfinite(before) or before < 0:
                raise ValueError('transit vehicle PCE must be a finite non-negative number')
            after = before * fraction
            scaled.append(('pce', before, after))
            element.set('pce', '%g' % after)
    with gzip_writer(dst, text=False) as w:
        tree.write(w, encoding='utf-8', xml_declaration=True)
    return scaled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--plans', required=True)
    ap.add_argument('--vehicles')
    ap.add_argument('--out-plans', required=True)
    ap.add_argument('--out-vehicles')
    ap.add_argument('--fraction', type=float, required=True)
    ap.add_argument('--seed', type=int, default=None,
                    help='default RUN.machine.seed from the registry')
    a = ap.parse_args()
    n_in, n_out, n_hhless = subsample_plans(a.plans, a.out_plans, a.fraction,
                                            a.seed)
    print('plans: %d of %d persons kept (%.4f), unit %s, %d household-less'
          % (n_out, n_in, n_out / max(n_in, 1), sample_unit(), n_hhless))
    if a.vehicles and a.out_vehicles:
        sc = scale_transit_capacity(a.vehicles, a.out_vehicles, a.fraction)
        print('transit capacity scaled on %d vehicle types: %s'
              % (len(sc), sorted(set(sc))))


if __name__ == '__main__':
    main()
