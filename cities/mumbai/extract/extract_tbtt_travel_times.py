"""Preserve moving-observer circuit measurements and audit printed speeds."""
from decimal import Decimal
import json
from pathlib import Path
import re

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

SID = 'mmrda_thane_borivali_tunnel_dpr'
OUTPUT_INPUTS = {
    'data/processed/observed/tbtt_travel_times.csv': ['data/raw/traffic/mmrda_thane_borivali_tunnel_dpr_*.pdf'],
    'data/processed/acquisition/tbtt_travel_time_audit.json': ['data/raw/traffic/mmrda_thane_borivali_tunnel_dpr_*.pdf'],
}
# Merged route cells and multiline clock labels visually reviewed on PDF 54-55.
PERIODS = (('8-00', '11.30'), ('13.00', '15.30'), ('17.30', '20.30'),
           ('8-30', '12.00'), ('13.30', '16.00'), ('18.00', '22.30'))
ROUTES = ('Magathane - Tikujiniwadi via Ghodbunder - Magathane via JVLR',
          'Magathane - Tikujiniwadi via JVLR - Magathane via Ghodbunder')


def interval(raw):
    value = Decimal(raw)
    half = Decimal(10) ** value.as_tuple().exponent / 2
    return value - half, value + half


def speed_check(distance, journey, delay, reported, running):
    dlow, dhigh = interval(distance)
    tlow, thigh = interval(journey)
    elapsed = Decimal(journey)
    if running:
        slow, shigh = interval(delay)
        tlow, thigh = tlow - shigh, thigh - slow
        elapsed -= Decimal(delay)
    if tlow <= 0:
        raise ValueError('Nonpositive elapsed-time interval')
    low, high = dlow * 60 / thigh, dhigh * 60 / tlow
    printed_low, printed_high = interval(reported)
    calculated = Decimal(distance) * 60 / elapsed
    return dict(derived_from='60 * distance_km / (journey_minutes - delay_minutes)' if running
                else '60 * distance_km / journey_minutes',
                speed_kind='running' if running else 'journey',
                calculated_speed_kmh=str(calculated), reported_speed_kmh=reported,
                residual_kmh=str(Decimal(reported) - calculated),
                calculated_rounding_interval_kmh=[str(low), str(high)],
                reported_rounding_interval_kmh=[str(printed_low), str(printed_high)],
                status='rounding_compatible' if max(low, printed_low) <= min(high, printed_high)
                else 'source_disagreement')


def clock(raw):
    hour, minute = re.split(r'[.-]', raw)
    return f'{int(hour):02d}:{int(minute):02d}'


def main():
    record, path = source(SID, 'traffic')
    method = ' '.join(page_text(path, 43).split())
    if 'moving observer method' not in method or 'travel time and stopping delay timings' not in method:
        raise ValueError('Survey method text changed')
    pages = {page: page_text(path, page) for page in (54, 55)}
    if 'Analysis of Speed and Delay' not in pages[54] or '4.7' not in pages[55]:
        raise ValueError('Speed table section changed')
    distance_matches = re.findall(r'\b(\d+\.\d+) Km\b', pages[54])
    if len(distance_matches) != 1:
        raise ValueError('Ambiguous merged circuit distance')
    distance = distance_matches[0]
    number = r'\d+(?:\.\d+)?'
    pattern = r'^\s*([1-6])\s+.*?\s+(' + number + r')\s+(' + number + r')\s+(' + number + r')\s+(' + number + r')\s+'
    rows, checks = [], []
    for page, text in pages.items():
        body = text.split('Analysis of Speed and Delay', 1)[-1] if page == 54 else text.split('4.7', 1)[0]
        for match in re.finditer(pattern, body, re.M):
            index, journey, delay, journey_speed, running_speed = match.groups()
            index = int(index)
            start, end = PERIODS[index - 1]
            if start not in body or end not in body:
                raise ValueError('Reviewed time label missing from source page')
            if not Decimal(journey) > Decimal(delay) >= 0:
                raise ValueError('Invalid journey/delay relationship')
            rows.append(dict(source='observed', source_id=SID, source_sha256=record['sha256'],
                             source_pdf_page=page, source_row=index, report_edition='October 2022',
                             survey_date='not_stated_in_speed_delay_section',
                             route=ROUTES[0 if index <= 3 else 1],
                             route_scope='complete_circuit_not_single_directional_leg',
                             route_geometry='not_georeferenced', survey_method='moving_observer',
                             survey_vehicle_class='not_stated', repetitions='not_stated',
                             period_start_local=clock(start), period_end_local=clock(end),
                             distance_km=distance, distance_source='merged_cell_PDF54_continued_PDF55',
                             journey_time_minutes=journey, delay_minutes=delay,
                             reported_journey_speed_kmh=journey_speed,
                             reported_running_speed_kmh=running_speed,
                             target_status='historical_evidence_not_current_link_speed_or_capacity'))
            for running, reported in ((False, journey_speed), (True, running_speed)):
                checks.append(dict(source_row=index, **speed_check(distance, journey, delay, reported, running)))
    if [row['source_row'] for row in rows] != list(range(1, 7)):
        raise ValueError('Speed table row coverage changed')
    write('tbtt_travel_times.csv', rows)
    audit = dict(source_id=SID, source_sha256=record['sha256'], rows=len(rows),
                 arithmetic_checks=checks,
                 source_disagreements=sum(c['status'] == 'source_disagreement' for c in checks),
                 extraction_review='PDF pages 54 and 55 visually reviewed including merged route and distance cells.',
                 limitations=[
                     'The two routes are reverse circuits through Ghodbunder Road and JVLR, not single legs between endpoints.',
                     'The count survey is dated 2018 elsewhere; the speed-delay section does not independently date its measurements.',
                     'Clock labels are survey windows, not timetabled departures or precise observation timestamps.',
                     'Rounding intervals test printed arithmetic only; they are not measurement uncertainty or confidence intervals.',
                     'Moving-observer running speed excludes recorded stopping delay, but remains a traffic-condition measurement, not free-flow speed.',
                     'Exact route geometry, test vehicle class, repetitions and day types remain unresolved.',
                 ])
    Path(city.path('data/processed/acquisition/tbtt_travel_time_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('rows', 'source_disagreements')}))


if __name__ == '__main__':
    main()
