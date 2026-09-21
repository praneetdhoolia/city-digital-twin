"""Declare the framework's run-side fields for Mumbai, from the reference city.

Until 21 September 2026 the Mumbai baseline declared its run settings under a
private `RUN.smoke.*` / `C.smoke.*` namespace, fifty-nine of them bound to the
same MATSim parameters as a framework field the reference city declares - a
second vocabulary for one config document. This script writes the framework's
keys into `registry/RUN_framework.json` and its companions (decision 9.202):

  * a Mumbai field whose tool binding a framework field already owns is MOVED
    under the framework key - Mumbai's value, source, sweep and description
    survive; the contract's units and `matsim_format` are taken;
  * a run-side field Mumbai never declared is ADOPTED from the reference
    city's declaration, its description saying so, its source downgraded to
    `assumed` where the reference city's was a measurement of Newcastle, and
    its status `placeholder` where the mechanism it parameterises is switched
    off for this baseline (the gate values are in GATES);
  * a handful are Mumbai's own facts (the seed, the sample unit, the crossings)
    and are written from OVERRIDES.

Run once per contract change; idempotent. Reads the reference city's registry
directly (it is the contract's `generated_from`), never the framework code.

A field already in a `*_framework.json` is kept as it stands (a moved twin
carries Mumbai's own value and must not be re-adopted from the reference), and
the file is rewritten as the union of what it held and what a contract change
adds: until 21 September 2026 (9.204) a contract change would have rewritten
each file with the new keys alone. An entry in OVERRIDES or GATES is re-applied
to a kept field, so a Mumbai fact stated here reaches the file on every run.
"""
import json
import os
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(REPO / 'src')]
import city                                                     # noqa: E402
import registry                                                 # noqa: E402

CONTRACT = json.loads((REPO / 'config/schema/required_fields.json').read_text(encoding='utf-8'))
REFERENCE = REPO / 'cities' / CONTRACT['generated_from'].split('/')[1] / 'registry'
DECISION = '9.202'
# Where each layer's adopted fields land in this city's registry.
TARGET = {'RUN': 'RUN_framework.json', 'CAL': 'CAL_framework.json',
          'A': 'A_framework.json', 'B': 'B_framework.json', 'C': 'C_framework.json'}
# The framework builders whose fields this city's package went through
# (the manifest's `produced_by`, suffix stripped) - what check_city reads.
# Mechanisms switched off for this baseline: the gate value, and why.
GATES = {
    'A.signals.representation': ('implicit_delay', 'no signal inventory is modelled; the corridor-signal effect stays implicit'),
    'A.gradient.representation': ('absent', 'no elevation is attached to the mapped network yet'),
    'A.crossings.representation': ('absent', 'no boom-gated freight crossing is represented'),
    'A.bike_stress.representation': ('absent', 'no motor-traffic stress classes are attached to the mapped network yet'),
    'C.raptor.mode_cost_representation': ('absent', 'the transit router carries no per-mode constant in the baseline'),
    'B.ride.pairing_enabled': (False, 'the baseline population carries no households, so no ride can name its driver'),
    'B.population.vehicle_roster': ('per_person', 'the baseline population carries no households; car access is a person attribute'),
}
# Fields the gates above silence, by key prefix: declared, adopted, inert.
GATED_BY = {
    'A.signals.': 'A.signals.representation', 'A.gradient.': 'A.gradient.representation',
    'A.crossings.': 'A.crossings.representation', 'A.bike_stress.': 'A.bike_stress.representation',
    'B.ride.': 'B.ride.pairing_enabled', 'B.taxi.': 'A.taxi.fleet_representation',
    'CAL.': None,
}
# Mumbai's own facts, where adopting the reference city's value would be wrong.
OVERRIDES = {
    'B.seed.master': dict(value=None, source='definition', status='active',
                          description='The one seed everything synthetic derives from; city.json declares it.'),
    'RUN.sample.fraction': dict(value=1.0, source='assumed', status='active',
                                sweep={'interval': [0.001, 1.0], 'basis': 'the synthesised core population is 27.06 M persons (9.204) and the plans are written at B.population.plans_build_fraction (9.205); a fraction below one has no measured fidelity for this city (docs/scaling.md), and the floor admits the first citywide case the machine can run'},
                                sweep_role='uncertainty',
                                description='Share of the population simulated. 1.0 for the explicit 1,000-person development case; a citywide case runs the plans built at B.population.plans_build_fraction at a fraction at or below it, declared on its overlay.'),
    'RUN.sample.unit': dict(value='household', source='derived', status='active', decisions_ref='9.205',
                            derived_from={'fields': ['B.seed.master'], 'identity': 'the citywide plans carry householdId (build_plans.py writes the households the nested hash keeps), so the sampler keeps whole households, as the reference city does'},
                            description='Whether the population subsample keeps whole households or independent persons. `household` since the citywide plans (9.205); the explicit 1,000-person development population had none.'),
    'A.crossings.freight_closures_per_day': dict(value={}, source='derived', status='active',
                                                 derived_from={'fields': ['A.crossings.representation'], 'identity': 'no boom-gated crossing is represented (A.crossings.representation = absent), so the closure table is empty'},
                                                 description='Non-timetabled freight movements a day at each boom-gated crossing. Empty: none is represented in this baseline.'),
    'CAL.asc.mode_to_constant': dict(value={}, source='definition', status='active',
                                     description='Which declared alternative-specific constant carries which board mode. Empty: the baseline scores one constant for every mode (C.scoring.mode_constant) and no ASC loop runs for this city.'),
    'C.asc.car_passenger': dict(value=0.0, source='assumed', status='placeholder',
                                sweep={'interval': [-2.0, 2.0], 'basis': 'the baseline has one constant for every mode; a passenger-specific constant is not solved for this city'},
                                sweep_role='uncertainty',
                                description='Car-passenger constant. Placeholder at zero: the baseline scores one constant for every mode and no ASC round has run for this city.'),
    'B.population.age_bands': dict(value=[[0, 4], [5, 9], [10, 14], [15, 19], [20, 24], [25, 29], [30, 34], [35, 39], [40, 44],
                                          [45, 49], [50, 54], [55, 59], [60, 64], [65, 69], [70, 74], [75, 79], [80, 120]],
                                   source='definition', status='active',
                                   description='Age banding for population synthesis: the five-year bands of the Census of India 2011 C-14 table the package holds (data/processed/observed/census_2011_age_sex.csv), 80+ open.'),
    'A.parking.charged_hours_by_day_type': dict(decisions_ref='9.204', value={'WEEKDAY': None}, source='definition', status='active',
                                                description='The charged parking window per day type. None for the one day type: no parking price is observed for this city, the assembled price table beside the scenario network is empty (every link free), and a free day is written as a window of (0, 0) exactly as the reference city writes its Sunday.'),
    'A.parking.charged_start_hour': dict(decisions_ref='9.204', value=None, source='derived', status='computed',
                                         derived_from={'fields': ['A.parking.charged_hours_by_day_type'], 'identity': 'A.parking.charged_hours_by_day_type[day][0], 0 for a day with no window; the harness supplies it under the derived runtime role'},
                                         description='Hour at which parking begins to be charged, derived at launch from the day type\'s window as in the reference city.'),
    'A.parking.charged_end_hour': dict(decisions_ref='9.204', value=None, source='derived', status='computed',
                                       derived_from={'fields': ['A.parking.charged_hours_by_day_type'], 'identity': 'A.parking.charged_hours_by_day_type[day][1], 0 for a day with no window; the harness supplies it under the derived runtime role'},
                                       description='Hour at which parking stops being charged, derived at launch from the day type\'s window as in the reference city.'),
    'C.scoring.activity_minimal_duration_s': dict(decisions_ref='9.204', value=0, source='definition', status='active',
                                                  description='The minimal duration an activity must reach before it scores, in seconds. 0 for this city: the baseline applies no minimal duration, which is what MATSim\'s own undefined default means, written as a zero floor so the harness\'s min(minimal, typical) identity holds for every activity type.'),
    'C.scoring.activity_minimal_applied_s': dict(decisions_ref='9.204', value=None, source='derived', status='computed',
                                                 derived_from={'fields': ['C.scoring.activity_minimal_duration_s', 'C.scoring.activity_typical_duration_s'], 'identity': 'min(C.scoring.activity_minimal_duration_s, typical duration) per activity type; the harness supplies it under the derived runtime role'},
                                                 description='The minimal activity duration written per activity type, derived at launch as in the reference city; 0 s for every type while C.scoring.activity_minimal_duration_s is 0.'),
    'RUN.scoring.translation': dict(decisions_ref='9.204', value='bound_fields', source='definition', status='active',
                                    description='Where this city\'s MATSim scoring parameters come from. `bound_fields`: this city has no C1 nested-logit table; every scoring parameter is a bound registry field (C.scoring.mode_constant, C.scoring.marginal_utility_of_traveling, C.scoring.waiting_pt, C.scoring.utility_of_line_switch, the crowding and service-quality prices) and the harness translates nothing (9.204).'),
    'RUN.transit_router.access_egress_basis': dict(decisions_ref='9.204', value='beeline', source='assumed', status='active',
                                                   sweep={'categorical': ['beeline', 'network'], 'basis': 'beeline reproduces the pre-fold cases exactly (the raptor draws access and egress straight); network routes them on the walk network, which GOAL.md requirement 1 asks for and which is switched on once the walk network\'s reach to the boarding links is measured for this city'},
                                                   sweep_role='uncertainty',
                                                   description='How a pt trip reaches its first stop and leaves its last. `beeline` for the fold: the previous cases\' behaviour, to be switched to `network` by a declared change of its own.'),
    'RUN.gate.interval_iterations': dict(decisions_ref='9.204', value=0, source='definition', status='active',
                                         description='How often the gate watcher reads the modes against their targets. 0 for this city: no target exists to judge a mode by, so the only automatic stop is the wall ceiling every run overlay declares (RUN.gate.wall_ceiling_h).'),
    'RUN.replanning.max_agent_plan_memory': dict(decisions_ref='9.206', value=5, source='literature', status='active',
                                                 sweep=[3, 10], sweep_role='uncertainty',
                                                 description='Plans an agent keeps: MATSim\'s own default, the leanest choice set the reference city\'s sweep admits with room to innovate. The citywide plans carry ONE initial plan a person (build_plans.py; the assembly refuses a memory below the supplied count), so the 9 the retired explicit 1,000-person case needed for its eight seeded alternatives (9.204) bought nothing but heap: the reference city\'s 25 % arm lives at about 19 KB a plan (20-28.6 GiB after a full collection for 155,000 agents at 8 plans over a 5 GiB floor), so at 9 plans 1 % of the 27.06 M core needs 51 GiB against 63 GB and at 5 plans 32 GiB (9.206, D14). Inside the declared 3-10 sweep; the choice-set width it costs is what the equivalence experiments of docs/scaling.md measure.'),
    'RUN.machine.heap_floor_gib': dict(decisions_ref='9.206', value=7.4, source='measured', status='active',
                                       held_fixed={'rule': 'the LIVE SET after the last full collection of a case with no population to speak of, read from its gc.log (Pause Full N->M: M), never the pre-collection peak - under ParallelGC with -Xms = -Xmx the peak tracks the heap GIVEN (16g peaked at 13.74, 24g at 17.30), not the heap needed; re-read from every longer case', 'decisions_ref': '9.206', 'departure_requires': 'a higher live set after a full collection at a negligible population in a later Mumbai gc.log'},
                                       description='The sample-independent part of the heap rule. MEASURED as the live set after the last full collection: 7.36 GiB in the gc.log of 20260921T182708_2it_100pct (the explicit 1,000-person case: the mapped regional network, the combined feed and the routers) and 7.81 GiB in 20260921T220701_2it_0.1pct with 26,884 agents at one or two plans - 18 KB an agent, the reference city\'s per-plan rate. 9.205 read 13.74 from the pre-collection peak of a 16g heap, which is the heap size, not the need (9.206).'),
    'RUN.machine.heap_per_fraction_gib': dict(decisions_ref='9.206', value=2400.0, source='measured', status='active',
                                              held_fixed={'rule': 'persons in the core (27.06 M) x RUN.replanning.max_agent_plan_memory x the live heap a routed plan holds at steady state - 19 KB on the reference city\'s 25 % arm 20260916T063903_250it_25pct (20-28.6 GiB after a full collection for 155,000 agents at 8 plans over a 5 GiB floor), the same Java stack; 27.06 M x 5 x 19 KB = 2,400 GiB per unit fraction; re-read from the 1 % case\'s own live set once its plan memory has filled', 'decisions_ref': '9.206', 'departure_requires': 'a live set after a full collection at another fraction, or a per-plan rate read from a Mumbai gc.log whose plan memory has filled'},
                                              description='The sample-dependent part of the heap rule, per unit of RUN.sample.fraction of the 27.06 M-person core, at plan memory 5: 2,400 GiB - so 1 % of the core (270,000 agents) needs 31.4 GiB with the floor, 2 % 55 GiB (the last this 63 GB host holds) and 5 % (1.35 M agents) 127 GiB. The 3,600 of 9.205 was the slope between two PRE-collection peaks of differently sized heaps (9.206). The fraction a defensible reading needs is the open question of docs/scaling.md; the memory is no longer the first constraint below 2 %, the flow identity is.'),
    'RUN.qsim.mode_vehicle_fields': dict(decisions_ref='9.204', value={
                                             mode: dict(length_m_field='A.vehicle.%s.length_m' % mode, width_m_field='A.vehicle.%s.width_m' % mode,
                                                        pce_field='A.vehicle.%s.pce' % mode, seats_field='A.vehicle.%s.seats' % mode,
                                                        standing_field='A.vehicle.%s.standing' % mode, maximum_speed_ms_field='A.vehicle.%s.max_speed_ms' % mode)
                                             for mode in ('car', 'ride', 'walk', 'bike', 'motorbike', 'taxi', 'auto_rickshaw', 'truck', 'freight_rail')},
                                         source='definition', status='active',
                                         description='Explicit network-mode vehicle definitions: one profile per routed mode, each naming the A.vehicle.<mode>.* scalar fields (registry/A_vehicles.json) for its length, width, PCE, seats, standing room and speed cap. Replaces the per-launch vehicle writer of the city\'s own launcher (9.204).'),
    'RUN.replanning.score_msa_fraction': dict(value=None, source='derived', status='computed',
                                              derived_from={'fields': ['RUN.replanning.score_msa_representation'], 'identity': 'the literal MATSim writes for its own default when the representation is absent; the launcher supplies it under the derived runtime role'},
                                              description='The iteration fraction at which a plan score becomes a moving average. Derived at launch from the representation gate, as in the reference city.'),
    'RUN.machine.xmx': dict(value='16g', source='definition', status='active',
                            description='JVM heap for the baseline case (-Xms = -Xmx). 16g served the 1,000-person population; the heap rule fields carry the reference city\'s measurement until a Mumbai peak is measured.'),
    'RUN.machine.threads': dict(value=2, source='definition', status='active',
                                description='qsim threads for the baseline case; the explicit population is small enough that two threads keep the machine free.'),
    'RUN.machine.replanning_threads': dict(value=2, source='definition', status='active',
                                           description='Replanning threads for the baseline case.'),
}
# Fields moved from Mumbai's private namespace: framework key -> Mumbai key,
# resolved by the shared tool binding at run time (see move_bound_twins).
CONVERT = {
    # a clock string in the private namespace, hours in the contract
    'RUN.qsim.start_time_h': lambda v: int(str(v).split(':')[0]),
    'RUN.qsim.end_time_h': lambda v: int(str(v).split(':')[0]),
}
# Derived by the launcher from the sample fraction, as in the reference city.
LAUNCH_DERIVED = {'RUN.sample.flow_capacity_factor', 'RUN.sample.storage_capacity_factor'}
# Bound in the reference city, declared unbound here: the baseline's behaviour
# is MATSim's own default, which is what emitting nothing gives.
DROP_BINDING = {'C.scoring.activity_minimal_applied_s'}
# Gate fields the launch-derived values read; adopted whether or not the
# contract lists them as run-side (they are read by the framework builder).
ALSO_ADOPT = {'RUN.replanning.score_msa_representation'}
DECLARED = set()   # every key this city will hold after the run: filled by main()
KEEP = ('units', 'source', 'sweep', 'sweep_basis', 'sweep_role', 'sweep_keys', 'status',
        'held_fixed', 'derived_from', 'matsim_param', 'matsim_format', 'baseline_ref',
        'pt2matsim_osm_param', 'pt2matsim_mapper_param', 'inert_at', 'inert_reason')


def contract_units(key):
    """The contract's unit string with this city's own currency and base year."""
    desc = city.descriptor()
    units = CONTRACT['fields'][key]['units']
    if isinstance(units, str):
        units = units.replace('{currency}', desc.get('currency', '')).replace('{base_year}', str(desc['base_year']))
    return units


def held(rule, requires):
    """A held_fixed rule in the schema's shape."""
    return {'rule': rule, 'decisions_ref': DECISION, 'departure_requires': requires}


def framework_consumers(field):
    return [c for c in field.get('consumers') or [] if c.startswith(('src/', 'run.py', 'tests/'))]


def first_sentence(text):
    text = (text or '').strip()
    cut = text.find('. ')
    return text if cut < 0 else text[:cut + 1]


def adopt(key, ref):
    """The reference city's declaration re-labelled as an adoption."""
    out = {k: ref[k] for k in KEEP if k in ref}
    out['units'] = contract_units(key)
    out['value'] = ref.get('value')
    gate = next((g for p, g in GATED_BY.items() if key.startswith(p)), None)
    inert = gate is not None and gate in GATES and key != gate
    if ref.get('source') in ('measured', 'observed'):
        out['source'] = 'assumed'
        sweep = ref.get('sweep')
        if isinstance(sweep, dict):
            out['sweep'] = dict(sweep)
            out['sweep'].setdefault('basis', 'the reference city\'s measured value, adopted unmeasured for this city')
            out['sweep_role'] = ref.get('sweep_role') or 'uncertainty'
        else:
            out['sweep'] = None
            out.pop('sweep_role', None)
            out['held_fixed'] = held('the reference city\'s measurement, adopted; no Mumbai measurement exists and the field is not varied',
                                     'a Mumbai measurement of the same quantity')
    if out.get('source') == 'assumed' and isinstance(out.get('sweep'), dict) and 'basis' in out['sweep']:
        out['sweep'] = dict(out['sweep'], basis='adopted from the reference city: ' + out['sweep']['basis'])
    if out.get('source') == 'assumed' and not out.get('sweep') and not out.get('held_fixed'):
        out['held_fixed'] = 'the reference city\'s value, adopted; not varied for this city'
    if out.get('sweep') and not out.get('sweep_role'):
        out['sweep_role'] = 'uncertainty'
    if isinstance(out.get('derived_from'), dict):
        names = out['derived_from'].get('fields') or []
        if any(n not in DECLARED for n in names):
            out.pop('derived_from')
            out['source'] = 'assumed'
            out['sweep'] = None
            out.pop('sweep_role', None)
            out['held_fixed'] = held('adopted from the reference city, where it is derived from %s; those fields are '
                                     'not declared for this city, so the value is held' % ', '.join(names),
                                     'declaring %s for this city' % ', '.join(names))
    if ref.get('status') == 'computed' and out.get('source') == 'derived':
        out['status'] = 'computed'
    elif inert:
        out['status'] = 'placeholder'
    else:
        out['status'] = 'active' if ref.get('status') != 'unobtained' else 'unobtained'
    lead = first_sentence(ref.get('description'))
    if key in GATES:
        value, why = GATES[key]
        out['value'] = value
        out['status'] = 'active'
        out['description'] = '%s Switched off for this baseline (%s): %s.' % (lead, json.dumps(value), why)
    elif inert:
        gv = GATES[gate][0]
        out['description'] = ('%s Adopted from the reference city and INERT here: %s = %s switches the mechanism off '
                              'for this baseline, so the value reaches the config and nothing acts on it.'
                              % (lead, gate, json.dumps(gv)))
    else:
        out['description'] = '%s Adopted from the reference city\'s declaration; not a Mumbai observation.' % lead
    out['decisions_ref'] = DECISION
    consumers = framework_consumers(ref)
    if consumers:
        out['consumers'] = consumers
    return out


def override(key, ref):
    out = adopt(key, ref)
    spec = OVERRIDES[key]
    for k in ('sweep', 'sweep_role', 'held_fixed', 'derived_from', 'sweep_basis'):
        out.pop(k, None)
    out.update(spec)
    out['units'] = contract_units(key)
    if 'decisions_ref' in spec:
        out['decisions_ref'] = spec['decisions_ref']
    if key == 'B.seed.master':
        out['value'] = city.descriptor()['seed']
    if key in DROP_BINDING:
        for k in ('matsim_param', 'matsim_format'):
            out.pop(k, None)
    return out


def move_bound_twins(mine, reference):
    """Mumbai fields bound to a parameter a framework field owns -> framework key."""
    by_binding = {v['matsim_param']: k for k, v in reference.items() if v.get('matsim_param')}
    moved = {}
    for key, field in mine.items():
        target = by_binding.get(field.get('matsim_param'))
        if target is None or target == key or target in mine:
            continue
        ref = reference[target]
        out = dict(field)
        out['units'] = contract_units(target)
        if ref.get('matsim_format'):
            out['matsim_format'] = ref['matsim_format']
        if target in CONVERT:
            out['value'] = CONVERT[target](field['value'])
        if target in OVERRIDES:
            spec = OVERRIDES[target]
            for k in ('sweep', 'sweep_role', 'held_fixed', 'derived_from', 'sweep_basis'):
                out.pop(k, None)
            out.update(spec)
        if target in LAUNCH_DERIVED:
            # the launcher derives it (the capacity factors from the fraction)
            out = {k: ref[k] for k in KEEP if k in ref}
            out['units'] = contract_units(target)
            out['value'] = None
            out['description'] = first_sentence(ref.get('description')) + ' Derived at launch, as in the reference city.'
        out['decisions_ref'] = DECISION
        out.setdefault('description', '')
        out['description'] = (out['description'].rstrip() + ' Moved from %s on 21 September 2026: one key per MATSim parameter.' % key).strip()
        for k in ('legacy_symbol', 'consumers'):
            out.pop(k, None)
        moved[target] = (key, out)
    return moved


def main():
    reference, _ = registry.load_registry(str(REFERENCE))
    mine, origin = registry.load_registry(city.path('registry'))
    twins = move_bound_twins(mine, reference)
    required = CONTRACT['fields']
    producers = {'src/build/build_matsim_network.py', 'src/build/build_manifest.py'}
    applicable = {key for key, spec in required.items()
                  if spec.get('required_by', 'run') == 'run'
                  or (isinstance(spec.get('required_by'), list) and any(b in producers for b in spec['required_by']))}
    DECLARED.update(k for k in mine if k not in {s for s, _ in twins.values()})
    DECLARED.update(twins)
    applicable |= ALSO_ADOPT
    DECLARED.update(applicable)
    written = {}
    for target, (source_key, field) in twins.items():
        written[target] = field
    # what the framework files already hold: kept, an OVERRIDES or GATES entry re-applied
    held = {}
    for key, path in origin.items():
        if os.path.basename(path) in TARGET.values():
            field = dict(mine[key])
            if key in OVERRIDES:
                field = override(key, reference[key]) if key in reference else dict(field, **OVERRIDES[key])
            elif key in GATES:
                field = adopt(key, reference[key])
            held[key] = field
    for key in sorted(applicable | set(OVERRIDES)):
        if key in written or key in held or (key in mine and key not in held):
            continue
        if key not in reference:
            # a Mumbai fact with no reference declaration: written from OVERRIDES alone
            spec = dict(OVERRIDES[key])
            spec.setdefault('units', CONTRACT['fields'][key]['units'] if key in CONTRACT['fields'] else 'see description')
            spec['decisions_ref'] = spec.get('decisions_ref', DECISION)
            written[key] = spec
            continue
        ref = reference[key]
        written[key] = override(key, ref) if key in OVERRIDES else adopt(key, ref)
    # write per layer as the union of the kept and the new; remove the moved
    # private fields from their files
    files = {}
    for key, field in list(held.items()) + list(written.items()):
        files.setdefault(TARGET[key.split('.')[0]], {})[key] = field
    for name, fields in files.items():
        path = Path(city.path('registry', name))
        doc = {'layer': name.split('_')[0],
               'title': 'Framework run-side fields: moved from the private baseline namespace or adopted from the reference city (9.202)',
               'fields': dict(sorted(fields.items()))}
        # LF explicitly: write_text writes CRLF on Windows (9.201, trap 7)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        print('wrote', name, len(fields), 'kept', sum(1 for k in fields if k in held), 'new', sum(1 for k in fields if k in written))
    retired = {}
    for target, (source_key, _) in twins.items():
        retired.setdefault(origin[source_key], []).append(source_key)
    for path, keys in retired.items():
        doc = json.loads(Path(path).read_text(encoding='utf-8'))
        for k in keys:
            doc['fields'].pop(k, None)
        Path(path).write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n', encoding='utf-8', newline='\n')
        print('retired', len(keys), 'private keys from', os.path.basename(path))
    print(json.dumps({k: v for k, v in sorted((t, s) for t, (s, _) in twins.items())}, indent=1))


if __name__ == '__main__':
    main()
