"""The one mapping from C1's alternative-specific-constant names to registry keys.

Imported by `build_params.py` (which writes the C1 table from the registry) and
by `build_matsim_run_inputs.py` (which emits the scoring constants from the
registry at every launch), so the two cannot disagree. It lives on its own
because `build_params.py` loads the registry and creates its output directory
at import, and the emitter is imported by every launch and every unit test.
"""

ASC_FIELDS = [('asc_car_driver', 'C.asc.car_driver'),
              ('asc_car_passenger', 'C.asc.car_passenger'),
              ('asc_bus', 'C.asc.bus'),
              ('asc_lr', 'C.asc.light_rail'),
              ('asc_rail', 'C.asc.rail'),
              ('asc_walk', 'C.asc.walk'),
              ('asc_cycle', 'C.asc.cycle'),
              ('asc_motorbike', 'C.asc.motorbike'),
              ('asc_ferry', 'C.asc.ferry')]
