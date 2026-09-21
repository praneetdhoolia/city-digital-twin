"""Clock corruption and fleet accounting must not manufacture bus supply."""
import importlib.util
from pathlib import Path

from pyproj import Geod
import pytest

PATH = Path(__file__).resolve().parents[2] / 'cities/mumbai/build/build_regional_bus_feed.py'
SPEC = importlib.util.spec_from_file_location('regional_bus_feed', PATH)
adapter = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(adapter)


def test_clock_reversal_is_missing_instead_of_twenty_four_hour_segment():
    assert adapter.segment_seconds('43200', '43140', 3600) is None
    assert adapter.segment_seconds('86340', '120', 3600) is None
    assert adapter.segment_seconds('43200', '43320', 3600) == 120
    assert adapter.segment_seconds('43200', '43200', 3600) is None
    assert adapter.segment_seconds('43200', '50000', 3600) is None


def test_directed_patterns_consume_fleet_once_and_round_conservatively():
    # Two directions, 30 minutes each plus terminal time. Four buses give an
    # 18-minute headway, not 36 minutes (double-counted return directions).
    assert adapter.pooled_headway([1800, 1800], 4, 360) == 1080
    assert adapter.pooled_headway([1801, 1800], 4, 360) == 1081
    with pytest.raises(ValueError):
        adapter.pooled_headway([1800], 0, 360)


def test_offsets_use_published_median_and_derive_missing_or_impossible_segments():
    stops = [dict(stop_lon=0, stop_lat=0), dict(stop_lon=.01, stop_lat=0),
             dict(stop_lon=.02, stop_lat=0), dict(stop_lon=.03, stop_lat=0)]
    offsets, counts = adapter.pattern_offsets(stops, [[200, 300, 400], [1], []],
        Geod(ellps='WGS84'), dict(speed_ms=10, distance_multiplier=1, dwell_s=20, maximum_delay_ratio=4))
    assert offsets[1] == 300
    assert 130 < offsets[2] - offsets[1] < 140
    assert offsets[3] - offsets[2] == offsets[2] - offsets[1]
    assert counts == {'published_median': 1, 'geographic_floor_over_published': 1,
                      'geographic_derivation': 1}


def test_published_clock_outlier_does_not_make_a_local_bus_take_all_day():
    stops = [dict(stop_lon=0, stop_lat=0), dict(stop_lon=.01, stop_lat=0)]
    offsets, counts = adapter.pattern_offsets(stops, [[1500, 1800]],
        Geod(ellps='WGS84'), dict(speed_ms=10, distance_multiplier=1, dwell_s=20, maximum_delay_ratio=4))
    assert 130 < offsets[-1] < 140
    assert counts['published_timing_rejected_as_outlier'] == 1
