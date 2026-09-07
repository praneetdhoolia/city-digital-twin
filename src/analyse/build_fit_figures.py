#!/usr/bin/env python
"""Draw a run's own fit record: modelled against observed, per mode.

    python src/analyse/build_fit_figures.py            # the calibrated base's run
    python src/analyse/build_fit_figures.py --run TAG  # any run that has a _fit.json
    python src/analyse/build_fit_figures.py --check    # committed figures are current

The front door used to state the package's size and say nothing about whether the
model reproduces the city. A reader could not tell, without opening an audit
document, that the base arm puts vehicle passengers at 0.09% against an observed
20.60%. These figures put that on the first screen.

**WHICH RUN.** Never the newest directory - that is usually a two-iteration
plumbing probe, and a probe is not a result (DECISIONS.md 9.7/9.43). The default
is the run the CALIBRATED BASE was written from: `params/C5_calibration.json`
names its `best_tag`, and this finds the run whose `_fit.json` carries that tag.
So these figures and `docs/reference/CALIBRATION_REPORT.md` always describe the same
arm, and both follow the base forward when a new one is calibrated.

**WHAT IT REFUSES TO DRAW.** Only what the fit statistic actually scored. A
target `fit.py` marked unscorable is not quietly plotted with a percentage
against it: the patronage target is a 2019-20 pre-pandemic vintage against a 2026
base year (DECISIONS.md 12.1), and drawing an error bar against it would
manufacture a comparison the model's own fit declines to make. Unscored
observations appear as CONTEXT, labelled, with the reason - never as error.

**Constraints are drawn apart from targets.** Occupancy and trip length are
observables the model is checked against and never fitted to (the C4 pattern).
Putting them in the same panel as the scored targets would let a reader count
them as evidence of fit; they are evidence of plausibility.

No wall-clock anywhere: a figure that restamps itself on every regeneration
churns the diff and cannot be checked for currency. The run's own launch stamp -
its directory name - is the provenance, and it does not move.
"""
# City-relative paths resolve through src/city.py: `params/...` names a location
# inside cities/<city>/, not inside the repository root.
import os as _os
import sys as _sys
_sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)),
                                  '..'))
import city as _city  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import glob  # noqa: E402
import math  # noqa: E402
import argparse  # noqa: E402

OUT_DIR = _city.path('docs', 'reference', 'figures')
CALIBRATION_FILE = _city.path('params/C5_calibration.json')
FAMILIES_FILE = _city.path('docs', 'run_families.json')
RESULTS_DIR = _os.path.join(_city.REPO, 'results')
# The one completion value that means a run executed the horizon it declared
# (src/run/run_matsim.py:RAN_TO_LAST). Named here rather than imported so this
# analysis module does not pull in the launcher.
RAN_TO_LAST = 'ran_to_last_iteration'
LEDGER = 'FIGURES.json'

# Page geometry, in SVG user units. Every number here decides where ink lands on
# a picture of a finished run; none of them can reach a model, an input or a
# result. Grouped into one table so the exception that excuses them is one
# reviewable claim rather than a dozen.
LAYOUT = {
    'width': 760,           # fits GitHub's rendered README column
    'pad': 20,
    'title_h': 26,
    'subtitle_h': 34,
    'legend_h': 22,
    'label_gutter': 196,    # mode names, left-aligned
    'value_gutter': 104,    # the number, right-aligned
    'row_pitch': 46,
    'bar_h': 13,
    'bar_gap': 4,
    'axis_h': 26,
    'tick_len': 4,
    'dot_r': 5,
    'font': 13,
    'font_small': 11.5,
    'font_title': 15,
}

# Two inks per theme so the same figure is legible in GitHub's light and dark
# renderings; the file carries no numbers, so it is structure rather than a
# decision. Modelled/observed are the blue-amber pair that survives the common
# forms of colour blindness - never red against green.
THEMES = {
    'light': {
        'ink': '#1f2328', 'muted': '#59636e', 'grid': '#d1d9e0',
        'modelled': '#0969da', 'observed': '#bc4c00', 'warn': '#a40e26',
        'band': '#dde5ee', 'zero': '#8250df',
    },
    'dark': {
        'ink': '#e6edf3', 'muted': '#9198a1', 'grid': '#3d444d',
        'modelled': '#6cb6ff', 'observed': '#f0883e', 'warn': '#ff8189',
        'band': '#2a313c', 'zero': '#c297ff',
    },
}
FONT_STACK = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, '
              'Arial, sans-serif')


# ------------------------------------------------------------------ selection

def _load(path):
    with io.open(path, encoding='utf-8') as fh:
        return json.load(fh)


def calibrated_base_tag():
    """The run tag the committed calibration was written from, or None."""
    if not _os.path.exists(CALIBRATION_FILE):
        return None
    return _load(CALIBRATION_FILE).get('best_tag')


def find_run(tag=None):
    """The run directory to draw: the named tag, else the calibrated base's.

    Matching is on the tag INSIDE `_fit.json`, not on the directory name, because
    the runner names directories by launch stamp and the calibration records a
    run-config tag. A directory name is accepted too, so `--run <dir>` works.
    """
    wanted = tag or calibrated_base_tag()
    if not wanted:
        raise SystemExit(
            'no --run given and %s names no best_tag: there is no calibrated '
            'base to draw.' % _os.path.relpath(CALIBRATION_FILE, _city.REPO))
    direct = wanted if _os.path.isdir(wanted) \
        else next((d for d in (_os.path.join(RESULTS_DIR, 'raw', wanted),
                               _os.path.join(RESULTS_DIR, wanted),
                               _os.path.join(RESULTS_DIR, 'processed', wanted))
                   if _os.path.isdir(d)),
                  _os.path.join(RESULTS_DIR, 'raw', wanted))
    if _os.path.isdir(direct) and _os.path.exists(_os.path.join(direct,
                                                                '_fit.json')):
        return direct
    hits = []
    for fit_path in sorted(glob.glob(_os.path.join(RESULTS_DIR, 'raw', '*',
                                     '_fit.json'))
                           + glob.glob(_os.path.join(RESULTS_DIR, 'processed', '*',
                                                   '_fit.json'))):
        if _load(fit_path).get('run') == wanted:
            hits.append(_os.path.dirname(fit_path))
    if not hits:
        raise SystemExit(
            'no run directory under results/ carries a _fit.json for %r. '
            'Run src/calibrate/fit.py first, or pass --run.' % wanted)
    # Deterministic: the launch stamp leads the directory name, so the last one
    # sorted is the most recent run of that tag.
    return hits[-1]


def _refuse_unless_ran_to_last(run_dir):
    """The front door draws a RESULT, so its run must have executed its horizon.

    `_fit.json` alone was the test, and a stopped arm carries one: its reading
    at `reached_iteration` is citable, but it is not a result and may not become
    the README's picture of the model's fit. Only `ran_to_last_iteration`
    anchors a calibrated base (9.143). A record written before the `completion`
    field existed was only ever written on rc = 0, so a missing value reads as
    `ran_to_last_iteration` - a frozen record is never rewritten to satisfy a
    newer schema.
    """
    path = _os.path.join(run_dir, '_run.json')
    if not _os.path.exists(path):
        raise SystemExit(
            '%s carries no _run.json, so it never ended at a defined boundary '
            'and cannot be drawn as the model\'s fit.'
            % _os.path.relpath(run_dir, _city.REPO))
    completion = _load(path).get('completion') or RAN_TO_LAST
    if completion != RAN_TO_LAST:
        raise SystemExit(
            '%s ended as %r, not %r: a stopped arm is a citable reading at its '
            'reached_iteration, never the fit on the front page. Point '
            'C5_calibration.json at a run that executed the horizon it '
            'declared, or pass --run explicitly to draw a diagnostic.'
            % (_os.path.relpath(run_dir, _city.REPO), completion, RAN_TO_LAST))
    return run_dir


def family_of(run_name):
    """The declared comparability family a run belongs to, or 'unattributed'."""
    if not _os.path.exists(FAMILIES_FILE):
        return 'unattributed'
    doc = _load(FAMILIES_FILE)
    fams = doc.get('families', doc)
    overrides = doc.get('overrides', {})
    if run_name in overrides and overrides[run_name].get('family'):
        return overrides[run_name]['family']
    best = 'unattributed'
    for key, fam in sorted(fams.items()):
        start = fam.get('from_launch')
        if start and run_name >= start:
            best = key
    return best


# --------------------------------------------------------------- svg drawing

def _n(value):
    """A coordinate, formatted identically on every machine and every run."""
    text = '%.2f' % float(value)
    text = text.rstrip('0').rstrip('.')
    return text if text not in ('', '-0') else '0'


def _esc(text):
    return (str(text).replace('&', '&amp;').replace('<', '&lt;')
            .replace('>', '&gt;'))


class Canvas(object):
    """An SVG document built as a list of elements. No layout engine, no deps.

    Text is never measured - there is no font metric available without pulling in
    a rendering library - so every column is a FIXED GUTTER wide enough for the
    longest label the artefacts produce. A label that outgrew its gutter would
    overlap, which is visible immediately; silently rescaled axes would not be.
    """

    def __init__(self, width, height, theme):
        self.width, self.height = width, height
        self.c = THEMES[theme]
        self.parts = []

    def text(self, x, y, s, size=None, fill=None, anchor='start', weight=None):
        size = LAYOUT['font'] if size is None else size
        attrs = ['x="%s"' % _n(x), 'y="%s"' % _n(y),
                 'font-size="%s"' % _n(size),
                 'fill="%s"' % (fill or self.c['ink'])]
        if anchor != 'start':
            attrs.append('text-anchor="%s"' % anchor)
        if weight:
            attrs.append('font-weight="%s"' % weight)
        self.parts.append('<text %s>%s</text>' % (' '.join(attrs), _esc(s)))

    def rect(self, x, y, w, h, fill, radius=None):
        extra = ' rx="%s"' % _n(radius) if radius else ''
        self.parts.append(
            '<rect x="%s" y="%s" width="%s" height="%s" fill="%s"%s/>'
            % (_n(x), _n(y), _n(max(w, 0)), _n(max(h, 0)), fill, extra))

    def line(self, x1, y1, x2, y2, stroke, dash=None, width=None):
        extra = ' stroke-dasharray="%s"' % dash if dash else ''
        self.parts.append(
            '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" '
            'stroke-width="%s"%s/>'
            % (_n(x1), _n(y1), _n(x2), _n(y2), stroke, _n(width or 1), extra))

    def dot(self, x, y, fill, r=None):
        self.parts.append('<circle cx="%s" cy="%s" r="%s" fill="%s"/>'
                          % (_n(x), _n(y), _n(r or LAYOUT['dot_r']), fill))

    def render(self, title):
        head = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="%s" height="%s" '
            'viewBox="0 0 %s %s" font-family=\'%s\' role="img" '
            'aria-label="%s">'
            % (_n(self.width), _n(self.height), _n(self.width),
               _n(self.height), FONT_STACK, _esc(title)))
        return '\n'.join([head] + self.parts + ['</svg>', ''])


def nice_ceiling(value):
    """A round axis maximum at or above `value`: 1/2/5 x a power of ten."""
    if value <= 0:
        return 1.0
    power = 10.0 ** math.floor(math.log10(value))
    for step in (1.0, 2.0, 2.5, 5.0, 10.0):
        if value <= step * power:
            return step * power
    return 10.0 * power


def axis_ticks(maximum, count):
    """`count` evenly spaced ticks from zero to `maximum`, inclusive."""
    return [maximum * i / float(count) for i in range(count + 1)]


def _header(canvas, title, subtitle_lines):
    pad = LAYOUT['pad']
    canvas.text(pad, pad + LAYOUT['title_h'] - 8, title,
                size=LAYOUT['font_title'], weight='600')
    y = pad + LAYOUT['title_h'] + 6
    for line in subtitle_lines:
        canvas.text(pad, y, line, size=LAYOUT['font_small'],
                    fill=canvas.c['muted'])
        y += 15
    return y + 6


def _legend(canvas, y, entries):
    """Swatches left to right. A `dash` entry is drawn as the line it explains.

    A dashed reference line legended with a solid block reads as a fourth data
    series, and on the dark theme the block is nearly invisible against the
    page - so the swatch is the mark itself.
    """
    x = LAYOUT['pad']
    for label, colour, dash in entries:
        if dash:
            canvas.line(x, y - 4, x + 11, y - 4, colour, dash=dash, width=2)
        else:
            canvas.rect(x, y - 9, 11, 11, colour, radius=2)
        canvas.text(x + 17, y, label, size=LAYOUT['font_small'])
        x += 19 + int(len(label) * 6.4)
    return y + LAYOUT['legend_h']


# ------------------------------------------------------------------- figure 1

def figure_mode_share(fit, theme):
    """Scored mode-share targets: two bars per mode, and the error in points."""
    block = fit['mode_share']
    rows = sorted(block['errors'], key=lambda r: -float(r['observed']))
    plot_x = LAYOUT['label_gutter']
    plot_w = (LAYOUT['width'] - LAYOUT['label_gutter']
              - LAYOUT['value_gutter'] - LAYOUT['pad'])
    height = (LAYOUT['pad'] + LAYOUT['title_h'] + LAYOUT['subtitle_h']
              + LAYOUT['legend_h'] + len(rows) * LAYOUT['row_pitch']
              + LAYOUT['axis_h'] + LAYOUT['pad'])
    canvas = Canvas(LAYOUT['width'], height, theme)

    top = _header(canvas, 'Mode share - modelled against observed', [
        'Every mode against ITS OWN observed value. %d scored targets, '
        'mean absolute error %.2f percentage points.'
        % (block['n'], float(block['mean_abs_pp'])),
        'A pre-calibration diagnostic of one base arm, not a finding about the '
        'intervention.'])
    top = _legend(canvas, top, [('modelled', canvas.c['modelled'], None),
                                ('observed', canvas.c['observed'], None)])

    top_value = nice_ceiling(max(max(float(r['modelled']),
                                     float(r['observed'])) for r in rows))
    scale = plot_w / top_value

    axis_y = top + len(rows) * LAYOUT['row_pitch'] + 6
    for tick in axis_ticks(top_value, 4):
        x = plot_x + tick * scale
        canvas.line(x, top - 4, x, axis_y, canvas.c['grid'])
        canvas.text(x, axis_y + 15, '%g%%' % tick, size=LAYOUT['font_small'],
                    fill=canvas.c['muted'], anchor='middle')

    drawn = []
    for i, row in enumerate(rows):
        y = top + i * LAYOUT['row_pitch']
        modelled, observed = float(row['modelled']), float(row['observed'])
        error = float(row['abs_error'])
        canvas.text(LAYOUT['pad'], y + 13, row['hts_category'], weight='600')
        canvas.text(LAYOUT['pad'], y + 28, row['matsim_mode'],
                    size=LAYOUT['font_small'], fill=canvas.c['muted'])
        canvas.rect(plot_x, y + 2, modelled * scale, LAYOUT['bar_h'],
                    canvas.c['modelled'], radius=2)
        canvas.rect(plot_x, y + 2 + LAYOUT['bar_h'] + LAYOUT['bar_gap'],
                    observed * scale, LAYOUT['bar_h'], canvas.c['observed'],
                    radius=2)
        canvas.text(LAYOUT['width'] - LAYOUT['pad'], y + 13,
                    '%+.2f pp' % error, anchor='end', weight='600',
                    fill=canvas.c['warn' if abs(error) >= 1 else 'ink'])
        canvas.text(LAYOUT['width'] - LAYOUT['pad'], y + 28,
                    '%.2f vs %.2f' % (modelled, observed), anchor='end',
                    size=LAYOUT['font_small'], fill=canvas.c['muted'])
        drawn.append({'hts_category': row['hts_category'],
                      'matsim_mode': row['matsim_mode'],
                      'modelled_pct': modelled, 'observed_pct': observed,
                      'error_pp': error, 'target_id': row['target_id']})
    return canvas.render('Mode share, modelled against observed'), drawn


# ------------------------------------------------------------------- figure 2

def figure_trip_length(fit, theme):
    """Trip length against the observed range: a constraint, never a target."""
    block = fit['trip_geometry_constraint']
    modes = sorted(block['modes'].items(),
                   key=lambda kv: -float(kv[1]['observed_mean_distance_km']))
    plot_x = LAYOUT['label_gutter']
    plot_w = (LAYOUT['width'] - LAYOUT['label_gutter']
              - LAYOUT['value_gutter'] - LAYOUT['pad'])
    height = (LAYOUT['pad'] + LAYOUT['title_h'] + LAYOUT['subtitle_h']
              + LAYOUT['legend_h'] + len(modes) * LAYOUT['row_pitch']
              + LAYOUT['axis_h'] + LAYOUT['pad'])
    canvas = Canvas(LAYOUT['width'], height, theme)

    inside = sum(1 for _, m in modes if m['inside_observed_range'])
    top = _header(canvas, 'Mean trip length - modelled against the observed range', [
        '%s. %d of %d modes fall inside their observed range.'
        % (block['geography'], inside, len(modes)),
        'A CONSTRAINT, checked and reported: it is never fitted to and enters no '
        'fit statistic.'])
    top = _legend(canvas, top, [('modelled', canvas.c['modelled'], None),
                                ('observed mean', canvas.c['observed'], None),
                                ('observed range', canvas.c['band'], None)])

    top_value = nice_ceiling(max(
        max(float(m['modelled_mean_distance_km']),
            float(m['observed_mean_distance_km']),
            max(float(v) for v in m['observed_distance_sweep']))
        for _, m in modes))
    scale = plot_w / top_value

    axis_y = top + len(modes) * LAYOUT['row_pitch'] + 6
    for tick in axis_ticks(top_value, 4):
        x = plot_x + tick * scale
        canvas.line(x, top - 4, x, axis_y, canvas.c['grid'])
        canvas.text(x, axis_y + 15, '%g km' % tick, size=LAYOUT['font_small'],
                    fill=canvas.c['muted'], anchor='middle')

    drawn = []
    for i, (mode, m) in enumerate(modes):
        y = top + i * LAYOUT['row_pitch']
        mid = y + 14
        lo, hi = (float(v) for v in m['observed_distance_sweep'])
        modelled = float(m['modelled_mean_distance_km'])
        observed = float(m['observed_mean_distance_km'])
        ok = bool(m['inside_observed_range'])
        canvas.text(LAYOUT['pad'], y + 13, mode, weight='600')
        canvas.text(LAYOUT['pad'], y + 28,
                    '%s observed range' % ('inside' if ok else 'OUTSIDE'),
                    size=LAYOUT['font_small'],
                    fill=canvas.c['muted' if ok else 'warn'])
        canvas.rect(plot_x + lo * scale, mid - 9, (hi - lo) * scale, 18,
                    canvas.c['band'], radius=3)
        canvas.line(plot_x + observed * scale, mid - 9,
                    plot_x + observed * scale, mid + 9,
                    canvas.c['observed'], width=2.5)
        canvas.dot(plot_x + modelled * scale, mid, canvas.c['modelled'])
        canvas.text(LAYOUT['width'] - LAYOUT['pad'], y + 13,
                    '%.2f km' % modelled, anchor='end', weight='600',
                    fill=canvas.c['ink' if ok else 'warn'])
        canvas.text(LAYOUT['width'] - LAYOUT['pad'], y + 28,
                    'x%.2f observed' % float(m['ratio_modelled_to_observed']),
                    anchor='end', size=LAYOUT['font_small'],
                    fill=canvas.c['muted'])
        drawn.append({'mode': mode, 'modelled_km': modelled,
                      'observed_km': observed, 'observed_sweep_km': [lo, hi],
                      'inside_observed_range': ok,
                      'ratio': float(m['ratio_modelled_to_observed'])})
    return canvas.render('Trip length against the observed range'), drawn


# ------------------------------------------------------------------- figure 3

def figure_counts(fit, theme):
    """Traffic counts: modelled against observed on log axes, with 1:1."""
    block = fit['counts']
    rows = sorted(block['errors'], key=lambda r: r['target_id'])
    plot_x = LAYOUT['pad'] + 52
    plot_w = LAYOUT['width'] - plot_x - LAYOUT['pad'] - 8
    plot_h = 300
    height = (LAYOUT['pad'] + LAYOUT['title_h'] + LAYOUT['subtitle_h']
              + LAYOUT['legend_h'] + plot_h + LAYOUT['axis_h'] + 18
              + LAYOUT['pad'])
    canvas = Canvas(LAYOUT['width'], height, theme)

    zeros = [r for r in rows if not float(r['modelled']) > 0]
    top = _header(canvas, 'Weekday traffic counts - modelled against observed', [
        '%d count stations. Mean error %.1f%%; %d stations model to zero.'
        % (block['n'], float(block['mean_pct_error']), len(zeros)),
        'Scored and REPORTED, never optimised against: tuning the network to '
        'these would hide what the model is missing.'])
    top = _legend(canvas, top, [('count station', canvas.c['modelled'], None),
                                ('modelled zero', canvas.c['zero'], None),
                                ('perfect agreement', canvas.c['muted'], '5 4')])

    values = ([float(r['observed']) for r in rows]
              + [float(r['modelled']) for r in rows if float(r['modelled']) > 0])
    lo_pow = math.floor(math.log10(min(values)))
    hi_pow = math.ceil(math.log10(max(values)))
    span = float(hi_pow - lo_pow)
    zero_band = 26

    def px(value):
        return plot_x + (math.log10(value) - lo_pow) / span * plot_w

    def py(value):
        if not value > 0:
            return top + plot_h - zero_band / 2.0
        usable = plot_h - zero_band
        return top + usable - (math.log10(value) - lo_pow) / span * usable

    decade = lo_pow
    while decade <= hi_pow:
        value = 10.0 ** decade
        canvas.line(px(value), top, px(value), top + plot_h - zero_band,
                    canvas.c['grid'])
        canvas.line(plot_x, py(value), plot_x + plot_w, py(value),
                    canvas.c['grid'])
        label = '%g' % value if value < 1000 else '%gk' % (value / 1000.0)
        canvas.text(px(value), top + plot_h + 4, label,
                    size=LAYOUT['font_small'], fill=canvas.c['muted'],
                    anchor='middle')
        canvas.text(plot_x - 8, py(value) + 4, label, size=LAYOUT['font_small'],
                    fill=canvas.c['muted'], anchor='end')
        decade += 1

    # y = x: where a station would sit if the model reproduced it exactly.
    canvas.line(px(10.0 ** lo_pow), py(10.0 ** lo_pow),
                px(10.0 ** hi_pow), py(10.0 ** hi_pow),
                canvas.c['grid'], dash='5 4', width=1.5)
    canvas.line(plot_x, top + plot_h - zero_band, plot_x + plot_w,
                top + plot_h - zero_band, canvas.c['grid'], dash='2 3')
    canvas.text(plot_x - 8, top + plot_h - zero_band / 2.0 + 4, '0',
                size=LAYOUT['font_small'], fill=canvas.c['zero'], anchor='end')

    for row in rows:
        modelled, observed = float(row['modelled']), float(row['observed'])
        positive = modelled > 0
        canvas.dot(px(observed), py(modelled),
                   canvas.c['modelled' if positive else 'zero'], r=4)
    canvas.text(plot_x + plot_w / 2.0, top + plot_h + 26,
                'observed vehicles/day', size=LAYOUT['font_small'],
                fill=canvas.c['muted'], anchor='middle')
    canvas.text(LAYOUT['pad'] - 6, top - 8, 'modelled vehicles/day',
                size=LAYOUT['font_small'], fill=canvas.c['muted'])

    drawn = {'stations': block['n'],
             'mean_pct_error': float(block['mean_pct_error']),
             'mean_abs_pct_error': float(block['mean_abs_pct_error']),
             'modelled_zero_stations': len(zeros)}
    return canvas.render('Traffic counts, modelled against observed'), drawn


# ------------------------------------------------------------------- assembly

FIGURES = (
    ('fit_mode_share', figure_mode_share, 'mode_share'),
    ('fit_trip_length', figure_trip_length, 'trip_length'),
    ('fit_counts', figure_counts, 'counts'),
)


def unscored_context(fit):
    """Observations the fit REFUSED to score, with the reason it gave.

    Recorded beside the figures precisely so nobody redraws them as error bars.
    The patronage level is the live example: the model puts the intervention at
    a number, the nearest published observation is a different market vintage,
    and the difference between the two is not a fit statistic.
    """
    patronage = fit.get('patronage') or {}
    out = {}
    modelled = patronage.get('intervention_boardings',
                             patronage.get('modelled_lr_weekday_boardings'))
    if modelled is not None:
        # Selected on the METRIC each unscored target names, not on its id: an
        # id is an opaque sequence number, and matching one would silently
        # return nothing the moment the target set is renumbered.
        out['intervention_boardings'] = {
            'modelled_per_weekday': modelled,
            'scored': bool(patronage.get('targets')),
            'unscored_targets': {
                u['target_id']: {'metric': u.get('metric', ''),
                                 'period': u.get('note', ''),
                                 'reason': u.get('reason', '')}
                for u in sorted(fit['unscorable'],
                                key=lambda u: u['target_id'])
                if 'boardings' in str(u.get('metric', '')).lower()},
        }
    return out


def build(run_dir):
    """Every figure and the ledger of what they draw, as text."""
    fit = _load(_os.path.join(run_dir, '_fit.json'))
    run_name = _os.path.basename(run_dir.rstrip('/\\'))
    files = {}
    drawings = {}
    for stem, fn, key in FIGURES:
        for theme in sorted(THEMES):
            svg, drawn = fn(fit, theme)
            files['%s.%s.svg' % (stem, theme)] = svg
        drawings[key] = drawn

    context = unscored_context(fit)
    ledger = {
        'generated_by': 'src/analyse/build_fit_figures.py',
        'note': 'Regenerate; do not edit. Carries no wall-clock stamp: the '
                'provenance is the run, and the run does not move.',
        'run': {
            'directory': run_name,
            'tag': fit.get('run'),
            'family': family_of(run_name),
            'scenario': fit.get('scenario'),
            'day': fit.get('day'),
            'fraction': fit.get('fraction'),
            'iterations': fit.get('iterations'),
            'state': 'pre-calibration diagnostic of the base arm; not a '
                     'scenario comparison and not a finding about the '
                     'intervention',
        },
        'targets': {
            'available': fit.get('calibration_targets_available'),
            'scored': fit.get('scored'),
            'unscored': fit.get('unscored'),
        },
        'mode_share': {
            'mean_abs_pp': float(fit['mode_share']['mean_abs_pp']),
            'n_scored': fit['mode_share']['n'],
            'rows': drawings['mode_share'],
        },
        'trip_length_constraint': {
            'geography': fit['trip_geometry_constraint']['geography'],
            'modes_inside_observed_range': sum(
                1 for r in drawings['trip_length'] if r['inside_observed_range']),
            'modes': drawings['trip_length'],
        },
        'occupancy_constraint': fit['occupancy_constraint'],
        'counts_constraint': drawings['counts'],
        'not_scored': context,
        'figures': sorted(files),
    }
    files[LEDGER] = json.dumps(ledger, indent=2, ensure_ascii=False) + '\n'
    return files


def write(files, out_dir):
    if not _os.path.isdir(out_dir):
        _os.makedirs(out_dir)
    for name in sorted(files):
        with io.open(_os.path.join(out_dir, name), 'w', encoding='utf-8',
                     newline='\n') as fh:
            fh.write(files[name])
    return sorted(files)


def check(files, out_dir):
    """Which committed figures no longer match the run they claim to draw."""
    stale = []
    for name in sorted(files):
        path = _os.path.join(out_dir, name)
        if not _os.path.exists(path):
            stale.append((name, 'missing'))
            continue
        with io.open(path, encoding='utf-8', newline='') as fh:
            if fh.read().replace('\r\n', '\n') != files[name]:
                stale.append((name, 'differs from the run it claims to draw'))
    return stale


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--run', help='run directory or the tag inside its '
                                  '_fit.json (default: the calibrated base)')
    ap.add_argument('--out', help='output directory (default: the city\'s '
                                  'docs/reference/figures)')
    ap.add_argument('--check', action='store_true',
                    help='exit 1 if the committed figures are not current')
    args = ap.parse_args()

    run_dir = _refuse_unless_ran_to_last(find_run(args.run))
    out_dir = args.out or OUT_DIR
    files = build(run_dir)
    rel_run = _os.path.relpath(run_dir, _city.REPO).replace(_os.sep, '/')

    if args.check:
        stale = check(files, out_dir)
        for name, why in stale:
            print('STALE %s - %s' % (name, why))
        print('%d of %d figure file(s) out of date against %s'
              % (len(stale), len(files), rel_run))
        return 1 if stale else 0

    written = write(files, out_dir)
    print('%s -> %s' % (rel_run,
                        _os.path.relpath(out_dir, _city.REPO).replace(_os.sep, '/')))
    for name in written:
        print('  %s' % name)
    return 0


if __name__ == '__main__':
    _sys.exit(main())
