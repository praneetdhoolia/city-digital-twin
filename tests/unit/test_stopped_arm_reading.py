"""A stopped arm is read AT the iteration it reached, and says so.

The rule is not new. `GOAL.md` and DECISIONS.md 9.143 already say a run that
did not reach its last iteration is citable at its `reached_iteration` and
nowhere past it. What was missing was the implementation: MATSim writes
`output_trips` only at controler end, so `extract_metrics` raised
`output_trips not found` on every arm that stopped at its gate — which is
EVERY arm this project has produced since F4. No gate arm had a
`_metrics.json`, therefore none had a `_fit.json`, therefore the fit half of
the pipeline had never once run on the kind of run the project actually makes.

Three things are asserted, because the fix is only safe if all three hold:

  * a stopped arm's tables are found at its reached iteration;
  * a completed run is untouched and still reads its final output;
  * the count comparison, which has NO per-iteration counterpart, is reported
    unavailable rather than substituted from a different table.

That last one is the one that matters. `linkstats` exists per iteration and is
the obvious thing to reach for; it is a different table with a different shape,
and comparing it against a target derived for `output_links` would be the same
class of basis error 9.101 records for truck.
"""
import extract_metrics as em


def test_a_stopped_arm_reads_the_iteration_it_reached():
    assert em.iteration_stem('output_trips', 100) == 'ITERS/it.100/100.trips'
    assert em.iteration_stem('output_legs', 23) == 'ITERS/it.23/23.legs'


def test_a_completed_run_reads_its_final_output():
    """iteration None means the run reached its last iteration and the final
    tables exist; nothing is redirected."""
    assert em.iteration_stem('output_trips', None) is None


def test_only_a_final_output_table_has_a_per_iteration_spelling():
    """A stem that is not a MATSim final-output table is left alone — the
    per-iteration path is derived from the `output_` prefix, not guessed."""
    assert em.iteration_stem('ITERS/it.5/5.trips', 100) is None
    assert em.iteration_stem('station_links', 100) is None


def test_the_read_point_defaults_to_the_final_output():
    """Module state, so a test that sets it must not leak into the next one."""
    assert em._READ_AT['iteration'] is None
