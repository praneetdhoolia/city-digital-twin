"""Every demand tier the chains carry reaches the population file - or the build refuses.

`build_matsim_plans.write_person` decides, per agent, whether a <person> is
written at all. The staging of 16 September 2026 tested only `through` and
`freight` as household-less tiers, so all 6,103 EXTERNAL agents returned before
the writer and the F36 plans ran without them; no check noticed for nine days
(fourteenth report). The repair is two-sided and both halves are pinned here:

  * `write_person`: a boundary tier (external, through, freight) is written
    WITHOUT a B1 lookup; only a resident (core) person is looked up, and a
    resident B1 does not carry writes nothing. `ctx.tiers_out` counts what was
    written, tier by tier.
  * `write_day`: the tiers the chains carried (`tiers_in`) must equal the tiers
    written (`tiers_out`), or the day is REFUSED - so an early return that loses
    agents stops the build instead of shipping a short population.

The ctx is the same namespace `write_day` builds, field for field; the rows are
a two-trip home-work-home tour per agent. Nothing reads the data package: the
module's registry values are the city's declared ones, and `write_day` is
pointed at a temporary directory for its three paths.
"""
import collections
import csv
import gzip
import io
import types
import xml.etree.ElementTree as ET

import numpy as np
import pytest

import build_matsim_plans as bmp

ROW_FIELDS = ('person_id', 'trip_seq', 'agent_tier', 'tour_id', 'origin_x',
              'origin_y', 'dest_x', 'dest_y', 'dep_time_s',
              'dest_activity_type', 'dest_placement')


def _rows(pid, tier):
    """A home -> work -> home tour, trips deliberately out of order."""
    back = dict(person_id=str(pid), trip_seq='2', agent_tier=tier, tour_id='1',
                origin_x='5000.0', origin_y='0.0', dest_x='0.0', dest_y='0.0',
                dep_time_s='61200', dest_activity_type='home', dest_placement='')
    out = dict(person_id=str(pid), trip_seq='1', agent_tier=tier, tour_id='1',
               origin_x='0.0', origin_y='0.0', dest_x='5000.0', dest_y='0.0',
               dep_time_s='28800', dest_activity_type='work', dest_placement='')
    return [back, out]


def _ctx(attrs=None):
    """The namespace write_day hands write_person, with empty binding tables."""
    return types.SimpleNamespace(
        act_counts=collections.Counter(), attrs=attrs or {}, bound_driver={},
        bound_placement={'ride_tours': 0, 'partial_tours': 0, 'plans_folded': 0,
                         'alternatives_kept': 0, 'alternatives_folded_held': 0,
                         'held_ride_trips': 0, 'held_persons': set(),
                         'persons': set()},
        covered_by_pid={}, covered_ride_legs=[0], escort_cover={},
        escort_ride_denied=[0], hh_vehicle_count={}, joint_companion={},
        joint_driver={},
        leaf_mix_repairs={'tours': 0, 'ride_tours_driven': 0, 'persons': set()},
        lift_cover={}, lift_hh={}, modes=collections.Counter(), n_acts=0,
        n_legs=0, n_legs_selected=0, n_persons=0,
        partial_bind={'tours': 0, 'trips': 0, 'plans_added': 0, 'persons': set()},
        seed_plans_hist=collections.Counter(), seed_table=None,
        serve_tours_carless=[0], shared_driver={}, shared_hh={}, tours=0,
        u=lambda: 0.5,
        unreachable={'escort_day_trips': 0, 'escort_day_persons': set(),
                     'no_vehicle_trips': 0, 'no_vehicle_persons': set()},
        w=io.StringIO(), tiers_in=collections.Counter(),
        tiers_out=collections.Counter())


# a resident as load_person_attributes returns one: (car, age, licence, employment,
# student, mobility, ride, bike, household, income)
RESIDENT = (1, 35, 1, 'employed_full_time', 'none', 0, 1, 1, 77, 900.0)


def _persons(ctx):
    root = ET.fromstring('<population>%s</population>' % ctx.w.getvalue())
    return {int(p.get('id')): p for p in root.findall('person')}


def _attr(person, name):
    for a in person.find('attributes').findall('attribute'):
        if a.get('name') == name:
            return a.text
    return None


def _legs(person):
    return [leg.get('mode') for plan in person.findall('plan')
            for leg in plan.findall('leg')]


def test_external_agent_absent_from_b1_is_written():
    ctx = _ctx()
    bmp.write_person(9001, _rows(9001, 'external'), ctx)
    persons = _persons(ctx)
    assert list(persons) == [9001]
    p = persons[9001]
    assert _attr(p, 'subpopulation') == 'external'
    # household-less by construction: no household, no driver, no ride
    assert _attr(p, 'householdId') is None
    assert _attr(p, 'rideAvail') == 'never'
    assert 'ride' not in _legs(p)
    assert ctx.tiers_out == {'external': 1}
    assert ctx.n_persons == 1


def test_core_resident_absent_from_b1_writes_nothing():
    ctx = _ctx()
    bmp.write_person(5, _rows(5, 'core'), ctx)
    assert ctx.w.getvalue() == ''
    assert ctx.n_persons == 0
    assert ctx.tiers_out['core'] == 0
    assert ctx.tours == 0


def test_core_resident_in_b1_is_written_with_its_household():
    ctx = _ctx({5: RESIDENT})
    bmp.write_person(5, _rows(5, 'core'), ctx)
    p = _persons(ctx)[5]
    assert _attr(p, 'subpopulation') == 'person'
    assert _attr(p, 'householdId') == '77'
    assert _attr(p, 'income') == '900.0'
    assert _attr(p, 'lockedMode') is None
    # exactly one selected plan, whatever the seed method
    assert [pl.get('selected') for pl in p.findall('plan')].count('yes') == 1
    assert ctx.tiers_out == {'core': 1}


@pytest.mark.parametrize('tier, locked, subpop', [
    ('through', 'car', 'external'),
    ('freight', 'truck', 'freight'),
])
def test_locked_tiers_are_written_on_their_lock(tier, locked, subpop):
    ctx = _ctx()
    bmp.write_person(8000, _rows(8000, tier), ctx)
    p = _persons(ctx)[8000]
    assert _attr(p, 'subpopulation') == subpop
    assert _attr(p, 'lockedMode') == locked
    assert set(_legs(p)) == {locked}
    assert len(p.findall('plan')) == 1          # a lock is a definition
    assert ctx.tiers_out == {tier: 1}


def test_tiers_out_counts_each_tier_and_legs_follow_trip_seq():
    ctx = _ctx({1: RESIDENT})
    for pid, tier in ((1, 'core'), (2, 'core'), (3, 'external'),
                      (4, 'through'), (5, 'freight'), (6, 'external')):
        bmp.write_person(pid, _rows(pid, tier), ctx)
    assert ctx.tiers_out == {'core': 1, 'external': 2, 'through': 1, 'freight': 1}
    assert ctx.n_persons == 5
    persons = _persons(ctx)
    assert sorted(persons) == [1, 3, 4, 5, 6]
    # the rows arrived out of order; the plan follows trip_seq
    first_plan = persons[3].find('plan')
    acts = [a.get('type') for a in first_plan.findall('activity')]
    assert acts == ['home', 'work', 'home']
    assert first_plan.find('activity').get('end_time') == '08:00:00'


# --------------------------------------------------------------------------
# write_day: the per-tier refusal
# --------------------------------------------------------------------------
def _stage_day(tmp_path, monkeypatch, persons):
    plans = tmp_path / 'plans'
    pop = tmp_path / 'population'
    out = tmp_path / 'matsim'
    for d in (plans, pop, out):
        d.mkdir()
    with open(pop / 'B1_households.csv', 'w', newline='', encoding='utf-8') as fh:
        w = csv.writer(fh)
        w.writerow(['household_id', 'household_vehicles'])
        w.writerow([77, 1])
    with open(plans / 'B2_activity_trips_TESTDAY.csv', 'w', newline='',
              encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=ROW_FIELDS)
        w.writeheader()
        for pid, tier in persons:                 # sorted by person id
            for r in sorted(_rows(pid, tier), key=lambda r: r['trip_seq']):
                w.writerow(r)
    monkeypatch.setattr(bmp, 'PLANS', str(plans))
    monkeypatch.setattr(bmp, 'POP', str(pop))
    monkeypatch.setattr(bmp, 'OUT', str(out))
    return out


def test_write_day_reports_every_tier_it_carried(tmp_path, monkeypatch, capsys):
    out = _stage_day(tmp_path, monkeypatch,
                     [(1, 'core'), (2, 'external'), (3, 'through'), (4, 'freight')])
    report = {}
    bmp.write_day('TESTDAY', {1: RESIDENT}, np.random.default_rng(1), report)
    assert report['TESTDAY']['persons'] == 4
    assert report['TESTDAY']['persons_by_tier'] == {
        'core': 1, 'external': 1, 'freight': 1, 'through': 1}
    with gzip.open(out / 'population_TESTDAY.xml.gz', 'rt', encoding='utf-8') as fh:
        root = ET.fromstring(fh.read())
    assert sorted(int(p.get('id')) for p in root.findall('person')) == [1, 2, 3, 4]


def test_write_day_refuses_a_day_that_lost_agents(tmp_path, monkeypatch):
    # person 2 is a resident B1 does not carry: write_person skips it, and the
    # day must refuse rather than ship a population one agent short
    _stage_day(tmp_path, monkeypatch, [(1, 'core'), (2, 'core'), (3, 'external')])
    with pytest.raises(SystemExit) as e:
        bmp.write_day('TESTDAY', {1: RESIDENT}, np.random.default_rng(1), {})
    msg = str(e.value)
    assert msg.startswith('REFUSED')
    assert "'core': (2, 1)" in msg
    assert 'external' not in msg
