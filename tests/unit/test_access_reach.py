"""The pt access ceiling may not cut the nearest-stop fallback.

`RUN.transit_router.access_max_radius_m` was derived as 1,000 + 200 m, which
refused transit to every trip end beyond 1.2 km of a stop and doubled the
no-route share (fourteenth report). The assembler now measures the reach -
the farthest activity location's nearest stop - and refuses a ceiling below
it plus the extension.
"""
import gzip

import pytest

import build_matsim_run_inputs as bi

SCHEDULE = ('<transitSchedule><transitStops>\n'
            '<stopFacility id="a" x="0.0" y="0.0" linkRefId="1"/>\n'
            '<stopFacility id="b" x="10000.0" y="0.0" linkRefId="2"/>\n'
            '</transitStops></transitSchedule>\n')


def _files(tmp_path, far_x):
    sched = tmp_path / 'transitSchedule.xml.gz'
    with gzip.open(sched, 'wt', encoding='utf-8') as fh:
        fh.write(SCHEDULE)
    trips = tmp_path / 'trips.csv'
    trips.write_text('origin_x,origin_y,dest_x,dest_y\n'
                     '100,0,9900,0\n'
                     '%s,0,0,0\n' % far_x, encoding='utf-8')
    return str(sched), str(trips)


def test_the_reach_is_the_farthest_nearest_stop(tmp_path):
    bi._REACH.clear()
    sched, trips = _files(tmp_path, far_x=5000)      # halfway: 5 km from both
    reach = bi.nearest_stop_reach_m(sched, trips)
    assert reach == pytest.approx(5000, abs=50)


def test_a_point_far_outside_every_cell_is_still_found(tmp_path):
    bi._REACH.clear()
    sched, trips = _files(tmp_path, far_x=-26500)    # 26.5 km beyond stop a
    assert bi.nearest_stop_reach_m(sched, trips) == pytest.approx(26500, abs=50)


def test_a_ceiling_below_the_reach_is_refused(tmp_path, monkeypatch):
    bi._REACH.clear()
    sched, trips = _files(tmp_path, far_x=5000)
    monkeypatch.setattr(bi._city, 'path', lambda rel: trips)
    cfg = {'RUN.transit_router.access_search_extension_radius_m': 200.0,
           'RUN.transit_router.access_max_radius_m': 1200.0}

    class C(dict):
        get = dict.get
    with pytest.raises(SystemExit, match='below the nearest-stop reach'):
        bi.refuse_access_ceiling_below_reach(C(cfg), sched, 'WEEKDAY')
    ok = C(cfg, **{'RUN.transit_router.access_max_radius_m': 5300.0})
    assert bi.refuse_access_ceiling_below_reach(ok, sched, 'WEEKDAY') == pytest.approx(5000, abs=50)
