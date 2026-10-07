#!/usr/bin/env python
"""Find values the model uses that were decided in a script, not declared.

    python src/registry/check_hardcoding.py               report the active city
    python src/registry/check_hardcoding.py --strict      exit 1 if anything is found
    python src/registry/check_hardcoding.py --json OUT    machine-readable ledger
    python src/registry/check_hardcoding.py --all-cities  every city under cities/
                                                          (the gate and CI)

A city's scripts carry what the city has not yet declared or classified, and a
second city brought 230 of them on the day it was built. Each city records
those, per question, in `cities/<city>/tests/hardcoding_debt.json` under a
ceiling that may only fall (src/registry/debt_ledger.py states the shape): an
item outside the record fails, a recorded item that no longer surfaces must be
deleted, and the gate is green and honest at once. A coordinate, a stale
register entry and a probe that could not run are never recordable.

This repository's signature defect is not a wrong number. It is a number in a
place nobody looks: a declared field that reaches nothing, a template literal
that shadows it, a sweep range typed beside the value it is supposed to bound.
Every instance found so far was caught by ARITHMETIC or by an audit, never by
reading the code, so the audit is committed rather than remembered.

Five questions, asked separately because the answers mean different things:

  1. UNWIRED FIELDS   a declared field whose key appears nowhere in the source
                      as a value. It cannot reach the model, whatever
                      `consumers` claims.
  2. REPORT-ONLY      a declared field read ONLY by the measurement layer. It
                      is printed back after a run; it decides nothing.
  3. TEMPLATE LITERALS a <param name=... value=...> written as a constant rather
                      than substituted. Each is a modelling choice in a builder.
  4. SCRIPT DECISIONS a value decided in code rather than declared - in any of
                      the five forms `scan_decisions` distinguishes.
  5. COORDINATES      a latitude/longitude pair typed into a script. The hard
                      constraint is absolute: a coordinate belongs in
                      `cities/<city>/geometry/` or the registry, never in code.
 10. WALL CLOCK       a build script reading the clock (`datetime.now()`,
                      `time.time()`, `date.today()`) or drawing from an
                      unseeded random stream. The determinism rule had no
                      scanner, and the manifest stamped every regeneration
                      with the time of day (#211).

**What changed, and why the count moved.** The first version of this audit
asked whether a field key was a SUBSTRING of any source file. That counted a
mention in a comment, a docstring or a test assertion as reach - so
`RUN.controler.write_events_interval`, named only in a Java comment, and
`A.signals.scats_phasing`, named only in a test, both passed as wired while
deciding nothing. Worse, the count fell when someone added an explanatory
comment. A gate you can satisfy by editing prose is not a gate. A key is now
counted as reaching the model only where it appears as a COMPLETE STRING
LITERAL in non-test source - the form a key takes when it is data.

The constant scan has the same history. It looked only at module-level,
single-target, ALL-CAPS, SCALAR assignments, which is a small minority of the
forms a decision takes: it could not see `ACCEL, DECEL = 1.2, 1.3`, a table of
stop coordinates, `def make_bus_shuttle(speed_kmh=28.0)`, or
`add_argument('--iterations', default=100)` for a field the registry declares
UNOBTAINED. It now delegates to `extract_legacy_constants.scan_decisions`,
which is the repository's one AST scanner for decided values.

It reports; it does not judge. A field may legitimately be read by prefix, and a
constant may be structural. The point is that every one of them is SEEN.

City-agnostic: the city comes from `city.py`, and nothing here names a place.
"""
import argparse
import ast
import io
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
import city as _city  # noqa: E402
import registry as _registry  # noqa: E402
import debt_ledger as _ledger  # noqa: E402
import extract_legacy_constants as _legacy  # noqa: E402

REPO = os.path.abspath(os.path.join(_HERE, '..', '..'))
SKIP_DIRS = {'.git', '__pycache__', '.tools', 'results', 'node_modules', '.venv'}
CODE_EXT = ('.py', '.java', '.html')

# The measurement apparatus: it reads a finished run and reports on it. A field
# read only here is printed, not applied. `calibrate.py` draws the same line for
# the same reason and this is the same list, imported rather than repeated.
MEASUREMENT_LAYERS = ('src/analyse/', 'src/calibrate/')

# The one file under tests/ that CONSUMES declared values rather than fixturing
# them: the package contract reads the registry to decide what the built package
# must contain. Every other test naming a key is a fixture, and a fixture is not
# a consumer - see unwired().
VALIDATION_CONSUMERS = ('tests/check_package.py',)

# How many lines either side of a <param> match are searched for the regex call
# that would make it a pattern rather than a value. A pattern is often built
# over several lines, so one line is not enough of a window.
REGEX_WINDOW = 3

# Files that TALK ABOUT the pattern rather than commit it. An audit that reports
# its own regex trains people to ignore it.
SELF_REFERENTIAL = ('src/registry/check_hardcoding.py',
                    'src/registry/extract_legacy_constants.py',
                    'src/registry/check_legacy_drift.py')

# A latitude/longitude pair, in ANY syntactic position. The previous rule wanted
# a literal two-tuple, so it saw three of this repository's coordinates and
# missed nineteen - a scenario's whole stop alignment was written as
# `('Civic', -32.92699, 151.77175)` and never reported. The test is now per
# LINE: a line carrying both a plausible latitude and a plausible longitude is a
# place, whatever brackets are around it.
FLOAT = re.compile(r'-?\d{1,3}\.\d{4,}')
LAT_MAX, LON_MAX, PLACE_MIN = 90.0, 180.0, 1.0

# A BOX GIVES ITSELF AWAY BY ITS CORNER NAMES, not by its precision. Three or
# more of these on one line, with numbers that could be a latitude and a
# longitude, is a hand-drawn extent however few decimals it carries - the class
# the four-decimal FLOAT rule above cannot see. Requires the corner names, so a
# line of ordinary two-decimal numbers is not reported.
EXTENT_KEYS = re.compile(
    r'(?:(?<![A-Za-z_])(?:s|w|n|e|south|west|north|east|lat_min|lat_max|'
    r'lon_min|lon_max|min_lat|max_lat|min_lon|max_lon)\s*[=:]).*?'
    r'(?:(?<![A-Za-z_])(?:s|w|n|e|south|west|north|east|lat_min|lat_max|'
    r'lon_min|lon_max|min_lat|max_lat|min_lon|max_lon)\s*[=:]).*?'
    r'(?:(?<![A-Za-z_])(?:s|w|n|e|south|west|north|east|lat_min|lat_max|'
    r'lon_min|lon_max|min_lat|max_lat|min_lon|max_lon)\s*[=:])')
COARSE_FLOAT = re.compile(r'-?\d{1,3}\.\d+')


def is_lat(v):
    return PLACE_MIN <= abs(v) <= LAT_MAX


def is_lon(v):
    return PLACE_MIN <= abs(v) <= LON_MAX


def sources(exts=CODE_EXT):
    """Every framework and city source file, city-relative agnostic."""
    for root in (os.path.join(REPO, 'src'), os.path.join(REPO, 'tests'),
                 _city.CITY_DIR, os.path.join(REPO, 'run.py')):
        if os.path.isfile(root):
            yield root
            continue
        for base, dirs, files in os.walk(root):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            if os.path.abspath(base) == os.path.abspath(_city.CITY_DIR):
                # A path under data/ is data: a .py there is a vendored
                # download (a published API client landed under data/raw/),
                # immutable by the provenance rule and not a script of ours.
                dirs[:] = [d for d in dirs if d != 'data']
            if os.path.abspath(base).startswith(os.path.join(_city.CITY_DIR,
                                                             'registry')):
                continue                  # a declaration is not a use
            for f in files:
                if f.endswith(exts):
                    yield os.path.join(base, f)


def rel(p):
    return os.path.relpath(p, REPO).replace(os.sep, '/')


def portable(path):
    """A repo-relative path with this city's directory written `<city>/`.

    So a framework register can name a file inside a city without naming the
    city - the same reason the manifest records city-relative paths.
    """
    prefix = 'cities/%s/' % _city.CITY
    return '<city>/' + path[len(prefix):] if path.startswith(prefix) else path


def is_test(path):
    return path.startswith('tests/')


def is_measurement(path):
    return any(path.startswith(m) for m in MEASUREMENT_LAYERS)


# --------------------------------------------------------------------------
# 1 + 2. where a declared key is actually used
# --------------------------------------------------------------------------
JAVA_STRING = re.compile(r'"([^"\\]*)"')


def key_uses(corpus, keys):
    """{key: {file: True}} for every COMPLETE string literal naming a key.

    A key inside a comment or a docstring is prose about the model, not a read
    of it. Only a whole string literal is the model using the key as data, and
    that distinction is the whole difference between this audit and the one it
    replaces.
    """
    out = {}
    for path, text in sorted(corpus.items()):
        r = rel(path)
        # An audit does not get to cite itself as evidence. This module names
        # keys in PENDING_CONSUMER and MEASUREMENT_OWNED_KEYS to EXCUSE them,
        # and counting those mentions as reads marked all seven pending fields
        # wired - which emptied the unwired list and made the gate pass for the
        # worst possible reason. Same exclusion the other four scans already use.
        if r in SELF_REFERENTIAL:
            continue
        literals = set()
        if path.endswith('.py'):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                continue
            docstrings = set()
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.FunctionDef,
                                     ast.AsyncFunctionDef, ast.ClassDef)):
                    doc = ast.get_docstring(node, clean=False)
                    if doc is not None and node.body:
                        first = node.body[0]
                        if isinstance(first, ast.Expr):
                            docstrings.add(id(first.value))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str) \
                        and id(node) not in docstrings:
                    literals.add(node.value)
        else:
            # Java and HTML have no AST here; a quoted run with no whitespace is
            # as close to "used as data" as a regex gets, and a comment naming a
            # key in prose does not survive it.
            literals = {m.group(1) for m in JAVA_STRING.finditer(text)}
        for key in keys:
            if key in literals:
                out.setdefault(key, set()).add(r)
        # A key BUILT at the call site, e.g.
        # `CFG.get('C.constraint.trip_length_km.%s' % mode)`. The docstring of
        # this audit has always conceded that a field may legitimately be read
        # by prefix; conceding it and then not detecting it reported eleven
        # measured constraint fields as unwired while a builder read every one.
        for pattern in _key_patterns(literals):
            for key in keys:
                if pattern.match(key):
                    out.setdefault(key, set()).add(r)
    return out


def _key_patterns(literals):
    """Regexes for string literals that CONSTRUCT a key rather than being one.

    Only literals that already look like a registry key are considered - at
    least two dotted segments and a placeholder - so an unrelated format string
    cannot start matching fields.
    """
    out = []
    for text in literals:
        if text.count('.') < 2:
            continue
        if '%s' not in text and '%d' not in text and '{}' not in text:
            continue
        # Split on the placeholders FIRST and escape only the literal parts.
        # Escaping the whole string and then substituting does not work: since
        # Python 3.7 re.escape leaves `%` alone, so `\%s` never matches and the
        # eleven measured constraint fields kept reporting as unwired while a
        # builder read every one of them.
        parts = re.split(r'(%s|%d|\{\})', text)
        # A placeholder stands for ONE key segment, so it must not match a dot.
        # Allowing dots made 'B.counts.%s' match D.retail.vacancy_rate and every
        # other field, which silently emptied the unwired list - a checker that
        # passes because its pattern is too greedy is worse than no checker.
        body = ''.join(r'\w+' if p in ('%s', '{}')
                       else (r'\d+' if p == '%d' else re.escape(p))
                       for p in parts)
        try:
            out.append(re.compile('^' + body + '$'))
        except re.error:
            continue
    return out


def schema_referenced_keys():
    """Field keys named by the portable config schema rather than by code.

    `RUN.replanning.subpopulations` is read through the `repeat_over` clause of
    config/schema/param_config.json - the emitter never spells the key in
    Python. A field wired through a declaration is wired.
    """
    found = set()
    path = os.path.join(REPO, 'config', 'schema', 'param_config.json')
    if not os.path.exists(path):
        return found

    def walk(node):
        if isinstance(node, dict):
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)
        elif isinstance(node, str):
            found.add(node)
    walk(json.load(io.open(path, encoding='utf-8')))
    return found


def identity_referenced_keys(fields):
    """Field keys named inside another field's `derived_from` identity.

    A field that is an INPUT to a declared identity participates in the model
    through that identity. `C.vot.trip_weighted` is the trip-weighted value of
    time: nothing spells its key, and three computed scoring fields name it as
    the quantity they are derived from.
    """
    found = set()
    for f in fields.values():
        if not isinstance(f, dict):
            continue
        found.update((f.get('derived_from') or {}).get('fields') or [])
    return found


def descriptor_referenced_keys():
    """Field keys the city DESCRIPTOR names in its `unobtained` block.

    check_city.py and the package checks read those keys through the
    descriptor rather than spelling them in Python (issue #62 B4: the
    unobtained list is the city's declaration, not a framework constant) - so
    a key named there is wired through a declaration, exactly as
    schema_referenced_keys() treats param_config.json.
    """
    return {u.get('field') for u in _city.descriptor().get('unobtained', [])
            if u.get('field')}


# --------------------------------------------------------------------------
# Fields DECLARED AHEAD OF THE CODE THAT WILL CONSUME THEM, each named against
# the phase or issue that will wire it.
#
# An unwired field is not a hardcoded value - it is the opposite - but the
# handover brief is right that it is still a defect: "a declared field that
# nothing reads is worse than no field, because it looks like the model is
# configurable when it is not". The cure is not to hide it. It is to say WHEN
# it becomes real, so an entry here is a commitment with an owner rather than a
# tolerated gap, and a NEW unwired field with no entry fails the gate.
# --------------------------------------------------------------------------
PENDING_CONSUMER = {
    'B.activity.weekend_to_weekday':
        'measured from the RMS hourly counts, which carry dates. Deliverable '
        '0b folds it into the day-type shape; nothing reads it until the SAT '
        'and SUN demand is rebuilt on it',
    'B.counts.vehicles_per_car_leg':
        'issue #20. Converts modelled legs to vehicles for comparison against '
        'observed counts, and count-based calibration is blocked until the '
        'boundary through traffic lands - calibrate.py enforces that',
    'B.counts.vehicles_per_ride_leg':
        'issue #20, the ride half of the same conversion',
    'C.constraint.passenger_per_driver':
        'issue #31. It bounds how many passengers one driver may carry, and '
        'the constraint that would enforce it is not adopted: eqasim\'s '
        'PassengerConstraint is a trip-level biconditional that consults no '
        'driver, and adopting it would pin the ride share to the B2 seed',
    # D.retail.vacancy_rate left this register when the descriptor's
    # unobtained block became the wiring route (issue #62 B4): it is declared
    # unobtained in city.json exactly as the SCATS phasing and journey-linked
    # Opal are, and carries the same handling - swept, never pinned. Nothing
    # consumes it before P6 (hypothesis B2), which its DECISIONS record states.
}

TOOL_BINDINGS = ('matsim_param',
                 'pt2matsim_osm_param', 'pt2matsim_mapper_param')

# --------------------------------------------------------------------------
# Numbers that are NOT model values, each with the reason it stays in code.
#
# This is the same device as `check_legacy_drift.EXPECTED_DIVERGENCE`: a
# deliberate exception is recorded in a file under version control, with a
# written justification, rather than silently filtered. An entry here is a
# claim - "this number decides nothing about the transport system" - and it is
# reviewable precisely because it had to be written down.
#
# Keyed by "path:SYMBOL", with a city's own directory written `<city>/` so this
# framework file does not name a place. A MODEL VALUE MUST NEVER BE ADDED HERE:
# if you cannot state why a number is not a modelling choice in one sentence,
# it is one.
# --------------------------------------------------------------------------
STRUCTURAL = {
    # A PROCESS-SIZE CLASSIFIER, not a model value. `bootstrap_toolchain`
    # refuses to recompile `.tools/classes` while an arm is up (#66, and the
    # rule had nothing behind it until 9 Sep 2026), and it tells an arm from
    # VS Code's language server by resident size: an arm sits in the tens of
    # GB, the language server under one. Nothing about this city or any other
    # decides it, it cannot be swept, and a different city would use the same
    # number. Since 12 Sep 2026 it is named ONCE, in `src/run/procs.py`, and
    # `session_gate` and `bootstrap_toolchain` both import it - the inlined
    # copy that was invisible here is gone.
    # THE TASK SCHEDULER'S OWN ENUMERATION (sixteenth report): TASK_STATE
    # Running is 4 on every Windows, and the proof an arm was launched by
    # its own task reads the number because the word `schtasks` prints for
    # it is localised. An operating-system constant, not a model value.
    'run.py:TASK_STATE_RUNNING':
        'the Task Scheduler\'s TASK_STATE value for Running, read in place '
        'of the localised status word; an operating-system enumeration, '
        'not a parameter of the model',
    'src/run/procs.py:ARM_RSS_KB':
        'the resident-size threshold that tells a running arm from the java '
        'process an IDE keeps alive, in KB. A classifier over '
        'operating-system processes, not a parameter of the model',
    'src/run/procs.py:arm_running(timeout)':
        'how long the process list is waited for, in seconds. An operating-'
        'system call\'s patience; nothing here reaches the model',
    # THE DOCUMENT TOOLS AND THE WATCHER (9.176) hold no model value: a cap
    # on a page's history list, a liveness window over a log file, and how
    # often a watcher polls. Nothing here reaches a run or a reading.
    'src/analyse/positions.py:HISTORY_CAP':
        'how many History entries a position page keeps, the same cap the '
        'handoff skill states; a document convention, not a model value',
    'src/analyse/positions.py:STALE_SECTIONS':
        'how many record sections a position page may trail the record by '
        'before the handoff check calls it stale; a document convention',
    'src/analyse/build_status_board.py:head_sha(short)':
        'how many characters of a git commit sha the board prints; a display '
        'width over a hash, not a model value',
    'src/registry/check_city.py:PROSE_WORDS':
        'the word count above which a string literal in a city script is '
        'read as prose (a label, a message) rather than a value a script '
        'decides by; a classifier over SOURCE TEXT in a check that reaches '
        'no build, no run and no target',
    'run.py:TASK_STATE_RUNNING':
        'the Windows Task Scheduler state code for a running task (4), read '
        'back from schtasks; the operating system\'s enum, not a model value',
    '<city>/build/adopt_framework_fields.py:OVERRIDES':
        'the second city\'s own declared facts, written INTO its registry '
        'files by the adopt script with source, sweep and description: the '
        'declaration itself, which the audit excludes under registry/, not a '
        'twin of one',
    'src/run/run_failure.py:LOG_FRESH_S':
        'how recently matsim.log must have been written for its JVM to count '
        'as alive when its harness is dead, in seconds - five MemoryObserver '
        'heartbeats; a process-liveness window, not a model value',
    'src/run/watch_run.py:--poll':
        'how often the watcher re-reads the run directory, in seconds; the '
        'watcher reads, it decides nothing',
    'src/run/watch_run.py:--heartbeat':
        'how often the watcher prints its one-line state unprompted, in '
        'seconds, 0 for never; a display cadence',
    # A MEMORY BOUND OF A READER, not a model value (ninth report, 14 Sep
    # 2026, finding 23): how many iteration tables one process keeps parsed.
    # It changes what the gate watcher's process holds in memory and nothing
    # any reading computes - the same rows come back from disk either way.
    'src/analyse/iteration_reading.py:CACHE_TABLES':
        'the number of parsed iteration tables a reader process keeps; a '
        'cache bound over process memory, not a parameter of the model',
    # Surfaced when the scanner was widened past module level (7 Sep 2026): a
    # constant assigned inside a function had never been visible to this check.
    # The Earth's mean radius is a physical constant, not a modelling choice -
    # it cannot be swept, and a city cannot declare a different one. Five
    # copies became one on 16 September 2026 (src/build/geo.py, 9.177).
    'src/build/geo.py:EARTH_RADIUS_M':
        'the Earth\'s mean radius in metres, inside the one haversine every '
        'builder imports. A physical constant of the planet, not a parameter '
        'of this model',
    '<city>/build/build_corridor_road_attributes.py:CELL':
        'the cell size of a grid INDEX over alignment points, in metres. It '
        'decides how many candidates a nearest-point search examines, never '
        'which point is nearest - the answer is identical at any cell size, '
        'only the speed changes',
    '<city>/extract/audit_source_use.py:GLOB_FIXED_CHARS_MIN':
        'the fewest fixed characters a string literal needs before the '
        'data-use ledger reads it as naming one family of raw files (`*.json` '
        'names everything and nothing): string-matching structure of an audit '
        'that reads the package and reaches no build, no run and no target',
    'src/analyse/mode_by_demographics.py:KM_EDGES':
        'a reporting grid (9.219): the trip-distance bands travel surveys '
        'publish trips in, so a modelled cell can be set beside a survey cell. '
        'It bins a finished run\'s trips for reading and reaches no build, no '
        'run and no target',
    'src/analyse/run_view.py:RAMP_MIN':
        'a display scale: the narrowest and widest a congestion ramp is drawn. '
        'The live view reads the run and never writes to it, so no number here '
        'can reach a result',
    'src/analyse/run_view.py:RAMP_MAX':
        'the other end of the same display scale',
    'src/analyse/run_view.py:STEP_TOLERANCE_S':
        'the qsim one-second step, which the congestion display does not '
        'count as delay: a property of the mobsim clock, read by the viewer '
        'alone, reaching no run',
    'src/analyse/run_view.py:MIN_STRETCH_M':
        'the shortest stretch of road a congestion colour describes (a map '
        'app segment, never a 10 m turn stub) - the same display scale as '
        'RAMP_MIN, reaching no run',
    'src/analyse/run_view.py:MODES_CACHE_ENTRIES':
        'how many computed readings the viewer keeps in memory. An observer '
        'cache bound: it decides what the page remembers, never what a run '
        'produces',
    'src/analyse/run_view.py:NET_CACHE_ENTRIES':
        'how many run networks the viewer keeps decoded in memory (~130 MB '
        'each). The same observer cache bound',
    'src/analyse/run_view.py:_send(code)':
        'an HTTP status code. The default 200 is the HTTP specification, not a '
        'transport parameter',
    'src/analyse/arm_cost.py:observed_arms(min_iterations)':
        'how many iterations a run must have reached before its median is '
        'quoted as a pace. A property of the ARITHMETIC - a median over one '
        'iteration is the warm-up - not of the transport system; the script '
        'reads finished run records and cannot reach a result',
    'src/run/verify_launch.py:_tail(limit)':
        'how many bytes are read from the END of a matsim.log to decide '
        'whether the launch reached an iteration. A bound on the READ, not on '
        'the model: a growing arm log reaches tens of GB and this script must '
        'never read one whole (9.155). It answers one operational question '
        'about a log already written and can reach no result',
    'src/run/verify_launch.py:--timeout':
        'how long the launch verifier waits for the first iteration before it '
        'reports UNDECIDED. Operational patience, not a transport parameter; '
        'the default is set above the 7 min startup measured in 9.154 so a '
        'healthy launch is never called dead',
    'src/run/verify_launch.py:--poll':
        'how often the launch verifier re-reads the log while waiting. It '
        'observes a run that is running anyway and writes nothing',
    'src/run/issue_gate.py:MIN_EVIDENCE_CHARS':
        'how much text after "AWAITING-RUN:" on a GitHub issue counts as a '
        'stated measurement rather than the label written out again. A '
        'threshold on PROSE IN THE TRACKER, not on anything the model reads: '
        'the gate refuses a launch, and no value here can reach a run, a '
        'config or a result',
    'src/analyse/profile_run.py:table(width)':
        'the column width of a printed table',
    'src/analyse/profile_run.py:--top':
        'how many rows of each profile table are printed. A reading of a '
        'flight recording; nothing here reaches the model',
    'src/analyse/profile_run.py:--depth':
        'how many stack frames are read from each sample. Deeper costs time '
        'and finds the same phase root; it changes what the READER sees of a '
        'recording that is already written, never the run',
    'src/analyse/replay_events.py:--step':
        'replay animation step in seconds - how often the REPLAY PAGE redraws a '
        'finished run. It reads events already written and changes nothing',
    'src/analyse/replay_events.py:--keep-every':
        'replay decimation, for page size only',
    'src/analyse/replay_events.py:--horizon-h':
        'how much of the simulated day the replay page draws. The day window '
        'itself is RUN.qsim.end_time_h, which IS declared',
    'src/analyse/replay_events.py:--net-sample':
        'how many network links the replay page draws, for page size only',
    'src/calibrate/report.py:pct(nd)':
        'decimal places in a printed percentage',
    'src/build/build_data_dictionary.py:sniff(n)':
        'how many rows of a CSV are read to infer its column types. A property '
        'of the file reader, not of the data',
    'src/build/det_io.py:gzip_writer(compresslevel)':
        'gzip compression level. FIXED FOR DETERMINISM rather than chosen for a '
        'model reason: the level changes the bytes, so it is pinned and must '
        'not vary. It affects file size, never content',
    '<city>/extract/reader_shapes.py:LF_BANDS':
        'the ABS G46 table\'s own age banding, read off its published column '
        'names (15_19 .. 85ov). A property of the census file being read, not '
        'a choice: the model\'s own banding is B.population.age_bands',
    '<city>/extract/reader_shapes.py:EDU_GROUPS':
        'the ABS G01 education-attendance age groups, likewise the table\'s '
        'own published column structure',
    '<city>/extract/reader_shapes.py:G04_GROUPED':
        'the ABS G04 grouped age columns (80_84 .. 95_99) that exist because '
        'G04 stops publishing single years at 79 - the file\'s structure, and '
        'exactly what the pre-9.46 build failed to read. The three moved from '
        'build_population.py into the city reader adapter with the census '
        'family (9.140, #62): the banding of the tables belongs to the city',
    'src/build/measure_osm_defaults.py:MIN_TAGGED':
        'the minimum tagged-edge count before an observed class median replaces '
        'an assumed default. It governs HOW A MEASUREMENT IS TAKEN, not what '
        'the model consumes - the values it produces are what enter the '
        'registry, each with its own observed sweep. The reasoning is written '
        'above the constant',
    'src/build/build_matsim_network.py:--workers':
        'process count for the OSM merge. Throughput only - unlike '
        'RUN.machine.threads, which partitions the mobsim network and IS part '
        'of a run identity',
    'src/build/build_matsim_network.py:--threads':
        'a build-time override for the mapper thread count, which otherwise '
        'comes from RUN.machine.threads',
    'src/build/build_matsim_run_inputs.py:nearest_stop_reach_m(cell_m)':
        'the bucket size of the nearest-stop search. The ring search is exact '
        'at any bucket size; this decides only how many stops are compared',
    'src/run/run_matsim.py:_log_tail(nbytes)':
        'how much of a finished run\'s matsim.log is read from its end to '
        'find the newest ITERATION ENDS marker (2 MB against a log that can '
        'reach 55 GB). A read window on text READ OUT of a run; it decides '
        'nothing about the transport system and the whole log stays where '
        'it is',
    'src/run/run_failure.py:MESSAGE_CHARS':
        'how much of a Java exception message is quoted into a dead run\'s '
        '`cause` before it is elided. A display length on text READ OUT of a '
        'finished run\'s log; it decides nothing about the transport system, '
        'and the full message stays in matsim.log at the line the record names',
    'src/analyse/build_fit_figures.py:LAYOUT':
        'page geometry for the fit figures - margins, gutters, bar heights and '
        'font sizes, in SVG user units. The generator READS a finished run and '
        'draws it; the same class as run_view.py:RAMP_MIN. No number here can '
        'reach a model, an input or a result, and every VALUE in the pictures '
        'comes from the run\'s own _fit.json',
    'src/analyse/progress_digest.py:REPLACE_ATTEMPTS':
        'atomic-replace retry count on a Windows directory lock - I/O '
        'mechanics, the RunTelemetry.MOVE_ATTEMPTS discipline, not a model '
        'value',
    'src/analyse/progress_digest.py:REPLACE_BACKOFF_S':
        'the backoff between those retries. Same class as REPLACE_ATTEMPTS',
    'src/registry/param_config.py:SECONDS_PER_UNIT':
        'how many seconds are in an hour and a minute. The definition of the '
        'units themselves, not a value about any city',
    '<city>/build/build_scenario_schedules.py:'
    'scale_lr_runtime(delta_per_intermediate_s)':
        'a NEUTRAL default of zero: "change nothing unless a caller asks". Each '
        'caller passes the scenario delta it means, and those deltas are '
        'declared (E.s2b.signal_delay_removed_share and its siblings)',
    '<city>/build/build_scenario_schedules.py:'
    'scale_lr_runtime(delta_per_segment_s)':
        'the other neutral zero of the same function',
    # THE SECOND CITY'S SOURCE STRUCTURE (sixteenth report): the published
    # tables' own pages, columns, bands and dates, restated so a reader can
    # find and expand them. Each is the shape of a file being read, not a
    # modelling choice - the same class as the ABS bands in reader_shapes.py.
    '<city>/build/build_plans.py:BANDS':
        'the Census of India work-distance bands (0-1 km .. 51+ km) as the '
        'B-28 table publishes them; a worker is drawn into the band the '
        'census put it in, and the band edges are the table\'s own',
    '<city>/build/build_population.py:SIZE_BANDS':
        'the census household-size columns (1 .. 9+) with the size each '
        'column spans; the table\'s own column structure',
    '<city>/extract/extract_bmc_population_estimates.py:DIARIES':
        'the page of each civic diary a population estimate is read from and '
        'the year it states; where a figure sits in a published document',
    '<city>/extract/extract_bmc_signal_inventory.py:PAGES':
        'the pages of the signal inventory PDF and the serial range each page '
        'carries; the document\'s own pagination',
    '<city>/extract/extract_bmc_signal_inventory.py:COLUMNS':
        'column boundaries of the same PDF table in points; where a cell sits '
        'on the page, never a coordinate on the ground',
    '<city>/extract/extract_navi_metro_controls.py:add(page)':
        'the page of the operating report a control figure is cited from',
    '<city>/extract/extract_population_projections.py:ANNUAL':
        'the page and table numbers of each projection series in the '
        'published report, with the series\' own labels',
    '<city>/extract/harvest.py:FIXED_TIME':
        'the fixed zip entry timestamp (1980-01-01) every harvest archive '
        'carries so that two harvests of the same bytes hash the same; the '
        'determinism rule itself, the same class as det_io.zip_entry',
    '<city>/extract/harvest.py:pack(pause_seconds)':
        'the pause between two fetches from one host, in seconds; '
        'acquisition courtesy, and the bytes retrieved are the same at any '
        'value',
    '<city>/extract/acquire_mbmt_sources.py:--pause-seconds':
        'the same fetch pacing, as a command-line default',
    '<city>/extract/acquire_nmmt_paths.py:--pause-seconds':
        'the same fetch pacing',
    '<city>/extract/acquire_nmmt_route_stops.py:--pause-seconds':
        'the same fetch pacing',
    '<city>/extract/acquire_nmmt_schedules.py:--pause-seconds':
        'the same fetch pacing',
    '<city>/extract/acquire_nmmt_vehicle_details.py:--pause-seconds':
        'the same fetch pacing',
}


def is_bound(field):
    """Does this field reach a tool through a declared parameter binding?

    A bound field does NOT need its key to appear in code: that is the point of
    building the config from the registry instead of substituting into a
    template. Its reach is decided by the perturbation probe - moving the value
    and watching the emitted config move - which is a stronger test than any
    text search, and it is reported separately as question 6.
    """
    return any(field.get(b) for b in TOOL_BINDINGS)


def unwired(fields, uses):
    """An UNBOUND field no source file names as data at all.

    Two routes to the model, so two tests. A field with a parameter binding is
    written into a tool's config by the emitter and is tested by moving it. A
    field without one has to be read by name somewhere, and if its key appears
    nowhere as a value then nothing can be reading it.

    A USE INSIDE `tests/` IS NOT A USE, with one named exception. `sources()`
    walks the test tree so that a test may not hide a hardcoded number either,
    but a key named only by a unit-test FIXTURE reaches no model: the fixture is
    the thing being checked, not a consumer. Counting it wired is how a field
    that nothing reads can sit in the registry looking consumed.

    The exception is `tests/check_package.py`, which is not a unit test but the
    PACKAGE CONTRACT: it reads declared values to decide what the built package
    must contain (which scenarios must exist, what a mode's minimum trip time
    is). A field it reads is doing work - the same role the measurement layer
    plays for `MEASUREMENT_OWNED_KEYS` - so it counts, and it is named here
    rather than the whole tree being excused.
    """
    def model_uses(k):
        return {f for f in uses.get(k, ())
                if not is_test(f) or f in VALIDATION_CONSUMERS}

    return [(k, fields[k].get('source'), fields[k].get('status'))
            for k in sorted(fields)
            if isinstance(fields[k], dict) and not is_bound(fields[k])
            and not model_uses(k) and k not in PENDING_CONSUMER]


def pending(fields, uses):
    """Unwired fields that carry a written reason and the phase that will wire them."""
    return [(k, PENDING_CONSUMER[k]) for k in sorted(PENDING_CONSUMER)
            if k in fields and k not in uses and not is_bound(fields[k])]


def stale_pending(fields, uses):
    """A PENDING_CONSUMER entry for a field that is now wired, or is gone.

    The register is a promise that something will read the field. When it does,
    the promise is kept and the entry must go - otherwise the list grows into a
    permanent excuse, which is what any allowlist becomes if nothing prunes it.

    The register is one over every city. A field this city never declared is
    not "gone" while another city declares it: under the second city the four
    entries read as kept promises to prune, for fields that city has no use
    for (sixteenth report).
    """
    return sorted(k for k in PENDING_CONSUMER
                  if (k not in fields and not _declared_in_any_city(k))
                  or (k in fields and (k in uses or is_bound(fields[k]))))


_FIELDS_BY_CITY = {}


def _declared_in_any_city(key):
    """Whether any city under cities/ declares `key`."""
    for name in _city.available():
        if name not in _FIELDS_BY_CITY:
            try:
                _FIELDS_BY_CITY[name] = _registry.load_registry(
                    os.path.join(_city.CITIES_DIR, name, 'registry'))[0]
            except Exception:                             # noqa: BLE001
                _FIELDS_BY_CITY[name] = {}
        if key in _FIELDS_BY_CITY[name]:
            return True
    return False


# Layers whose fields BELONG to the measurement apparatus: how the calibration
# loop searches, how the live view polls, how flat a mode-share trace must be
# before a run is called settled. A field here being read only by src/analyse or
# src/calibrate is correct, not a defect - so it is reported for visibility and
# not counted against the gate. Anything else read only there is printed back
# after a run while deciding nothing, which is the trap.
MEASUREMENT_OWNED_PREFIXES = ('CAL.', 'RUN.monitor.', 'RUN.relaxation.')

# Individual fields that belong to the measurement apparatus without sharing a
# prefix with it. Each states why.
MEASUREMENT_OWNED_KEYS = {
    'B.counts.station_match_radius_m':
        'the radius that joins an observed traffic count station to a network '
        'link. It decides what the VALIDATION compares, never what the model '
        'simulates, so being read only by src/analyse is correct',
    'B.taxi.daily_trips_band':
        'a CONSTRAINT, never a target (9.8/9.13, 9.76): the modelled taxi '
        'volume is REPORTED against this band and nothing is fitted to it - '
        'being read only by the measurement layer is the field\'s entire '
        'design, the same class as the C4 occupancy constraint',
    'B.census.thin_cell_min_journeys':
        'the reporting flag that marks an observed census cell too thin to '
        'constrain anything (issue #50, 9.77). It decides how a comparison '
        'is LABELLED, never what the model simulates, so being read only by '
        'src/analyse is correct',
}


def report_only(fields, uses):
    """A field only the measurement layer reads: printed back, never applied.

    Returns (defects, owned). A bound field is excluded from both: it reaches its
    tool through the binding, so where its key happens to be spelled in code
    says nothing about whether it decides anything - the perturbation probe
    answers that, and answers it better.
    """
    defects, owned = [], []
    for key in sorted(uses):
        if is_bound(fields[key]):
            continue
        where = {p for p in uses[key] if not is_test(p)}
        if not where or not all(is_measurement(p) for p in where):
            continue
        row = (key, fields[key].get('source'), sorted(where))
        if key.startswith(MEASUREMENT_OWNED_PREFIXES) or key in MEASUREMENT_OWNED_KEYS:
            owned.append(row)
        else:
            defects.append(row)
    return defects, owned


# --------------------------------------------------------------------------
# 3. config template literals
# --------------------------------------------------------------------------
def template_literals(corpus):
    """<param name="X" value="Y"> where Y is a constant, not a {substitution}."""
    param = re.compile(r'<param name="([^"]+)" value="([^"]*)"')
    out = []
    for p, text in sorted(corpus.items()):
        r = rel(p)
        if not p.endswith('.py') or r in SELF_REFERENTIAL or is_test(r):
            continue
        for m in param.finditer(text):
            name, val = m.group(1), m.group(2)
            # Both substitution styles count as WRITTEN FROM SOMEWHERE ELSE:
            # `{x}` for str.format and `%s` for printf. Whether that somewhere
            # is the resolver or a Python default is what question 4 answers.
            if '{' in val or '%' in val:
                continue
            line_no = text[:m.start()].count('\n') + 1
            lines = text.splitlines()
            # A REGEX that MATCHES a <param> is not a <param>. `setp` and
            # `set_mode_param` in the harness search for a parameter by name so
            # they can rewrite it; reporting their patterns as hardcoded values
            # is how an audit teaches people to skim past it. A window rather
            # than the one line, because a pattern is often built over several.
            window = '\n'.join(lines[max(0, line_no - 1 - REGEX_WINDOW):
                                     line_no + REGEX_WINDOW])
            if any(fn in window for fn in ('re.sub(', 're.subn(', 're.compile(',
                                           're.search(', 're.match(',
                                           're.finditer(', 're.findall(')):
                continue
            out.append((r, line_no, name, val))
    return out


# Inline literals that are structure, not modelling values (#188), keyed
# `<file>:<function>:<value>`. Every entry says why. A value that decides the
# demand, the network or a target is NOT entered here - it is declared.
_TOL = ('a DRIFT TOLERANCE between a declared value and the observation it restates: '
        'the build refuses when the two differ by more than this, and any value that is '
        'small against the quantity gives the same refusals')
_HASH = ('a HASH WIDTH: the number of hex digits or bits of a seeded sha256 digest read as '
         'a uniform draw; identical draws at any width above ~40 bits, no modelling content')
_RETRY = ('an ACQUISITION retry/backoff/page size for an HTTP download; the bytes '
          'retrieved are the same at any value that succeeds')
STRUCTURAL_INLINE = {
    # ---- solver and arithmetic structure
    'src/build/shape_tools.py:project_onto:1e-18':
        'a division guard for a zero-length segment; any value far below a '
        'squared metre gives the same projection',
    'src/build/build_gtfs_extras.py:_pairs_within:0.1':
        'a floor on cos(latitude) so a grid cell never divides by zero near a '
        'pole; never reached at this latitude (cos 33 deg = 0.84)',
    'src/build/build_population.py:main:0.0001':
        'a zone-area floor (km2) under the home jitter radius so a zero-area '
        'zone does not divide by zero; 100 m2 is below any SA1',
    '<city>/build/build_licence_rates.py:erp_single_years:99':
        'the last single year the ABS ERP table publishes (100 and over is '
        'one open band); the SHAPE of the source table, not a choice',
    '<city>/extract/overpass.py:_get:120':
        _RETRY,
    'src/build/build_activity_chains.py:_solve_decay:0.5':
        'the MIDPOINT of a bisection over the gravity decay; solver structure',
    'src/build/build_activity_chains.py:_solve_short_decay:0.5':
        'the midpoint of the short-trip decay bisection - as above',
    'src/build/build_activity_chains.py:through_agents:0.5':
        'a through flow is split into its two directions; half each is the '
        'definition of a symmetric flow, not a choice',
    'src/build/build_population.py:_age_sex_draw_shares:0.5':
        'the sex split of an age band the census leaves EMPTY (no persons); an '
        'even split of nobody, never reached on this city',
    '<city>/build/build_corridor_layers.py:corridor_signal_rows:0.5':
        'half a cycle: the mean delay of an arrival uniform over the cycle, '
        'the textbook identity, not a value',
    '<city>/build/build_landuse_parking.py:build_frontages:0.5':
        'the midpoint of a frontage segment (shapely interpolate at half length)',
    '<city>/build/build_level_crossings.py:closure_spans:0.5':
        'the centre of a window slot (i + 0.5): even spacing of the derived '
        'closures inside their window, geometry rather than a value',
    '<city>/build/build_mode_targets.py:road_person_targets:0.5':
        'the midpoint of the IPART trips-per-day band (lo + hi) / 2 - the band is '
        'the declared value, B.taxi.daily_trips_band',
    '<city>/build/build_mode_targets.py:tpa_ferry_weekday_boardings:0.5':
        'the midpoint of a published day\'s tap-on interval (lower + upper) / 2 - '
        'the interval is the disclosed value, its hourly cells rounded to 100 (D8)',
    '<city>/extract/extract_bitre_registrations.py:study_area_postcodes:0.5':
        'a postcode is inside the study area when more than half of it is - a '
        'majority rule for a boundary clip',
    '<city>/extract/extract_boam.py:main:0.5':
        'a depot is kept when more than half of its sightings vote for it - a '
        'majority rule',
    'src/build/build_activity_chains.py:_solve_decay:0.005':
        'the LOWER BRACKET of a bisection over the gravity decay; the solution is '
        'interior and identical for any bracket that contains it',
    'src/build/build_activity_chains.py:_solve_short_decay:0.005':
        'the lower bracket of the short-trip decay bisection - as above',
    'src/build/build_activity_chains.py:calibrate_one:0.8':
        'a FLOOR on the long-trip target mean (0.8 km beeline) that keeps the '
        'solver off a degenerate target; never binding on this city\'s observed means',
    'src/build/build_activity_chains.py:_decay_by_lga:0.8':
        'the same floor on the per-LGA long-trip target, applied where the decay '
        'is solved per home LGA',
    'src/build/build_activity_chains.py:_fit_short_mix:0.8':
        'the same floor on the long-trip target left after the short-trip mixture',
    'src/build/build_activity_chains.py:draw_hour:23':
        'the last hour of the day, in the hour-of-day wraparound',
    'src/build/build_activity_chains.py:__init__:20':
        'a buffer size (1 << 20 draws) for the seeded random stream',
    'src/build/build_activity_chains.py:sample_unit_hash:8':
        _HASH,
    'src/build/build_activity_chains.py:sample_unit_hash:64':
        _HASH,
    'src/build/build_activity_chains.py:bind_joint_tours:984':
        'a seed-stream SALT that separates this pass\'s draws from every other '
        'pass seeded from the same registry seed; any constant does the same',
    'src/build/build_activity_chains.py:cordon_nodes:64':
        'a chunk size for a vectorised distance computation',
    'src/build/build_activity_chains.py:<module>:0.0005':
        _TOL,
    'src/build/build_matsim_plans.py:truck_user:48':
        _HASH,
    'src/build/build_matsim_plans.py:motorbike_user:48':
        _HASH,
    'src/build/build_matsim_plans.py:write_day:20':
        'a buffer size (1 << 20 draws) for the seeded random stream',
    'src/build/build_matsim_plans.py:u:20':
        'the same buffer size, refilled',
    'src/build/build_matsim_plans.py:thin_carve_cells:0.05':
        _TOL,
    'src/build/build_matsim_run_inputs.py:stamp:0.05':
        'a REPORTING bin: a grade within 0.05 % of flat is counted as flat in the '
        'run-inputs report; the link carries its exact grade regardless',
    'src/build/build_population.py:main:6':
        'the lower bound of the census "6 or more persons" band, which is the '
        'band\'s own definition; its mean and tail are declared fields',
    'src/build/attach_gradient.py:sample:400':
        'a DEM plausibility bound: an elevation below -400 m is a nodata artefact '
        '(the continent\'s lowest point is -15 m); any bound between -15 and the '
        'raster\'s nodata value gives the same result',
    'src/build/attach_gradient.py:sample:3000':
        'a DEM plausibility bound: above 3,000 m is an artefact (the continent\'s '
        'highest point is 2,228 m)',
    'src/build/measure_network_factors.py:measure_day_type:0.2':
        'a plausibility bound on a station-year weekend/weekday ratio (below 0.2 is '
        'a counter outage); the measured median is insensitive to it',
    'src/build/measure_osm_defaults.py:_lane_widths:1.5':
        'a plausibility bound on an OSM width tag per lane (below 1.5 m is a tag '
        'recorded for something else); a filter on the measurement, not a value',
    'src/build/measure_osm_defaults.py:_lane_widths:6':
        'the upper plausibility bound of the same filter',
    'src/build/shape_tools.py:_build:200':
        'a spatial grid resolution (cells per degree) for a nearest-node index; the '
        'nearest node is the same at any resolution',
    'src/build/shape_tools.py:nearest_node:200':
        'the same grid resolution, at lookup',
    # ---- output formatting and file structure
    'src/build/build_data_dictionary.py:sniff:400':
        'how many rows are sampled to infer a column type in the data dictionary',
    'src/build/build_data_dictionary.py:<module>:92':
        'a column width in the rendered dictionary',
    'src/build/build_data_dictionary.py:<module>:34':
        'a column width in the rendered dictionary',
    'src/build/build_data_dictionary.py:<module>:124':
        'a column width in the rendered dictionary',
    'src/build/build_manifest.py:sha256:20':
        'a read chunk size (1 << 20 bytes) while hashing',
    'src/build/build_matsim_network.py:_sha256:20':
        'a read chunk size (1 << 20 bytes) while hashing the OSM inputs the merge is keyed on',
    'src/build/build_manifest.py:main:30':
        'a column width in the printed manifest summary',
    'src/build/det_io.py:gzip_writer:6':
        'the gzip compression level of every deterministic writer; bytes differ, '
        'content does not',
    'src/build/det_io.py:zip_entry:16':
        'the bit shift that places POSIX permission bits in a zip entry header',
    'src/build/det_io.py:zip_entry:420':
        'POSIX permissions 0o644 in the zip entry header',
    # ---- the city's own scripts
    '<city>/build/build_corridor_layers.py:corridor_signal_clusters:45':
        'a JOIN TOLERANCE: OSM places one signal node per approach, and nodes within '
        '45 m are one intersection; a whole intersection spans 30-60 m and the '
        'nearest other one on the corridor is hundreds of metres away, so any value '
        'in that gap clusters identically',
    '<city>/build/build_corridor_road_attributes.py:build:200':
        'a search margin (metres) added to the declared parallel buffer when '
        'measuring a way\'s distance to the alignment; the distance is the same '
        'at any margin that contains the answer',
    '<city>/build/build_corridor_road_attributes.py:build:40':
        'a REPORTING band: turn restrictions within 40 m of the alignment are '
        'counted in the build report',
    '<city>/build/build_corridor_road_attributes.py:build:80':
        'a reporting band (80 m) in the same report',
    '<city>/build/build_corridor_road_attributes.py:build:300':
        'a reporting band (300 m) in the same report',
    '<city>/build/build_era1_reconstruction.py:main:50':
        'a JOIN TOLERANCE: the reconstruction is already at a closed station when '
        'within 50 m of its position',
    '<city>/build/build_era1_reconstruction.py:main:8':
        'how many truncation termini the build report lists',
    '<city>/build/build_external_interaction.py:main:0.0005':
        _TOL,
    '<city>/build/build_licence_rates.py:erp_single_years:120':
        'the upper age of an open-ended "85 and over" band when it is expanded to '
        'single years; nobody in the ERP is older',
    '<city>/build/build_licence_rates.py:assert_declared:5e-05':
        _TOL,
    '<city>/build/build_motorcycle_possession.py:main:5e-05':
        _TOL,
    '<city>/build/build_mode_targets.py:road_person_targets:5e-05':
        _TOL,
    '<city>/build/build_validation_targets.py:pt_targets:30.4':
        'the mean number of days in a month (365 / 12), converting a monthly '
        'publication to a daily one',
    '<city>/extract/extract_speed_zones.py:sha256:20':
        'a read chunk size (1 << 20 bytes) while hashing',
    '<city>/extract/fetch_with_provenance.py:sha256:20':
        'a read chunk size (1 << 20 bytes) while hashing, in the one fetch '
        'helper the reference city\'s fetchers share (sixteenth report)',
    '<city>/extract/fetch_with_provenance.py:download:20':
        'the same chunk size while downloading',
    '<city>/extract/fetch_abs_dem.py:main:1800':
        'an HTTP timeout (seconds) for a 30 m DEM tile; the bytes retrieved '
        'are the same at any value that succeeds',
    '<city>/extract/fetch_licences.py:main:600':
        'an HTTP timeout (seconds) for the licence tables; as above',
    '<city>/extract/fetch_licences.py:main:500':
        'a VERIFICATION threshold on a downloaded file\'s byte size (below '
        '500 bytes a response is an error page, not a table); the download '
        'is unchanged',
    '<city>/extract/fetch_tpa_daily.py:_sha256:20':
        'a read chunk size (1 << 20 bytes) while hashing',
    '<city>/extract/fetch_tpa_daily.py:fetch:20':
        'a read chunk size while downloading',
    '<city>/extract/fetch_open_data.py:main:500':
        'a VERIFICATION threshold on a downloaded file\'s byte size (below '
        '500 bytes a response is an error page); the download is unchanged',
    '<city>/extract/fetch_open_data.py:main:600':
        'an HTTP timeout (seconds); the bytes retrieved are the same at any '
        'value that succeeds',
    '<city>/extract/osm_tiles.py:verify:2000':
        'a VERIFICATION threshold on a tile file\'s byte size (below 2,000 bytes an '
        'Overpass answer is an error page, not a tile); the harvest is unchanged',
    '<city>/extract/osm_tiles.py:verify:0.9':
        'a verification threshold: a tile under 90 %% of its neighbours\' size is '
        're-checked; the harvest is unchanged',
    '<city>/extract/overpass.py:_get:20':
        _RETRY,
    '<city>/extract/overpass.py:_get:15':
        _RETRY,
    '<city>/extract/overpass.py:fetch:20000':
        _RETRY,
    '<city>/extract/overpass.py:fetch:200':
        _RETRY,
    '<city>/extract/overpass.py:write_provenance:20':
        'a read chunk size (1 << 20 bytes) while hashing',
    '<city>/extract/reader_shapes.py:education_groups:25':
        'the lower age of the ABS "25 and over" attendance band - the publication\'s '
        'own band edge, restated so the reader can expand it',
    '<city>/extract/reader_shapes.py:education_groups:200':
        'the open upper age of the same band; nobody is older',
    # ---- surfaced when ALL-CAPS expression values were first visited (#212,
    # sixteenth report): structure that an ALL-CAPS name had hidden
    'src/build/audit_osm_transport_tags.py:<module>:1.60934e+06':
        'a mile in millimetres, in a unit table over OSM tag suffixes; the '
        'definition of the unit',
    'src/build/audit_osm_transport_tags.py:<module>:1852':
        'a nautical mile in metres; the definition of the unit',
    'src/build/audit_osm_transport_tags.py:<module>:3048':
        'a foot in tenths of a millimetre; the definition of the unit',
    'src/build/audit_osm_transport_tags.py:<module>:254':
        'an inch in tenths of a millimetre; the definition of the unit',
    'src/build/audit_osm_transport_tags.py:<module>:10000':
        'the denominator those two definitions are written over',
    'src/build/build_activity_chains.py:external_agents:0.0001':
        'the zone-area floor (km2) under the home jitter radius, the same '
        'guard as build_population.py:main:0.0001',
    'src/build/build_activity_chains.py:freight_agents:0.0001':
        'the same zone-area floor',
    'src/build/build_activity_chains.py:load_supply_inputs:0.0001':
        'the same zone-area floor',
    'src/build/build_data_dictionary.py:<module>:9':
        'the csv module\'s field-size limit (10 ** 9) so a cell holding a '
        'whole OSM relation is read; a reader bound, not a value',
    'src/build/det_io.py:<module>:1980':
        'the earliest year a zip entry timestamp can express, the fixed date '
        'every deterministic archive carries; the format\'s own epoch',
    '<city>/build/build_era_feeds.py:<module>:6':
        'the GTFS calendar column index of Sunday (Monday is 0): which day '
        'column a day type reads, the feed format\'s own order',
    '<city>/extract/rms_hourly.py:<module>:6':
        'ISO weekday 6 (Saturday) in the day-of-week to day-type map the two '
        'count readers share; the ISO 8601 numbering the raw counts carry',
    # ---- the second city's builders (sixteenth report): reviewed one by one
    '<city>/build/build_baseline_transit_feed.py:main:1e+07':
        'the csv module\'s field-size limit while a long shape column is read; '
        'a reader bound, not a value',
    '<city>/build/build_suburban_timetable_feed.py:<module>:9':
        'the same csv field-size limit (10 ** 9)',
    '<city>/build/build_hired_fleet.py:main:0.5':
        'round-half-up of an expected count to a whole vehicle (floor(x + 0.5))',
    '<city>/build/build_plans.py:points_in:64':
        'the smallest batch of candidate points drawn before a polygon is '
        'tested; the points kept are the same at any batch size',
    '<city>/build/build_plans.py:home_polygons:4326':
        'EPSG:4326, the CRS the source polygons are published in; a property '
        'of the file being read, reprojected at once to city.crs()',
    '<city>/build/build_population.py:projected_share:0.999999':
        'a clamp that keeps a published share strictly below one so its '
        'complement never divides by zero',
    '<city>/build/build_population.py:draw_sizes:1.2':
        'an oversampling factor on household-size draws so one pass fills '
        'the person count; the kept draws are seeded and identical at any '
        'factor that suffices',
    '<city>/build/build_mode_targets.py:car_passenger_split:2e+06':
        'a pandas chunk size while a 27 M-row population is read; throughput only',
    '<city>/build/build_plans.py:kept_persons:2e+06':
        'the same chunk size',
    '<city>/build/build_mode_targets.py:derived_rows:100000':
        'one lakh, the unit the published ridership is stated in; a unit '
        'conversion',
    '<city>/build/build_population.py:synthesise_leaves:20':
        'the lower edge of the census 20-24 attendance band, the table\'s '
        'own band',
    '<city>/build/build_population.py:synthesise_leaves:6':
        'the upper edge of the census 0-6 age column, the table\'s own band',
    '<city>/build/build_suburban_timetable_feed.py:assemble_trains:1800':
        'a parsing tolerance over the printed timetable: a stop time more '
        'than 30 min after the previous leg starts a new trip. A property of '
        'how the published table is laid out, not of the service',
    '<city>/build/derive_vehicle_possession_growth.py:main:2015.5':
        'the midpoint of the NFHS-4 fieldwork period (2015-16); the survey\'s '
        'own date',
    '<city>/build/derive_vehicle_possession_growth.py:main:2020':
        'the midpoint of the NFHS-5 fieldwork period (2019-21); the survey\'s '
        'own date',
}


# --------------------------------------------------------------------------
# 4. values decided in code
# --------------------------------------------------------------------------
def stale_structural(corpus):
    """A STRUCTURAL entry naming a symbol that no longer exists.

    An allowlist that outlives what it excuses is how an exception quietly
    becomes a blanket. Each entry is checked against the scanner's own
    findings, so deleting a constant deletes its excuse with it.
    """
    seen = set()
    for p in sorted(corpus):
        r = rel(p)
        if not p.endswith('.py') or r in SELF_REFERENTIAL or is_test(r):
            continue
        try:
            seen |= _symbol_keys(p, portable(r))
        except SyntaxError:
            continue
    return sorted(k for k in STRUCTURAL
                  if k not in seen and not _live_in_reference_city(k, _decision_keys))


def _symbol_keys(path, rp):
    """The register keys a file makes live: every decision the scanner
    reports, and every ALL-CAPS name it assigns - an entry for an ALL-CAPS
    EXPRESSION (a table of registry declarations the inline scan reads
    through, #212) names a symbol that is there even though it is not a
    literal the decision scan reports."""
    keys = {'%s:%s' % (rp, d['name']) for d in _legacy.scan_decisions(path)}
    with io.open(path, encoding='utf-8', errors='replace') as f:
        tree = ast.parse(f.read())
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            keys |= {'%s:%s' % (rp, t.id) for t in node.targets
                     if isinstance(t, ast.Name) and t.id.isupper()}
    return keys


def _decision_keys(text, rp, city_name=None):
    path = os.path.join(_city.REPO, 'cities', city_name or _city.DEFAULT_CITY, rp[len('<city>/'):])
    return _symbol_keys(path, rp)


def script_decisions(corpus, fields):
    pinned = {str(f.get('legacy_symbol', '')).rsplit(':', 1)[-1]
              for f in fields.values()
              if isinstance(f, dict) and f.get('legacy_symbol')}
    out = []
    for p in sorted(corpus):
        r = rel(p)
        if not p.endswith('.py') or r in SELF_REFERENTIAL or is_test(r):
            continue
        try:
            found = _legacy.scan_decisions(p)
        except SyntaxError:
            continue
        for d in found:
            if d['kind'] != 'parameter':
                continue
            if '%s:%s' % (portable(r), d['name']) in STRUCTURAL:
                continue
            if d['name'] in pinned:
                # Pinned to its registry field by `legacy_symbol` and compared
                # with it on every run of check_legacy_drift.py. Two copies of a
                # number, but not two UNCOMPARED copies - which is the thing
                # that bites. Accounted for by a different committed check
                # rather than excused here.
                continue
            out.append((r, d['line'], d['form'], d['name'], d['value'],
                        d['n_numbers']))
    return out


# --------------------------------------------------------------------------
# 5. coordinates
# --------------------------------------------------------------------------
def _numeric_constants(tree):
    """{line: [value, ...]} for every numeric literal, negatives included.

    Read from the AST rather than from the text, so a figure quoted in a comment
    or a docstring - "an observed 1.3503", "lon 151.7767 to 151.7889" - cannot
    be reported as a place. Prose about a coordinate is not a coordinate.
    """
    by_line = {}
    for node in ast.walk(tree):
        value = None
        if isinstance(node, ast.Constant) and isinstance(node.value, float):
            value = node.value
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub) \
                and isinstance(node.operand, ast.Constant) \
                and isinstance(node.operand.value, float):
            value = -node.operand.value
        if value is None:
            continue
        by_line.setdefault(node.lineno, []).append(value)
    return by_line


# --------------------------------------------------------------------------
# 8. Java-side defaults that shadow a declared value
# --------------------------------------------------------------------------
# A MATSim ConfigGroup field is a config parameter when a @StringSetter or a
# @Parameter annotation names it. Its Java initialiser is the value used IF THE CONFIG NEVER SETS IT - so a
# default equal to the declared value is the worst case the handover brief
# names: right by accident, every test passing, and silently wrong the moment
# anyone sweeps the field, because a config that lost the binding would run on
# the Java number and report success.
JAVA_FIELD = re.compile(
    r'(?:private|public)\s+(?:static\s+)?(?:final\s+)?(?:double|int|long|float|boolean|String)\s+'
    r'(\w+)\s*=\s*([^;]+);')
# a parameter is named by a @StringSetter (the getter/setter form) or by a
# @Parameter annotation on a public field (the field form, since #180 - the
# pinned ReflectiveConfigGroup reads both)
JAVA_SETTER = re.compile(r'@(?:StringSetter|Parameter)\("([^"]+)"\)')


def _java_literal(text):
    """The Java initialiser as a Python value, or None if it is not a literal."""
    raw = text.strip().rstrip('LlFfDd') if text.strip()[-1:] in 'LlFfDd' else text.strip()
    if raw.startswith('"') and raw.endswith('"'):
        return raw[1:-1]
    if raw in ('true', 'false'):
        return raw == 'true'
    try:
        return float(raw) if '.' in raw or 'e' in raw.lower() else int(raw)
    except ValueError:
        return None


def java_shadow_defaults(corpus, fields):
    """A Java config default that EQUALS the value its registry field declares."""
    by_param = {}
    for key, f in fields.items():
        if not isinstance(f, dict):
            continue
        for target in str(f.get('matsim_param') or '').split(','):
            target = target.strip()
            if target and '[' not in target:
                by_param[target.split('.')[-1]] = (key, f.get('value'))

    out = []
    for path, text in sorted(corpus.items()):
        if not path.endswith('.java'):
            continue
        params = set(JAVA_SETTER.findall(text))
        for m in JAVA_FIELD.finditer(text):
            name, raw = m.group(1), m.group(2)
            if name not in params or name not in by_param:
                continue
            value = _java_literal(raw)
            if value is None:
                continue
            key, declared = by_param[name]
            same = value == declared
            if isinstance(declared, list) and len(declared) == 1:
                same = value == declared[0]
            if isinstance(declared, (int, float)) and isinstance(value, (int, float)):
                same = abs(float(value) - float(declared)) < 1e-9
            if same:
                out.append((rel(path), text[:m.start()].count('\n') + 1,
                            name, raw.strip(), key))
    return out


def coordinates(corpus):
    """A line whose literals include both a plausible latitude and longitude.

    Two passes, because either alone is wrong. The AST says which lines carry
    real numeric literals, so prose about a figure cannot be reported as a
    place. The SOURCE TEXT then supplies the precision, because a float's repr
    drops trailing zeros - `-32.92800` reprs as `32.928`, and judging precision
    from the parsed value silently dropped four of this repository's
    coordinates on the first attempt.
    """
    out = []
    for p, text in sorted(corpus.items()):
        r = rel(p)
        if not p.endswith('.py') or r in SELF_REFERENTIAL:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        lines = text.splitlines()
        numeric_lines = _numeric_constants(tree)
        for line in sorted(numeric_lines):
            if line > len(lines):
                continue
            src = lines[line - 1]
            vals = [float(m.group(0)) for m in FLOAT.finditer(src)]
            if any(is_lat(v) for v in vals) and any(is_lon(v) for v in vals):
                out.append((r, line, src.strip()[:96]))
                continue
            # A HAND-DRAWN EXTENT, AT ANY PRECISION. The scan above needs four
            # decimal places, because that is what a placed coordinate looks
            # like. A BOX does not: `dict(s=-33.20,w=151.10,n=-32.55,e=151.95)`
            # sat in src/build/gtfs_tools.py as the framework default that
            # clipped every era feed, and carried two decimals, so nothing saw
            # it. A line that names at least three corners of a box AND
            # carries numbers is an extent wherever it is written.
            if EXTENT_KEYS.search(src) and COARSE_FLOAT.search(src):
                coarse = [float(m.group(0)) for m in COARSE_FLOAT.finditer(src)]
                if any(is_lat(v) for v in coarse) and any(is_lon(v) for v in coarse):
                    out.append((r, line, src.strip()[:96]))
    return out


# --------------------------------------------------------------------------
def config_reach():
    """Which bound fields move the emitted config, proven by moving them.

    This is the only check in the repository that can see a value which is
    declared, resolved, recorded in a run's provenance snapshot - and reaches
    nothing. `consumers` is a claim; a text search finds the key in a comment;
    reading the code has never once caught an instance. Changing the value and
    watching the output change has caught every one.

    Cheap enough to run on every commit: it emits a config per field, in memory,
    and never starts MATSim.

    Returns (reaching, inert, error). `error` is not a pass - it means the probe
    could not be built at all, which must be reported rather than counted as
    zero findings.
    """
    try:
        import param_config  # noqa: PLC0415
    except ImportError as exc:                            # noqa: BLE001
        return [], [], 'param_config unavailable: %s' % exc
    try:
        import sys as _s
        import build_matsim_run_inputs as builder         # noqa: PLC0415
    except Exception as exc:                              # noqa: BLE001
        return [], [], 'the run-input builder does not import: %s' % exc
    try:
        resolved = _registry.load(strict=True)
        # The probe runs at the fewest iterations the field admits: its
        # sweep's floor, or its declared value where the city declares the
        # count as a definition with no sweep (the second city, sixteenth
        # report) - the probe could not be built at all for it until then.
        try:
            sweep = resolved.sweep('RUN.controler.last_iteration')
            interval = sweep['interval'] if isinstance(sweep, dict) else sweep
            iterations = int(interval[0])
        except Exception:                                 # noqa: BLE001
            iterations = int(resolved.get('RUN.controler.last_iteration'))
        city_doc = _city.descriptor()
        cfg = _registry.load(
            scenario=city_doc.get('intervention', {}).get('base_scenario'),
            day=city_doc['day_types'][0],
            set={'RUN.controler.last_iteration': iterations})
        # Under `bound_fields` nothing is translated and there is no C1 table
        # to read (9.204): the probe emits what the launcher would, None.
        if builder.scoring_translation(cfg) == 'bound_fields':
            scoring = None
        else:
            scoring = builder.scoring_from_c1(
                cfg, json.load(io.open(builder.PARAMS, encoding='utf-8')),
                builder.hts_purpose_share())
        # The signal and crossing paths are read only under their declared
        # representation gates (9.77); supplying them unconditionally keeps
        # the probe valid on either side of the boundary.
        # The signal, crossing, fare-table and hired-fleet paths are read
        # only under their declared representation gates (9.77); supplying
        # them unconditionally keeps the probe valid on either side of each.
        runtime = builder.config_runtime(cfg, scoring, city_doc['day_types'][0], dict(
            output='output', network='n', plans='p', schedule='s', vehicles='v',
            mode_vehicles='m', parking_prices='k',
            signal_systems='ss', signal_groups='sg', signal_control='sc',
            change_events='ce', boarding_fares='bf', hired_fleet='hf',
            fraction=cfg.get('RUN.sample.fraction')))
    except (Exception, SystemExit) as exc:                # noqa: BLE001
        # a refusal the assembler raises as SystemExit is a probe failure
        # to report, not a reason for the audit to die (the second city's
        # fare table refused the probe for want of a path, sixteenth report)
        return [], [], 'could not resolve a probe configuration: %s' % exc
    reaching, inert = param_config.reach('matsim', cfg, runtime)

    # The pt2matsim configs too. Their parameters are network-construction and
    # schedule-mapping choices - link splitting, candidate distance, which
    # network modes may carry a tram - and until this change all twenty-six of
    # them were literals in the network builder.
    try:
        import build_matsim_network as network            # noqa: PLC0415
        mapper_runtime = {
            'PublicTransitMapping.inputNetworkFile': ('n', 'path', ''),
            'PublicTransitMapping.inputScheduleFile': ('s', 'path', ''),
            'PublicTransitMapping.outputNetworkFile': ('o', 'path', ''),
            'PublicTransitMapping.outputScheduleFile': ('q', 'path', ''),
            'PublicTransitMapping.outputStreetNetworkFile': ('t', 'path', ''),
            'PublicTransitMapping.numOfThreads': (cfg.get('RUN.machine.threads'),
                                                  'derived', 'RUN.machine.threads'),
        }
        for tool_name, rt in (('pt2matsim_osm',
                               network.config_runtime_osm(cfg, 'osm', 'net')),
                              ('pt2matsim_mapper', mapper_runtime)):
            more_reaching, more_inert = param_config.reach(tool_name, cfg, rt)
            reaching = reaching + more_reaching
            inert = inert + more_inert
    except Exception as exc:                              # noqa: BLE001
        return reaching, inert, 'the pt2matsim probes did not run: %s' % exc
    return reaching, inert, None


# --------------------------------------------------------------------------
# 9. Inline literals in the build layer (#188)
# --------------------------------------------------------------------------
# The constant scan above sees ALL-CAPS assignments, keyword defaults, argparse
# defaults and containers of four or more numbers - and a decided value inside
# an expression (`age - 70) / 30`, `population * 0.02`, `t_now + 600`) passed
# the gate at 0 for as long as the gate existed (eighth project report, 11
# September 2026; #188). This walks every numeric literal in the build and
# extract layers' function bodies, drops the shapes that are structure rather
# than decision (indices, unit conversions, format widths, the arguments of
# calls that shape data rather than decide it, subscripts, f-strings), and
# reports the rest. An item leaves the list by being DECLARED - a registry
# field the script reads - or by being entered in STRUCTURAL_INLINE with the
# reason it is not a modelling value. The category gates like every other.
INLINE_LAYERS = ('src/build/', '<city>/build/', '<city>/extract/')
INLINE_ALLOW = {0, 1, 2, 3, 4, 5, 10, 100, 1000, 60, 3600, 24, 7, 12, 365, 1024, 255,
                90, 180, 360, 1e3, 1e6, 1e9, 1e-3, 1e-6, 1e-9, 1e-12, 111320, 6371000,
                6371, 111000, 110540, 3.6}
INLINE_STRUCTURAL_CALLS = {
    'round', 'range', 'enumerate', 'ljust', 'rjust', 'zfill', 'seek', 'read', 'print',
    'format', 'sample', 'head', 'tail', 'islice', 'getsizeof', 'sleep', 'timeout', 'zip',
    'log', 'split', 'rsplit', 'join', 'index', 'setdefault', 'insert', 'pop',
    'sort', 'exit', 'SystemExit', 'ValueError', 'randint', 'reshape', 'zeros', 'ones',
    'full', 'linspace', 'arange', 'repeat', 'tile', 'percentile', 'quantile',
    'nanpercentile', 'digitize', 'histogram', 'cut', 'qcut', 'to_datetime', 'Period',
    'timedelta', 'strftime', 'isoformat', 'to_crs', 'set_crs', 'from_epsg', 'Transformer',
    'from_crs', 'writestr', 'open', 'Counter', 'defaultdict', 'seed', 'Random',
    'RandomState', 'default_rng', 'dump', 'dumps', 'loads', 'load', 'isclose',
    'allclose', 'assertIf', 'ceil', 'floor', 'sqrt', 'pow', 'abs', 'sum',
    'len', 'int', 'float', 'str', 'bool', 'sha256', 'md5', 'urlretrieve', 'urlopen',
    'Request', 'run', 'check_call', 'check_output', 'Popen', 'wait', 'Thread', 'fold',
    'wrap', 'truncate', 'quantize', 'ZipFile', 'GzipFile', 'BytesIO', 'StringIO',
    'progress', 'batched', 'chunked', 'nsmallest', 'nlargest', 'query_ball_point',
    'query', 'cKDTree', 'KDTree', 'sjoin_nearest', 'buffer', 'simplify', 'densify',
    'array', 'asarray', 'where', 'searchsorted', 'partition', 'argpartition',
    'std', 'var', 'mean', 'median', 'nanmean', 'nanmedian', 'isfinite', 'iloc', 'loc',
    'rename', 'astype', 'fillna', 'replace', 'startswith', 'endswith', 'strip', 'find'}


class _InlineScan(ast.NodeVisitor):
    """Every numeric literal that is a decision rather than structure.

    A literal is structure when it is a DIRECT argument of a call that shapes
    data rather than deciding it (`round(x, 2)`, `range(3)`), an index or
    slice bound, an f-string format spec, or an ALL-CAPS assignment (category
    4's business). Only the direct argument is exempt: `int(age >= 16)` still
    reports the 16, because the call wraps a decision rather than making one.
    """

    def __init__(self, rp=''):
        self.hits = []
        self.exempt = set()            # id() of Constant nodes that are structure
        self.func = ['<module>']
        self.rp = rp                   # the file, portable, for the STRUCTURAL register

    def visit_FunctionDef(self, node):
        self.func.append(node.name)
        self.generic_visit(node)
        self.func.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    @staticmethod
    def _leaf_constants(node):
        """The Constant under a direct argument: itself, or inside a unary minus."""
        if isinstance(node, ast.Constant):
            return [node]
        if isinstance(node, ast.UnaryOp) and isinstance(node.operand, ast.Constant):
            return [node.operand]
        return []

    def visit_Call(self, node):
        name = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else None)
        if name in INLINE_STRUCTURAL_CALLS:
            for a in list(node.args) + [k.value for k in node.keywords]:
                for c in self._leaf_constants(a):
                    self.exempt.add(id(c))
        self.generic_visit(node)

    def visit_Subscript(self, node):
        sl = node.slice
        parts = [sl] if not isinstance(sl, ast.Slice) else [sl.lower, sl.upper, sl.step]
        for part in parts:
            if part is None:
                continue
            for c in self._leaf_constants(part):
                self.exempt.add(id(c))
            if isinstance(part, ast.Tuple):
                for e in part.elts:
                    for c in self._leaf_constants(e):
                        self.exempt.add(id(c))
        self.generic_visit(node)

    def visit_Assign(self, node):
        caps = [t.id for t in node.targets if isinstance(t, ast.Name) and t.id.isupper()]
        if caps and _legacy.reported_as_decision(caps[0], node.value):
            return                         # category 4's business
        if caps and any('%s:%s' % (self.rp, c) in STRUCTURAL for c in caps):
            return                         # the symbol's STRUCTURAL entry states why
        # An ALL-CAPS EXPRESSION - `X = 0.6 * Y`, `TABLE = dict(a=1.5)`,
        # `BOUNDS = (0.2, 0.8)` - returned unvisited here and unparsed there,
        # so six typed twins of registry values passed the gate at 0 (#212).
        # Its literals are read like any other expression's.
        self.generic_visit(node)

    def visit_JoinedStr(self, node):
        return                             # f-string format specs

    def visit_Constant(self, node):
        v = node.value
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            return
        if v in INLINE_ALLOW or abs(v) in INLINE_ALLOW or id(node) in self.exempt:
            return
        self.hits.append((node.lineno, self.func[-1], v))


def inline_literals(corpus):
    """(file, line, function, value) for every undeclared inline literal."""
    out = []
    for path, text in sorted(corpus.items()):
        if not path.endswith('.py'):
            continue
        rp = portable(rel(path))
        if not any(rp.startswith(layer) for layer in INLINE_LAYERS):
            continue
        if rp in SELF_REFERENTIAL:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        scan = _InlineScan(rp)
        scan.visit(tree)
        for line, func, value in scan.hits:
            key = '%s:%s:%s' % (rp, func, ('%g' % value))
            if key in STRUCTURAL_INLINE:
                continue
            out.append((rp, line, func, value))
    return out


def stale_structural_inline(corpus):
    """A STRUCTURAL_INLINE entry whose literal is no longer in the source.

    A `<city>` entry is one register over every city, written against the
    reference city's files: under another city an entry that is not live is
    stale only if it is not live in the reference city's file either (the
    second city has no `reader_shapes.py`, and its `build_mode_targets.py`
    is a different script under the same name; 9.207).
    """
    live = set()
    for path, text in corpus.items():
        if not path.endswith('.py'):
            continue
        rp = portable(rel(path))
        if not any(rp.startswith(layer) for layer in INLINE_LAYERS):
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        scan = _InlineScan(rp)
        scan.visit(tree)
        for line, func, value in scan.hits:
            live.add('%s:%s:%s' % (rp, func, ('%g' % value)))
    return sorted(k for k in STRUCTURAL_INLINE
                  if k not in live and not _live_in_reference_city(k, _inline_keys))


def _inline_keys(text, rp, city_name=None):
    scan = _InlineScan(rp)
    scan.visit(ast.parse(text))
    return {'%s:%s:%s' % (rp, func, ('%g' % value)) for line, func, value in scan.hits}


def _live_in_reference_city(key, keys_of):
    """Whether a `<city>` register entry is live in another city's file.

    The register is one over every city. Under the reference city an entry
    for a script only a second city has (its own extract or build adapter)
    is not stale while that city's file makes it live; under a second city
    an entry for a reference-city script is judged against the reference
    city's file (9.207). `keys_of` turns a file's text into the register
    keys it makes live.
    """
    if not key.startswith('<city>/'):
        return False
    rp = key.rsplit(':', 2)[0]
    cities_dir = os.path.join(_city.REPO, 'cities')
    others = sorted(d for d in os.listdir(cities_dir)
                    if d != _city.CITY and os.path.isdir(os.path.join(cities_dir, d)))
    for other in others:
        path = os.path.join(cities_dir, other, rp[len('<city>/'):])
        if not os.path.exists(path):
            continue
        try:
            with open(path, encoding='utf-8') as f:
                if key in keys_of(f.read(), rp, other):
                    return True
        except (SyntaxError, OSError):
            continue
    return False


# --------------------------------------------------------------------------
# 10. the clock and unseeded randomness in the build layer (#211's class)
# --------------------------------------------------------------------------
# Everything synthetic is seeded (20260810) and nothing a builder writes may
# depend on the wall clock - the hard constraint, and until the sixteenth
# report it had no scanner: build_manifest.py stamped every regeneration with
# the time of day, so a regeneration with no row changed was a diff (#211).
# Reported like every other question; an item leaves by being removed, or by
# an entry in STRUCTURAL_CLOCK stating why the clock reaches no artefact.
CLOCK_LAYERS = ('src/build/', '<city>/build/')
CLOCK_CALLS = ('datetime.now', 'datetime.utcnow', 'datetime.today', 'date.today',
               'time.time', 'time.time_ns')
# module-level draws from the interpreter's global stream, seeded by the
# clock unless the file seeds it
GLOBAL_RANDOM = {'random', 'randint', 'choice', 'choices', 'shuffle', 'sample',
                 'uniform', 'gauss', 'normalvariate', 'randrange', 'rand', 'randn',
                 'permutation', 'binomial', 'poisson', 'exponential', 'standard_normal',
                 'integers'}
SEEDED_CONSTRUCTORS = ('default_rng', 'RandomState', 'Random', 'Generator', 'SeedSequence')
STRUCTURAL_CLOCK = {
    'src/build/build_timing.py:record:datetime.now':
        'the timing roll-up records WHEN a builder ran; its whole purpose is '
        'the wall time, and it lands in data/_build_timing.json, which the '
        'manifest\'s scan does not cover and .gitignore excludes',
    'src/build/build_timing.py:start:time.time':
        'the same roll-up: a builder\'s elapsed seconds, never in a hashed file',
    'src/build/build_timing.py:__enter__:time.time':
        'the same roll-up, as a context manager',
    'src/build/build_timing.py:__exit__:time.time':
        'the same roll-up, the context manager\'s end',
    'src/build/build_timing.py:_finish:time.time':
        'the same roll-up, the atexit hook that records a builder\'s end',
    'src/build/build_matsim_network.py:java:time.time':
        'how long a pt2matsim stage took, printed to the build log; the '
        'seconds left _matsim_build_report.json in the sixteenth report so '
        'that two builds of one feed describe it the same',
    'src/build/build_matsim_network.py:build_schedule:time.time':
        'the same elapsed seconds, printed beside the mapped feed',
}


def _dotted(node):
    """`a.b.c` for a call target, or the bare name, or ''."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return '.'.join(reversed(parts))


class _ClockScan(ast.NodeVisitor):
    def __init__(self, text):
        self.hits = []
        self.func = ['<module>']
        self.seeded = bool(re.search(r'\brandom\.seed\s*\(\s*[^)\s]', text))

    def visit_FunctionDef(self, node):
        self.func.append(node.name)
        self.generic_visit(node)
        self.func.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Call(self, node):
        name = _dotted(node.func)
        call = None
        if any(name == c or name.endswith('.' + c) for c in CLOCK_CALLS):
            call = name.split('.', 1)[-1] if name.count('.') > 1 else name
        elif name.endswith(SEEDED_CONSTRUCTORS) and not node.args and not node.keywords:
            call = name.rsplit('.', 1)[-1] + '()'          # seeded by the clock
        elif ('.' in name and name.rsplit('.', 1)[-1] in GLOBAL_RANDOM
              and name.rsplit('.', 1)[0].endswith('random') and not self.seeded):
            call = name
        if call:
            self.hits.append((node.lineno, self.func[-1], call))
        self.generic_visit(node)


def wall_clock(corpus):
    """(file, line, function, call) for every clock read or unseeded draw."""
    out = []
    for path, text in sorted(corpus.items()):
        if not path.endswith('.py'):
            continue
        rp = portable(rel(path))
        if not any(rp.startswith(layer) for layer in CLOCK_LAYERS) or rp in SELF_REFERENTIAL:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        scan = _ClockScan(text)
        scan.visit(tree)
        for line, func, call in scan.hits:
            if '%s:%s:%s' % (rp, func, call) in STRUCTURAL_CLOCK:
                continue
            out.append((rp, line, func, call))
    return out


# --------------------------------------------------------------------------
# the city's recorded debt: which rows of which question, keyed stably
# --------------------------------------------------------------------------
DEBT_FILE = ('tests', 'hardcoding_debt.json')
# How a reported row is named in the ledger - without its line number, so a
# recorded item survives an edit above it. A coordinate, a stale register
# entry and a failed probe have no key: they are never recordable.
LEDGER_KEYS = {
    'unwired': lambda r: r[0],
    'report_only': lambda r: r[0],
    'template_literals': lambda r: '%s:%s' % (r[0], r[2]),
    'script_decisions': lambda r: '%s:%s' % (portable(r[0]), r[3]),
    'java_shadow_defaults': lambda r: '%s:%s:%s' % (r[0], r[2], r[4]),
    'inert_bindings': lambda r: r[0],
    'inline_literals': lambda r: '%s:%s:%g' % (r[0], r[2], r[3]),
    'wall_clock': lambda r: '%s:%s:%s' % (r[0], r[2], r[3]),
}


def recorded_debt(led):
    """(failures, {rule: keys recorded}) against this city's ledger.

    The ledger's rules about itself (the ceiling equals the list, a rise is
    an explicit `"raised": true`) and the rule that a recorded item which no
    longer surfaces must be deleted are debt_ledger's, shared with the
    manifest check.
    """
    ledger = _ledger.load(DEBT_FILE)
    debt = {rule: frozenset(e.get('items') or ()) for rule, e in ledger.items()}
    judged = [(rule, {key(r) for r in led.get(rule, [])}, '%s item(s)' % rule, None)
              for rule, key in LEDGER_KEYS.items()]
    failures = _ledger.check_ceilings(ledger, _ledger.base(DEBT_FILE),
                                      tuple(LEDGER_KEYS), 'items')
    more, _counts = _ledger.check_recorded(
        judged, debt, 'cities/%s/%s' % (_city.CITY, '/'.join(DEBT_FILE)))
    # the ROWS the ledger covers: one key (no line number) may stand for
    # several reported lines, and the gate's number is counted in rows
    recorded = {rule: [r for r in led.get(rule, []) if key(r) in debt.get(rule, ())]
                for rule, key in LEDGER_KEYS.items()}
    return failures + more, recorded


def audit():
    """The whole ledger, as data. `--json` writes it; the gate checks it."""
    corpus = {}
    for p in sources():
        try:
            corpus[p] = io.open(p, encoding='utf-8', errors='replace').read()
        except OSError:
            pass
    fields, _ = _registry.load_registry()
    uses = key_uses(corpus, set(fields))
    # Three more ways a field reaches the model without its key being spelled
    # in Python: named by the portable config schema, named as an input to
    # another field's declared derived_from identity, or named by the city
    # descriptor's own unobtained declaration (read via city.descriptor()).
    for key in schema_referenced_keys() | identity_referenced_keys(fields):
        if key in fields:
            uses.setdefault(key, set()).add('config/schema/param_config.json')
    for key in descriptor_referenced_keys():
        if key in fields:
            uses.setdefault(key, set()).add('<city>/city.json')
    reaching, inert, error = config_reach()
    defects, owned = report_only(fields, uses)
    led = dict(
        unwired=unwired(fields, uses),
        report_only=defects,
        stale_structural=[(k,) for k in stale_structural(corpus)],
        stale_pending=[(k,) for k in stale_pending(fields, uses)],
        template_literals=template_literals(corpus),
        script_decisions=script_decisions(corpus, fields),
        coordinates=coordinates(corpus),
        java_shadow_defaults=java_shadow_defaults(corpus, fields),
        inert_bindings=[(k,) for k in inert],
        inline_literals=inline_literals(corpus),
        stale_structural_inline=[(k,) for k in stale_structural_inline(corpus)],
        wall_clock=wall_clock(corpus),
    )
    if error:
        led['reach_probe_failed'] = [(error,)]
    return corpus, fields, led, len(reaching), owned, pending(fields, uses)


# --------------------------------------------------------------------------
# What "reaches the config" does NOT prove
# --------------------------------------------------------------------------
#
# Section 7 nudges every bound field and watches the config bytes move. That
# proves the value ARRIVES. It cannot prove the consumer does anything with it,
# and three fields in this city are live counter-examples: their consumer treats
# the shipped value as an OFF switch, so they are declared, swept, rendered into
# the reference, proven to reach - and inert.
#
# `inert_at` is the consumer's documented off value, declared on the field.
# A field shipped at it is reported here and NOT counted: being switched off is
# a modelling decision with a record behind it, not a defect. What would be a
# defect is a reader taking "137 of 137 proven to reach" as "137 of 137 doing
# something", which is what this section exists to stop.

def switched_off(fields):
    """(key, shipped, inert_at, why) for every field shipped at its off value."""
    out = []
    for key in sorted(fields):
        field = fields[key]
        if not isinstance(field, dict) or 'inert_at' not in field:
            continue
        shipped, off = field.get('value'), field['inert_at']
        try:
            same = float(shipped) == float(off)
        except (TypeError, ValueError):
            same = shipped == off
        if same:
            out.append((key, shipped, off, field.get('inert_reason', '')))
    return out


def _print_switched_off(fields):
    rows = switched_off(fields)
    print('     of those, SHIPPED AT THE CONSUMER\'S OFF VALUE - the field '
          'reaches the config and the consumer ignores it:')
    for key, shipped, off, why in rows:
        print('       %-42s = %-8s (off at %s) %s'
              % (key, shipped, off, why[:60]))
    print('       %d  (not counted: switching a mechanism off is a decision '
          'with a record, but "proven to reach" is not "doing something")'
          % len(rows))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--strict', action='store_true',
                    help='exit 1 if anything is reported outside the recorded debt')
    ap.add_argument('--json', metavar='OUT',
                    help='write the ledger as JSON as well as printing it')
    ap.add_argument('--all-cities', action='store_true',
                    help='run once per city under cities/ (the gate and CI)')
    a = ap.parse_args()
    if a.all_cities:
        return _city.run_per_city(__file__, [x for x in sys.argv[1:] if x != '--all-cities'])

    corpus, fields, led, n_reaching, owned, pending_rows = audit()
    debt_failures, recorded = recorded_debt(led)
    n_recorded = sum(len(v) for v in recorded.values())

    def mark(rule, row):
        """`DEBT` before a row the city has recorded, blanks before one it has not."""
        return 'DEBT' if row in recorded.get(rule, ()) else '    '

    def count(rule):
        n, d = len(led[rule]), len(recorded.get(rule, ()))
        return '%d%s' % (n, '  (%d recorded as debt)' % d if d else '')

    print('city %s - %d declared field(s), %d source file(s)\n'
          % (_city.CITY, len(fields), len(corpus)))

    print('1. DECLARED BUT UNWIRED - the key appears nowhere as a value')
    for row in led['unwired']:
        key, src, status = row
        print('%s %-46s source=%-11s status=%s' % (mark('unwired', row), key, src, status))
    print('     %s\n' % count('unwired'))

    print('   DECLARED AHEAD OF ITS CONSUMER - unwired, with a written reason')
    for key, why in pending_rows:
        print('     %-46s %s' % (key, why[:72]))
    print('     %d  (not counted: each names the phase or issue that will wire '
          'it, and a NEW unwired field with no reason fails the gate)\n'
          % len(pending_rows))

    print('2. REPORT-ONLY - read only by the measurement layer, decides nothing')
    for row in led['report_only']:
        key, src, where = row
        print('%s %-46s source=%-11s %s' % (mark('report_only', row), key, src, ' '.join(where)))
    print('     %s\n' % count('report_only'))

    print('3. TEMPLATE LITERALS - a <param> constant rather than a substitution')
    for row in led['template_literals']:
        f, ln, name, val = row
        print('%s %s:%-5d %-42s = %s' % (mark('template_literals', row), f, ln, name, val))
    print('     %s\n' % count('template_literals'))

    print('4. VALUES DECIDED IN CODE - constant, table, unpacked, kwarg, CLI')
    for row in led['script_decisions']:
        f, ln, form, name, val, n = row
        shown = ('%d numbers' % n) if n > 1 else repr(val)
        print('%s %s:%-5d %-13s %-38s = %s'
              % (mark('script_decisions', row), f, ln, form, name[:38], shown))
    print('     %s\n' % count('script_decisions'))

    print('5. COORDINATES typed into a script - always a violation')
    for f, ln, txt in led['coordinates']:
        print('     %s:%-5d %s' % (f, ln, txt))
    print('     %d\n' % len(led['coordinates']))

    print('6. JAVA DEFAULTS THAT EQUAL THEIR DECLARED VALUE - right by accident')
    for row in led['java_shadow_defaults']:
        f, ln, name, raw, key = row
        print('%s %s:%-5d %-22s = %-12s shadows %s'
              % (mark('java_shadow_defaults', row), f, ln, name, raw, key))
    print('     %s\n' % count('java_shadow_defaults'))

    print('7. INERT BINDINGS - the field is declared, resolves, and moving it '
          'changes NOTHING')
    for row in led['inert_bindings']:
        print('%s %s' % (mark('inert_bindings', row), row[0]))
    for (why,) in led.get('reach_probe_failed', []):
        print('     PROBE FAILED (not a pass): %s' % why)
    print('     %d of %d bound field(s) proven to reach the config by changing '
          'them' % (n_reaching, n_reaching + len(led['inert_bindings'])))
    _print_switched_off(fields)
    print('')

    print('8. STALE EXCEPTIONS - a STRUCTURAL entry whose symbol is gone')
    for (key,) in led['stale_structural']:
        print('     %s' % key)
    print('     %d of %d structural exception(s) no longer name anything'
          % (len(led['stale_structural']), len(STRUCTURAL)))
    for (key,) in led['stale_pending']:
        print('     %s is now wired - drop its PENDING_CONSUMER entry' % key)
    print('     %d of %d pending-consumer entr(ies) are kept promises to prune\n'
          % (len(led['stale_pending']), len(PENDING_CONSUMER)))

    print('9. INLINE LITERALS in the build and extract layers - a number inside '
          'an expression, declared by no field (#188)')
    for row in led['inline_literals']:
        f, ln, func, val = row
        print('%s %s:%d  %s()  %g' % (mark('inline_literals', row), f, ln, func, val))
    print('     %s  (an item leaves by a registry field the script reads, or a '
          'STRUCTURAL_INLINE entry stating why it is not a modelling value)\n'
          % count('inline_literals'))
    for (key,) in led['stale_structural_inline']:
        print('     STALE STRUCTURAL_INLINE entry: %s' % key)

    print('10. WALL CLOCK and unseeded randomness in the build layer - a builder '
          'whose bytes depend on when it ran (#211)')
    for row in led['wall_clock']:
        f, ln, func, call = row
        print('%s %s:%d  %s()  %s' % (mark('wall_clock', row), f, ln, func, call))
    print('     %s\n' % count('wall_clock'))

    for line in debt_failures:
        print('DEBT LEDGER  %s' % line)

    total = sum(len(v) for v in led.values()) - n_recorded + len(debt_failures)
    print('TOTAL %d item(s) outside the recorded debt (%d recorded in '
          'cities/%s/%s). A number in a script is a modelling choice nobody '
          'can see or sweep.' % (total, n_recorded, _city.CITY, '/'.join(DEBT_FILE)))

    if a.json:
        with io.open(a.json, 'w', encoding='utf-8', newline='\n') as f:
            json.dump({k: [list(x) for x in v] for k, v in sorted(led.items())},
                      f, indent=2, ensure_ascii=False, sort_keys=True, default=str)
            f.write('\n')
        print('wrote %s' % a.json)

    if a.strict and total:
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
