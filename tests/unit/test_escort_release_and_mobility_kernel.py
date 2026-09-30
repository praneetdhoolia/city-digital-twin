"""The two demand mechanisms of 9.214, on inputs the tests build themselves.

A one-way escort binding held a licensed, car-available member's outward trip
to ride and left the car at home for the whole tour: on F37's arm 0 those tours
carried 35.6 % of residents' walk km. The release drops that binding and marks
the serve tour as serving nobody, so the lift pass may offer it to a
non-household passenger. And destinations are drawn by the person's own
mobility: one time decay at each segment's planning speed, solved so the two
segments together realise the observed mean.
"""
import collections
import types

import numpy as np

import build_activity_chains as bac


def _household(lic, cav):
    """Two members: an escorter (0) and a member (1) with the given mobility."""
    mc = types.SimpleNamespace(pid=np.array([10, 11]), lic=np.array([True, lic]),
                               cav=np.array([True, cav]))
    hc = types.SimpleNamespace(mc=mc, hh_bindings=[], esc=collections.Counter())
    member_leg = dict(tour_id=1, is_tour_anchor=1, tour_purpose='HW',
                      dest_placement='poi', dest_x=5.0, dest_y=7.0)
    serve = [dict(tour_id=3, is_tour_anchor=1, tour_purpose='HX',
                  dest_placement='escorted', dest_x=5.0, dest_y=7.0),
             dict(tour_id=3, is_tour_anchor=0, tour_purpose='HX',
                  dest_placement='home', dest_x=0.0, dest_y=0.0)]
    legs_of = {0: serve, 1: [member_leg]}
    return hc, legs_of


def test_a_member_who_could_drive_is_released_and_the_serve_tour_serves_nobody():
    hc, legs_of = _household(lic=True, cav=True)
    hc.hh_bindings.append(dict(member_person_id=11, member_tour_id=1,
                               direction='drop', driver_person_id=10))
    bac.release_oneway_drivers([0, 1], 0, legs_of, hc)
    assert hc.hh_bindings == []
    assert hc.esc['released_oneway_drop'] == 1
    assert legs_of[0][0]['dest_placement'] == 'escort_released'
    assert legs_of[0][1]['dest_placement'] == 'home'
    # the lift pass reads a released tour as an unbound one
    assert 'escort_released' in bac.UNBOUND_SERVE_PLACEMENTS


def test_a_member_who_cannot_drive_keeps_the_one_way_binding():
    for lic, cav in ((False, True), (True, False)):
        hc, legs_of = _household(lic=lic, cav=cav)
        row = dict(member_person_id=11, member_tour_id=1, direction='drop',
                   driver_person_id=10)
        hc.hh_bindings.append(row)
        bac.release_oneway_drivers([0, 1], 0, legs_of, hc)
        assert hc.hh_bindings == [row]
        assert legs_of[0][0]['dest_placement'] == 'escorted'


def test_a_round_trip_is_never_released():
    hc, legs_of = _household(lic=True, cav=True)
    rows = [dict(member_person_id=11, member_tour_id=1, direction=d,
                 driver_person_id=10) for d in ('drop', 'pickup')]
    hc.hh_bindings.extend(rows)
    bac.release_oneway_drivers([0, 1], 0, legs_of, hc)
    assert hc.hh_bindings == rows


def test_only_this_households_rows_are_touched():
    hc, legs_of = _household(lic=True, cav=True)
    earlier = dict(member_person_id=99, member_tour_id=1, direction='drop',
                   driver_person_id=98)
    hc.hh_bindings.extend([earlier, dict(member_person_id=11, member_tour_id=1,
                                         direction='drop', driver_person_id=10)])
    bac.release_oneway_drivers([0, 1], 1, legs_of, hc)
    assert hc.hh_bindings == [earlier]


def _line(n=40, km=1.0):
    x = np.arange(n, dtype=float) * km
    return np.abs(x[None, :] - x[:, None]), np.ones(n), np.full(n, 1.0 / n)


def test_one_segment_is_the_single_kernel_exactly():
    dkm, aeff, w = _line()
    assert bac._solve_decay(aeff, dkm, w, 6.0) == bac._solve_decay(
        aeff, dkm, w, 6.0, seg=None)


def test_the_two_segments_together_hit_the_target_and_the_carless_travel_shorter():
    dkm, aeff, w = _line()
    share = np.full(dkm.shape[0], 0.2)
    ratio = 1.25
    beta, got = bac._solve_decay(aeff, dkm, w, 6.0, seg=(share, ratio))
    assert abs(got - 6.0) < 1e-3
    car = float((w * bac._row_mean_km(aeff, dkm, beta)).sum())
    nocar = float((w * bac._row_mean_km(aeff, dkm, ratio * beta)).sum())
    assert nocar < 6.0 < car
    assert abs(0.8 * car + 0.2 * nocar - 6.0) < 1e-3
