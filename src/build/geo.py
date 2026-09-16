"""Two geometry helpers every builder used to carry its own copy of.

`haversine` was defined five times and `kinematic_time` three times across the
city builders and the framework (twelfth report, 16 September 2026), each copy
identical to the byte. They live here once; a builder imports them. Both are
pure functions of their arguments, so the artefacts a builder writes are the
same bytes they were.
"""
import math

EARTH_RADIUS_M = 6371000.0   # the mean Earth radius every copy carried


def haversine(a, b):
    """Great-circle metres between two (lat, lon) pairs in degrees."""
    R = EARTH_RADIUS_M
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dl = math.radians(b[1] - a[1])
    dp = p2 - p1
    return 2 * R * math.asin(math.sqrt(
        math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2))


def kinematic_time(d, v_kmh, a, b):
    """Seconds to cover d metres from rest to rest at a line speed of v_kmh
    with acceleration a and deceleration b (m/s^2): trapezoidal when the
    distance allows the line speed to be reached, triangular otherwise."""
    v = v_kmh / 3.6
    da, db = v * v / (2 * a), v * v / (2 * b)
    if d >= da + db:
        return v / a + v / b + (d - da - db) / v
    vp = math.sqrt(2 * d * a * b / (a + b))
    return vp / a + vp / b
