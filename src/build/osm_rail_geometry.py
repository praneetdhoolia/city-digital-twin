"""Compatibility entry points for the native railway geometry tables."""
from build.osm_way_geometry import build as _build, collect as _collect


def collect(inputs, projected_crs):
    return _collect(inputs, projected_crs, feature_key='railway')


def build(inputs, output_dir, projected_crs):
    return _build(inputs, output_dir, projected_crs, feature_key='railway')
