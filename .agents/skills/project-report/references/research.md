## Phase 6 — The field: the library first, only its gaps searched

**One researcher**, using Codex web search and page-open tools for external
research. Use primary sources and record the actual URLs read. It opens
`REFERENCE_DIR/field-survey.json` **before it runs a single search**, and
treats it as the answer, not as a hint.

**The reuse rule.** A stored row inside its freshness horizon is carried into
the report as it stands and **is not searched for again**. Search is spent
only on the left-hand column:

| Search this | Leave this alone |
|---|---|
| a project or platform the library has no row for | any row inside its horizon |
| a cell the row records as `unknown`, `ambiguous` or empty | a cell the row already answers with a source URL |
| a row whose facts are past **180 days** (engine, city, modes, validation rung, published fit) | a fact that cannot move: what a 2019 paper measured is what it measured |
| a liveness cell past **90 days** (active / dormant, last release or paper date) | a row's liveness inside 90 days |
| anything the library lists in `gaps` | a candidate already in `excluded`, unless its reason is `not re-verified` |

A reused row is rendered with `reused` and its `last_verified` date in the
sources column, so a reader sees exactly what was checked this pass and what
was inherited. **Reuse is not a shortcut to apologise for: it is how the
library pays for itself.** A row searched for and not re-found keeps its
stored attributes and gains `not_reverified_on: <date>`; it is never emptied.

**The search budget: at most 40 searches or fetches for this phase**, spent in
the order of the table above — the library's own `gaps` first, then
never-seen candidates, then `unknown` cells, then expiries. When the budget is
gone, everything still unsearched is written back into `field-survey.json` as
a named `gap` carrying the query that would close it, and the report says which
gaps it inherited and which it added. A search whose result reaches no row and
no gap was a wasted search; do not run its variants again.

**Who qualifies.** A project that models a real city or region with agents
(activity-based or agent-based, any engine) and publishes a validation claim of
any kind; and a platform (open or commercial) on which such projects are built.
A candidate checked and excluded is written to the library's `excluded` list
with its reason (no validation claim, not a real city, a demo) **so that no
later pass pays for it again**. The territory — every public MATSim scenario
and eqasim derivative, the SUMO / Aimsun / PTV / POLARIS / BEAM / ActivitySim /
SimMobility / mobiTopp / TRANSIMS / Cube / EMME worlds, the commercial and
national "digital twin" platforms and city programmes, the LLM-agent and
generative-agent mobility simulators of the last three years, and what a
transport agency, a university lab or a GitHub search turns up under *city
digital twin*, *agent-based transport model*, *activity-based model
validation*, *multimodal microsimulation calibration* — is the territory the
**library** is meant to cover, not the territory each pass re-walks. Sweep only
the parts of it the library is blank or stale on.

**Stopping rule**: stop when the budget is spent, or when two successive rounds
of differently phrased searches add no qualifying entry the library does not
already hold. Record the round count and the searches spent.

**One row per project**, these columns, an `unknown` where the source does not
say (never a guess, never a figure remembered from training):

engine · city and population · sample fraction · modes simulated · active
modes physical or teleported · public transport physical · signals · freight ·
fares and pricing · **validation rung** (none / survey shares / road link counts /
transit ridership counts / per-mode ridership, every simulated mode) · best
published fit with its metric and what it was measured on · open source ·
reproducible pipeline · city-agnostic · **status** (active / dormant, last
release or paper date) · **what it does best** (one line; the thing this
project could learn from it) · sources (at least one URL per row; a paywalled
source gives `unknown`, and says so).

**One row per platform**: engine, licence, last release, city-agnostic by
design, what it does best, who runs on it. **Our row** is filled from the
artefacts only — the board's scoreboard for the reading, the registry for what
is priced and signalled, the run record for the sample — and says "in
calibration, no mode inside 10 %" if that is what the board says.

Output, **written before the researcher returns** so the work survives an
interrupted pass: the refreshed `REFERENCE_DIR/field-survey.json` — every row
reused, updated or added, each with its `sources`, `last_verified` and
`verified_in`, plus the refreshed `excluded`, `not_reverified` and `gaps`
arrays. Then a copy at `<scratch>/research/field.json` for the writer, which
renders the table, the validation-ladder chart, a "what the comparison says"
list of at most eight bullets, a "what each does best that we lack" list that
feeds Phase 8's recommendations, and the delta since the previous pass
(projects that appeared, went dormant, moved a rung, were not re-verified, or
were carried unchanged from the library).

## Phase 7 — The factors: the library's literature, this repository's status

**One researcher**, the same tools, and one rule that splits the row in half:

- **The literature half is reused.** What the research says about a factor,
  its magnitude, its source and how the leading simulators of Phase 6
  implement it come from `REFERENCE_DIR/factors.json` under a **365-day**
  horizon — a 2021 meta-analysis says the same thing this week as last. Search
  only for a factor the library has no row for, a row whose
  `what_research_says` is empty or marked `needs_research`, or a row past the
  horizon. Count the current empty literature cells from the library; do not
  carry forward the seed library's historical count. Work the gaps in order
  of highest `relevance`.
- **The status half is never reused.** Every factor's status in this model —
  IN / PARTIAL / INERT / ASC / OUT — is re-read at `HEAD` on every pass
  without exception, by `rg` of the registry and the Java, not by a search.
  The model moves weekly and a status carried forward is a status that is
  wrong, which is why the library deliberately does not store one.

**The search budget: at most 40 searches or fetches for this phase.** What it
does not reach is written back as a `needs_research: true` row with the query
that would close it, so the next pass resumes instead of restarting.

The question is wider than mode choice: **every factor that the research says
bears on how people and goods decide to move, and every mechanism a simulator
needs to reproduce those decisions**, organised by decision horizon and layer:

| Layer | Covers |
|---|---|
| A. Long-term choices | residential and workplace location, vehicle ownership and type (including EV and e-bike), licence holding, public-transport passes |
| B. Daily activity pattern | activity generation and scheduling, joint household decisions, escort, telework, day-type differences |
| C. Destination choice | attraction, distance decay, constraints at both ends, intra-zonal trips |
| D. Departure time | peak spreading, schedule delay, activity duration preferences |
| E. Mode choice | time and money; household resources; person attributes; the built form; the trip; comfort, safety, habit, weather, scenery; mode-specific factors for every one of the twelve modes |
| F. Route and within-day | route choice, re-routing and information, parking search, boarding and crowding, ride pairing, reliability |
| G. Supply and physics | network detail, signals, transit operations and dwell, capacity, freight and external traffic, incidents, weather |
| H. Behavioural machinery | utility form, heterogeneity and value-of-time segments, choice-set generation, learning and replanning, plan memory, habit, satisficing, LLM-driven agents |
| I. Calibration and validation | targets and the validation ladder, holdouts, convergence criteria, replication across seeds, sensitivity and sweeps |
| J. Data | population synthesis, travel surveys, smartcard, counts, GTFS, OSM, what is disclosed and what must be derived |
| K. Computation | sample fraction and scaling rules, iteration count, reproducibility, cost per iteration |

**One row per factor**: what the research says, with the source read this
pass (a benchmark synthesis or meta-analysis where one exists, named); how the
leading simulators of Phase 6 implement it; **status in this model** — IN /
PARTIAL / INERT (declared in the registry, read by nothing) / ASC (folded into
a mode constant) / OUT — **proven** by the registry key or the `file:line` that
holds it, checked this pass (`rg` the registry and the Java; the
declared-but-unwired list from `check_hardcoding.py` is the INERT source); and
what it would move on the current scoreboard, tied to a mode's present
deviation. Magnitudes are central tendencies from the literature, labelled
`literature` exactly as the registry's source classes would label them; **no
coefficient is invented, no literature value is presented as observed.**

Output, **written before the researcher returns**: the refreshed
`REFERENCE_DIR/factors.json` — the literature half of every row with its
`source_url`, `last_verified` and `needs_research` flag, and **no status
column** (Phase 8 joins this pass's freshly read statuses to it). Then
`<scratch>/research/factors.json` for the writer, carrying both halves,
rendered as the ledger with its status tiles and a **ranked "would move the
scoreboard" list** — strength of evidence × relevance to a current deviation ×
how much of the data is already in the package — that feeds Phase 8's
recommendations; plus the delta since the previous pass (statuses that changed,
factors added, factors retired, literature halves newly filled).
