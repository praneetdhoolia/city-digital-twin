"""Motorbike as a CHOSEN mode (DECISIONS.md 9.214, D22, #257).

The pieces that decide what the choice is offered over, on synthetic inputs:

* the Poisson at-least-one identity (src/build/possession.py) and its bound;
* the rider licence rate: summed over BOTH primary flags of the Rider class,
  learners included, over the same ERP denominator as the car rate
  (cities/<city>/build/build_licence_rates.py band_rates);
* the availability draw: deterministic under the master seed, per person for
  the licence and per HOUSEHOLD for the motorcycle, on streams of their own;
  `independent` reproduces the uncoupled draw exactly, and `riders_first`
  draws riders first (cell totals exact in expectation) and lets only a
  household with a rider hold a motorcycle, at the closed-form P(hold | rider)
  that keeps each postal area's expected possessing households observed;
* the gate: `choice` writes motorbikeAvail and a motorbike plan and never a
  motorbike lock; `carve` writes neither the attribute nor the plan;
* the running cost: the SMVU Table 6 reader finds its rows and column by
  label, and the motorbike monetaryDistanceRate = car rate x fuel ratio is
  written under `choice` only;
* the daily use (D28, B.motorbike.daily_use): `use_ratio` draws the day on a
  stream of its own at the SMVU Table 4 km-per-vehicle ratio, read by label;
  `possession` reproduces F38's availability exactly;
* a `choice` build refuses a missing observed table instead of pooling.
"""
import collections
import importlib.util
import math
import types
from pathlib import Path

import numpy as np
import pytest

import possession
import build_matsim_plans as bmp
from test_plans_writer_tiers import RESIDENT, _attr, _ctx, _persons, _rows

REPO = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    'build_licence_rates', REPO / 'cities/newcastle/build/build_licence_rates.py')
lic = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(lic)

SEED = 20260810


# -- the Poisson identity ---------------------------------------------------
@pytest.mark.parametrize('lam', [0.01, 0.1, 0.1321, 0.5, 2.0])
def test_at_least_one_is_the_poisson_complement_of_none(lam):
    assert possession.at_least_one(lam) == pytest.approx(1.0 - math.exp(-lam))
    # and the rate it implies is the rate it came from
    assert possession.rate_of_share(possession.at_least_one(lam)) == pytest.approx(lam)


def test_the_poisson_share_sits_under_one_per_household():
    for lam in (0.05, 0.3, 0.9, 1.5):
        assert possession.at_least_one(lam) < possession.one_per_household(lam) or lam == 0
    assert possession.one_per_household(1.5) == 1.0
    assert possession.at_least_one(0.0) == 0.0


def test_no_households_is_no_share_not_a_division():
    assert possession.share_owning(5, 0, 'poisson_at_least_one') is None
    assert possession.share_owning(10, 100, 'poisson_at_least_one') == \
        pytest.approx(1.0 - math.exp(-0.1))
    with pytest.raises(ValueError):
        possession.share_owning(10, 100, 'made_up')


# -- the rider rate derivation ---------------------------------------------
def test_rider_rate_is_holders_over_the_shared_denominator():
    """Two LGAs, one band; holders spread by the ERP shape and pooled."""
    bands = [(18, 24), (25, 34)]
    erp1 = {'A': {a: 100.0 for a in range(0, 100)},
            'B': {a: 50.0 for a in range(0, 100)}}
    hold = {'A': collections.Counter({'21-24': 40.0, '25-29': 50.0}),
            'B': collections.Counter({'25-29': 25.0})}
    rows, vec = lic.band_rates(hold, ['A', 'B'], erp1, bands)
    by = {(r['lga'], r['band']): r['rate'] for r in rows}
    assert by[('A', '18-24')] == pytest.approx(40.0 / 700.0, abs=1e-4)
    assert by[('A', '25-34')] == pytest.approx(50.0 / 1000.0, abs=1e-4)
    assert by[('B', '25-34')] == pytest.approx(25.0 / 500.0, abs=1e-4)
    assert vec[1] == pytest.approx(75.0 / 1500.0, abs=1e-4)


def test_rider_class_counts_both_primary_flags_and_learners():
    """The snapshot filter as main() applies it, read from its source: a Rider
    row counts whatever its primary flag and whatever its type - a NSW learner
    rider may ride unaccompanied - while the car rate still skips learners."""
    src = (REPO / 'cities/newcastle/build/build_licence_rates.py').read_text(encoding='utf-8')
    body = src[src.index('def main():'):]
    rider_at = body.index("if r['LICENCE CLASS'] == RIDER_CLASS:")
    learner_skip = body.index("if r['LICENCE TYPE'] == 'Learner':\n            continue")
    assert rider_at < learner_skip        # riders counted before learners are dropped
    assert "rider[lga][r['AGE GROUP'].strip()]" in body[rider_at:learner_skip]


# -- the availability draw --------------------------------------------------
PERSONS = [(p, 1 + p // 3, 'S%d' % (p % 4), 20 + p % 50) for p in range(1, 3001)]
HOUSEHOLDS = [(h, 'S%d' % (h % 4)) for h in range(1, 1001)]


def _draw(rider=0.3, share=0.4, seed=SEED, persons=PERSONS, households=HOUSEHOLDS):
    return bmp.draw_motorbike_availability(
        persons, households, lambda sa1, age: rider, lambda sa1: share, seed)


def test_the_draw_is_deterministic_under_the_seed():
    assert _draw() == _draw()
    assert _draw() != _draw(seed=SEED + 1)


def test_the_motorcycle_is_drawn_per_household():
    d = _draw()
    by_hh = collections.defaultdict(set)
    for pid, h, _, _ in PERSONS:
        by_hh[h].add(d[pid][1])
    assert all(len(v) == 1 for v in by_hh.values())
    held = sum(1 for v in by_hh.values() if True in v) / len(by_hh)
    assert held == pytest.approx(0.4, abs=0.05)


def test_rates_bound_the_draw():
    assert not any(r for r, _ in _draw(rider=0.0).values())
    assert all(r for r, _ in _draw(rider=1.0).values())
    assert not any(h for _, h in _draw(share=0.0).values())


def test_the_streams_are_their_own():
    """The licence draw does not move when the household list changes, and
    neither stream is the bike stream ([seed, 1])."""
    a = {p: r for p, (r, _) in _draw().items()}
    b = {p: r for p, (r, _) in _draw(households=HOUSEHOLDS[:10]).items()}
    assert a == b
    bike = np.random.default_rng([SEED, 1]).random(5)
    rider = bmp.seeded_stream(SEED, 'rider_licence').random(5)
    moto = bmp.seeded_stream(SEED, 'household_motorcycle').random(5)
    assert not np.allclose(bike, rider) and not np.allclose(rider, moto)


def test_independent_reproduces_the_uncoupled_draw_exactly():
    """`independent` is the first 9.214 draw, stream for stream."""
    rate = lambda sa1, age: 0.05 + 0.001 * (age % 40)
    share = lambda sa1: 0.1 + 0.05 * int(sa1[1:])
    got = bmp.draw_motorbike_availability(PERSONS, HOUSEHOLDS, rate, share, SEED,
                                          coupling='independent')
    u = np.random.default_rng([SEED] + list(b'rider_licence')).random(len(PERSONS))
    v = np.random.default_rng([SEED] + list(b'household_motorcycle')).random(len(HOUSEHOLDS))
    held = {h: bool(v[i] < share(s)) for i, (h, s) in enumerate(HOUSEHOLDS)}
    want = {pid: (bool(u[i] < rate(s, a)), held.get(h, False))
            for i, (pid, h, s, a) in enumerate(PERSONS)}
    assert got == want


# -- the coupled draw (B.motorbike.rider_coupling = riders_first) ------------
HH2 = [(h, 'S%d' % (h % 4)) for h in range(1, 1201)]
PERS2 = [(3 * h + k, h, s, 18 + (7 * h + 13 * k) % 70) for h, s in HH2 for k in range(3)]


def _rate(sa1, age):
    return 0.0 if age < 25 else 0.05 + 0.002 * (age - 25)


def _share(sa1):
    return 0.08 + 0.03 * int(sa1[1:])


def _group(sa1):
    return sa1


def _riders_first(seed=SEED, diag=None, persons=PERS2, households=HH2):
    return bmp.draw_motorbike_availability(persons, households, _rate, _share, seed,
                                          'riders_first', _group, diag)


def test_riders_are_the_same_draw_under_both_couplings_and_hold_the_cell_totals():
    """Riders come first, per person at the observed rate, so each cell's
    expected total is sum(rate) exactly - and the draw is the independent one."""
    a = _riders_first()
    b = bmp.draw_motorbike_availability(PERS2, HH2, _rate, _share, SEED)
    assert {p: r for p, (r, _) in a.items()} == {p: r for p, (r, _) in b.items()}
    expected = collections.Counter()
    for _, _, s, age in PERS2:
        expected[(s, age // 10)] += _rate(s, age)
    drawn = collections.Counter()
    for seed in range(60):
        d = _riders_first(seed=seed)
        for pid, _, s, age in PERS2:
            drawn[(s, age // 10)] += d[pid][0]
    assert sum(drawn.values()) / 60 == pytest.approx(sum(expected.values()), rel=0.025)
    for c, e in expected.items():
        if e > 50:
            assert drawn[c] / 60 == pytest.approx(e, rel=0.06)


def test_expected_possessing_households_equal_the_observed_share_per_group():
    rate, report, clipped = bmp.riders_first_hold_rate(PERS2, HH2, _rate, _share, _group)
    assert clipped == []
    for k, r in report.items():
        # closed form: P(hold | rider) x expected households with a rider
        assert rate[k] * r['with_rider'] == pytest.approx(r['observed'], rel=1e-12)
        assert r['observed'] == pytest.approx(_share(k) * r['households'], rel=1e-12)
    held = collections.Counter()
    for seed in range(60):
        d = _riders_first(seed=seed)
        seen = set()
        for pid, h, s, _ in PERS2:
            if h not in seen:
                seen.add(h)
                held[s] += d[pid][1]
    for k, r in report.items():
        assert held[k] / 60 == pytest.approx(r['observed'], rel=0.05)


def test_no_household_holds_a_motorcycle_without_a_rider():
    d = _riders_first()
    riders = collections.defaultdict(bool)
    for pid, h, _, _ in PERS2:
        riders[h] |= d[pid][0]
    assert all(riders[h] for pid, h, _, _ in PERS2 if d[pid][1])
    # and every member of a household sees the same motorcycle
    by_hh = collections.defaultdict(set)
    for pid, h, _, _ in PERS2:
        by_hh[h].add(d[pid][1])
    assert all(len(v) == 1 for v in by_hh.values())


def test_riders_first_is_deterministic():
    assert _riders_first() == _riders_first()
    assert _riders_first() != _riders_first(seed=SEED + 1)


def test_a_group_whose_riders_cannot_carry_its_motorcycles_is_clipped_and_reported():
    """Lone residents at a 1 % rider rate cannot carry a 50 % possession:
    P(hold | rider) clips at 1 and the lost households are stated."""
    persons = [(p, p, 'S0', 90) for p in range(1, 201)]
    households = [(p, 'S0') for p in range(1, 201)]
    rate, report, clipped = bmp.riders_first_hold_rate(
        persons, households, lambda s, a: 0.01, lambda s: 0.5, _group)
    assert clipped == ['S0'] and rate['S0'] == 1.0
    assert report['S0']['lost'] == pytest.approx(200 * 0.5 - 200 * 0.01)


def test_an_unknown_coupling_is_refused():
    with pytest.raises(ValueError):
        bmp.draw_motorbike_availability(PERS2, HH2, _rate, _share, SEED, 'made_up', _group)


def test_age_band_index_follows_the_declared_bands():
    bands = [[0, 4], [5, 11], [12, 17], [18, 24]]
    assert bmp.age_band_index(0, bands) == 0
    assert bmp.age_band_index(17, bands) == 2
    assert bmp.age_band_index(30, bands) is None


# -- the gate ---------------------------------------------------------------
@pytest.fixture
def representation(monkeypatch):
    def set_to(value, avail):
        choice = value == 'choice'
        monkeypatch.setattr(bmp, 'MOTORBIKE_CHOICE', choice)
        monkeypatch.setattr(bmp, 'SEED_METHOD', 'full_choice_set')
        chain = frozenset(bmp.CFG.get('RUN.mode_choice.chain_based_modes'))
        monkeypatch.setattr(bmp, 'CHAIN_BASED_MODES',
                            chain | frozenset([bmp.MOTORBIKE]) if choice else chain)
        monkeypatch.setattr(bmp, '_MOTO_AVAIL', dict(avail))
        monkeypatch.setattr(bmp, '_MOTORBIKE_Q', {'q': 0.0})
        monkeypatch.setattr(bmp, '_MOTORBIKE_Q_BY_PID', {})
    return set_to


def _modes_of(person):
    return {leg.get('mode') for plan in person.findall('plan')
            for leg in plan.findall('leg')}


def test_choice_offers_motorbike_to_the_available_and_never_locks(representation):
    representation('choice', {5: 1, 6: 0})
    ctx = _ctx({5: RESIDENT, 6: RESIDENT})
    bmp.write_person(5, _rows(5, 'core'), ctx)
    bmp.write_person(6, _rows(6, 'core'), ctx)
    bmp.write_person(9001, _rows(9001, 'external'), ctx)
    persons = _persons(ctx)
    assert _attr(persons[5], 'motorbikeAvail') == 'always'
    assert _attr(persons[6], 'motorbikeAvail') == 'never'
    assert _attr(persons[9001], 'motorbikeAvail') == 'never'
    assert 'motorbike' in _modes_of(persons[5])
    assert 'motorbike' not in _modes_of(persons[6])
    assert all(_attr(p, 'lockedMode') is None for p in persons.values())


def test_carve_writes_no_availability_and_no_motorbike_plan(representation):
    representation('carve', {5: 1})
    ctx = _ctx({5: RESIDENT})
    bmp.write_person(5, _rows(5, 'core'), ctx)
    p = _persons(ctx)[5]
    assert _attr(p, 'motorbikeAvail') is None
    assert 'motorbike' not in _modes_of(p)


def test_a_car_and_a_motorbike_in_one_leaf_is_repaired(representation):
    """Two tours, the second an excursion from where the first's serve stop
    left the car: under `choice` car + motorbike in one leaf is refused, the
    motorbike tours flagged; under `carve` the same plan is not examined."""
    representation('choice', {})
    rows = [dict(tour_id='1', origin_x='0', origin_y='0', dest_x='1000', dest_y='0'),
            dict(tour_id='2', origin_x='1000', origin_y='0', dest_x='0', dest_y='0')]
    assert bmp.leaf_mixed_tours(rows, {1: 'car', 2: 'motorbike'}) == {2}
    assert bmp.leaf_mixed_tours(rows, {1: 'motorbike', 2: 'motorbike'}) == set()
    representation('carve', {})
    assert bmp.leaf_mixed_tours(rows, {1: 'car', 2: 'bike'}) == set()


# -- the motorbike running cost (C.scoring.motorbike_fuel_ratio) -------------
FSPEC = importlib.util.spec_from_file_location(
    'build_vehicle_fuel_ratio', REPO / 'cities/newcastle/build/build_vehicle_fuel_ratio.py')
fuel = importlib.util.module_from_spec(FSPEC)
FSPEC.loader.exec_module(fuel)


def _table6():
    """Table 6's shape: title rows, a header row, then one block per state."""
    pd = pytest.importorskip('pandas')
    nan = float('nan')
    rows = [[nan] * 5,
            ['Table 6 Average rate of fuel consumption', nan, nan, nan, nan],
            [nan, 'Petrol', 'Petrol - RSE', fuel.COLUMN, 'Total fuel - RSE'],
            [nan, 'l/100 km', '%', 'l/100 km', '%'],
            ['State A', nan, nan, nan, nan],
            [fuel.CAR_ROW, 9.0, 1.0, 10.0, 1.0],
            [fuel.MOTORCYCLE_ROW, 5.0, 2.0, 5.5, 2.0],
            ['State B', nan, nan, nan, nan],
            [fuel.MOTORCYCLE_ROW, 6.0, 2.0, 7.0, 2.0],
            [fuel.CAR_ROW, 11.0, 1.0, 12.0, 1.0]]
    return pd.DataFrame(rows)


def test_the_fuel_reader_finds_rows_and_column_by_label_within_the_state():
    b = fuel.read_rates(_table6(), 'State B')
    assert b[fuel.CAR_ROW] == 12.0 and b[fuel.MOTORCYCLE_ROW] == 7.0   # Total fuel, not Petrol
    a = fuel.read_rates(_table6(), 'State A')
    assert a == {fuel.CAR_ROW: 10.0, fuel.MOTORCYCLE_ROW: 5.5}          # the block ends at B
    with pytest.raises(SystemExit):
        fuel.read_rates(_table6(), 'State C')


def test_the_packaged_survey_gives_the_declared_ratio():
    """Against the acquired cube, where the package holds it."""
    pd = pytest.importorskip('pandas')
    path = REPO / 'cities/newcastle/data/raw/abs/92080DO001_202006.xls'
    if not path.exists():
        pytest.skip('SMVU cube not on this checkout')
    import city
    state = city.descriptor()['jurisdiction']['subdivision']
    r = fuel.read_rates(pd.read_excel(path, sheet_name=fuel.SHEET, header=None), state)
    ratio = r[fuel.MOTORCYCLE_ROW] / r[fuel.CAR_ROW]
    assert ratio == bmp.CFG.get('C.scoring.motorbike_fuel_ratio')


class _Cfg:
    def __init__(self, **v):
        self.v = v

    def get(self, key, caller=None):
        return self.v[key]


def test_the_motorbike_running_cost_is_written_under_choice_only():
    import build_matsim_run_inputs as bmri
    cfg = dict(**{'C.scoring.monetary_distance_rate': {'car': -0.00018, 'motorbike': 0.0},
                  'C.scoring.motorbike_fuel_ratio': 6.1 / 11.4})
    got = bmri.motorbike_running_cost(_Cfg(**{'B.motorbike.representation': 'choice'}, **cfg))
    value, role, note = got['scoring.modeParams[motorbike].monetaryDistanceRate']
    assert value == pytest.approx(-0.00018 * 6.1 / 11.4) and role == 'derived'
    assert bmri.motorbike_running_cost(
        _Cfg(**{'B.motorbike.representation': 'carve'}, **cfg)) == {}


def test_the_runtime_entry_replaces_the_table_value_in_the_emitted_set():
    """The emitter places a runtime entry after the bound fields, so the
    derived motorbike rate replaces the declared table's 0.0 for that one set
    and leaves car's alone."""
    import param_config
    import build_matsim_run_inputs as bmri
    cfg = bmp.CFG
    runtime = bmri.motorbike_running_cost(_Cfg(**{
        'B.motorbike.representation': 'choice',
        'C.scoring.monetary_distance_rate': cfg.get('C.scoring.monetary_distance_rate'),
        'C.scoring.motorbike_fuel_ratio': cfg.get('C.scoring.motorbike_fuel_ratio')}))
    field = cfg.field('C.scoring.monetary_distance_rate')
    fields = {'C.scoring.monetary_distance_rate': field}
    _, _, sets, _ = param_config.collect('matsim', cfg, runtime, fields)
    mp = sets['scoring']['modeParams']
    car = cfg.get('C.scoring.monetary_distance_rate')['car']
    ratio = cfg.get('C.scoring.motorbike_fuel_ratio')
    assert float(mp['motorbike']['monetaryDistanceRate'][0]) == pytest.approx(car * ratio)
    assert float(mp['car']['monetaryDistanceRate'][0]) == pytest.approx(car)
    _, _, sets0, _ = param_config.collect('matsim', cfg, {}, fields)
    assert float(sets0['scoring']['modeParams']['motorbike']['monetaryDistanceRate'][0]) == 0.0


# -- the daily use (D28, B.motorbike.daily_use) -------------------------------
def _available(drawn, on_day):
    """The composition load_motorbike_availability applies per person."""
    return {pid: bool(r and h and on_day[pid]) for pid, (r, h) in drawn.items()}


def test_the_daily_draw_is_deterministic_and_on_its_own_named_stream():
    a = bmp.draw_motorbike_daily_use(PERS2, SEED, 'use_ratio', 0.18)
    assert a == bmp.draw_motorbike_daily_use(PERS2, SEED, 'use_ratio', 0.18)
    assert a != bmp.draw_motorbike_daily_use(PERS2, SEED + 1, 'use_ratio', 0.18)
    w = np.random.default_rng([SEED] + list(b'motorbike_daily_use')).random(len(PERS2))
    assert a == {p[0]: bool(w[i] < 0.18) for i, p in enumerate(PERS2)}
    assert sum(a.values()) / len(a) == pytest.approx(0.18, abs=0.02)
    others = [np.random.default_rng([SEED, 1]).random(5),
              bmp.seeded_stream(SEED, 'rider_licence').random(5),
              bmp.seeded_stream(SEED, 'household_motorcycle').random(5)]
    mine = bmp.seeded_stream(SEED, 'motorbike_daily_use').random(5)
    assert not any(np.allclose(mine, o) for o in others)


def test_the_daily_draw_shifts_no_other_draw_and_no_other_draw_shifts_it():
    """The licence and motorcycle draws are the same whether or not the day is
    drawn, and the day is the same whatever the rates behind the other two."""
    before = _riders_first()
    bmp.draw_motorbike_daily_use(PERS2, SEED, 'use_ratio', 0.18)
    assert _riders_first() == before
    day = bmp.draw_motorbike_daily_use(PERS2, SEED, 'use_ratio', 0.18)
    bmp.draw_motorbike_availability(PERS2, HH2, lambda s, a: 0.9, lambda s: 0.7, SEED)
    assert bmp.draw_motorbike_daily_use(PERS2, SEED, 'use_ratio', 0.18) == day


def test_possession_reproduces_the_f38_availability_exactly():
    drawn = _riders_first()
    day = bmp.draw_motorbike_daily_use(PERS2, SEED, 'possession',
                                       bmp.MOTORBIKE_DAILY_USE_RATIO)
    assert all(day.values())
    assert _available(drawn, day) == {pid: bool(r and h) for pid, (r, h) in drawn.items()}


def test_use_ratio_thins_only_the_available_by_possession():
    drawn = _riders_first()
    by_possession = {p for p, (r, h) in drawn.items() if r and h}
    avail = _available(drawn, bmp.draw_motorbike_daily_use(PERS2, SEED, 'use_ratio', 0.18))
    on = {p for p, v in avail.items() if v}
    assert on <= by_possession and 0 < len(on) < len(by_possession)
    assert not any(_available(drawn, bmp.draw_motorbike_daily_use(
        PERS2, SEED, 'use_ratio', 0.0)).values())
    assert {p for p, v in _available(drawn, bmp.draw_motorbike_daily_use(
        PERS2, SEED, 'use_ratio', 1.0)).items() if v} == by_possession


def test_an_unknown_daily_use_or_a_ratio_outside_a_probability_is_refused():
    with pytest.raises(ValueError):
        bmp.draw_motorbike_daily_use(PERS2, SEED, 'made_up', 0.18)
    with pytest.raises(ValueError):
        bmp.draw_motorbike_daily_use(PERS2, SEED, 'use_ratio', 1.2)


def test_the_registry_ships_the_gate_and_a_probability():
    assert bmp.MOTORBIKE_DAILY_USE in bmp.DAILY_USE_MODES
    assert 0.0 < bmp.MOTORBIKE_DAILY_USE_RATIO < 1.0
    f = bmp.CFG.field('B.motorbike.daily_use_ratio')
    assert f['source'] == 'derived' and 'B.motorbike.daily_use' in f['derived_from']['fields']


def test_the_motorbike_constant_is_swept_for_sensitivity_and_not_free():
    """C.asc.motorbike is assumed with a bracket containing its shipped value,
    and `placeholder` keeps it out of the calibrator's free parameters."""
    import calibrate
    f = bmp.CFG.field('C.asc.motorbike')
    lo, hi = calibrate.sweep_interval(f)
    assert f['source'] == 'assumed' and lo <= f['value'] <= hi
    assert 'C.asc.motorbike' not in {p['key'] for p in calibrate.free_parameters(bmp.CFG)}


# -- a `choice` build refuses a missing observed table ------------------------
def test_a_missing_observed_table_is_refused_by_name(tmp_path):
    present = {bmp.MOTORBIKE_TABLES[1][0]}
    for rel in present:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text('x\n', encoding='utf-8')
    with pytest.raises(SystemExit) as e:
        bmp.require_motorbike_tables(lambda rel: str(tmp_path / rel))
    msg = str(e.value)
    assert bmp.MOTORBIKE_TABLES[0][0] in msg and bmp.MOTORBIKE_TABLES[0][1] in msg
    assert bmp.MOTORBIKE_TABLES[1][0] not in msg


def test_both_tables_missing_names_both_and_both_present_passes(tmp_path):
    with pytest.raises(SystemExit) as e:
        bmp.require_motorbike_tables(lambda rel: str(tmp_path / rel))
    assert all(rel in str(e.value) and builder in str(e.value)
               for rel, builder in bmp.MOTORBIKE_TABLES)
    for rel, _ in bmp.MOTORBIKE_TABLES:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text('x\n', encoding='utf-8')
    bmp.require_motorbike_tables(lambda rel: str(tmp_path / rel))


def test_the_lookups_refuse_before_reading_anything(monkeypatch, tmp_path):
    """motorbike_rate_lookups() is the `choice` path's only reader, and it
    asks for the tables first - no pooled fallback for a missing file."""
    import city as _c
    monkeypatch.setattr(_c, 'path', lambda *parts: str(tmp_path.joinpath(*parts)))
    with pytest.raises(SystemExit):
        bmp.motorbike_rate_lookups()


# -- the SMVU use ratio (B.motorbike.daily_use_ratio) --------------------------
def _table4():
    """Table 4's shape: totals, vehicle counts and a rounded average per state."""
    pd = pytest.importorskip('pandas')
    nan = float('nan')
    rows = [[nan] * 7,
            ['Table 4 Motor vehicle use, by state/territory of registration', nan, nan,
             nan, nan, nan, nan],
            [nan, fuel.KM_COLUMN, fuel.KM_COLUMN + ' - RSE', fuel.VEHICLES_COLUMN,
             fuel.VEHICLES_COLUMN + ' - RSE', fuel.AVERAGE_COLUMN,
             fuel.AVERAGE_COLUMN + ' - RSE'],
            [nan, 'million', '%', 'no.', '%', "'000", '%'],
            ['State A', nan, nan, nan, nan, nan, nan],
            [fuel.CAR_ROW, 1000.0, 5.0, 100000.0, 1.0, 10.0, 5.0],
            [fuel.MOTORCYCLE_ROW, 20.0, 15.0, 10000.0, 3.0, 2.0, 15.0],
            ['State B', nan, nan, nan, nan, nan, nan],
            [fuel.MOTORCYCLE_ROW, 30.0, 15.0, 12000.0, 3.0, 2.5, 15.0],
            [fuel.CAR_ROW, 1200.0, 5.0, 110000.0, 1.0, 10.9, 5.0],
            ['State C', nan, nan, nan, nan, nan, nan],
            [fuel.CAR_ROW, 1200.0, 5.0, 110000.0, 1.0, 10.9, 5.0]]
    return pd.DataFrame(rows)


def test_the_use_reader_takes_totals_by_label_within_the_state():
    b = fuel.read_use(_table4(), 'State B')
    # km per vehicle from the TOTALS, not the rounded average column
    assert b['daily_use_ratio'] == (30.0 / 12000.0) / (1200.0 / 110000.0)
    assert b['motor_cycles_published_average_km_thousand'] == 2.5
    a = fuel.read_use(_table4(), 'State A')                 # the block ends at B
    assert a['daily_use_ratio'] == (20.0 / 10000.0) / (1000.0 / 100000.0)
    with pytest.raises(SystemExit):
        fuel.read_use(_table4(), 'State C')                 # no motor cycles row
    with pytest.raises(SystemExit):
        fuel.read_use(_table4(), 'State D')


def test_the_packaged_survey_gives_the_declared_use_ratio():
    """Against the acquired cube, where the package holds it."""
    pd = pytest.importorskip('pandas')
    path = REPO / 'cities/newcastle/data/raw/abs/92080DO001_202006.xls'
    if not path.exists():
        pytest.skip('SMVU cube not on this checkout')
    import city
    state = city.descriptor()['jurisdiction']['subdivision']
    u = fuel.read_use(pd.read_excel(path, sheet_name=fuel.USE_SHEET, header=None), state)
    assert u['daily_use_ratio'] == bmp.CFG.get('B.motorbike.daily_use_ratio')
