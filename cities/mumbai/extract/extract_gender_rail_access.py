"""Preserve historical women-user survey denominators and access-mode counts."""
from decimal import Decimal
import json
from pathlib import Path
import re

from pypdf import PdfReader
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/tiss_rail_survey_strata_2016.csv': ['data/raw/demand/mrvc_gender_tiss_study_*.pdf'],
    'data/processed/observed/tiss_rail_access_modes_2016.csv': ['data/raw/demand/mrvc_gender_tiss_study_*.pdf'],
    'data/processed/acquisition/tiss_rail_access_audit.json': ['data/raw/demand/mrvc_gender_tiss_study_*.pdf'],
}


def percentage_check(count, denominator, printed):
    observed = Decimal(printed)
    derived = Decimal(count) * 100 / Decimal(denominator)
    half_last_digit = Decimal(10) ** observed.as_tuple().exponent / 2
    return dict(recomputed_share_percent=str(derived),
                reported_minus_recomputed_percentage_points=str(observed - derived),
                consistent_with_printed_rounding=abs(observed - derived) <= half_last_digit)


def main():
    sid = 'mrvc_gender_tiss_study'
    record, path = source(sid, 'demand')
    pdf = PdfReader(path)
    if '2016' not in pdf.pages[1].extract_text():
        raise ValueError('Survey report title-page year changed')
    common = dict(source='observed_historical_survey_publication', source_id=sid,
        source_sha256=record['sha256'], publication_year=2016,
        population_scope='sampled_women_suburban_rail_users_not_all_residents_or_all_trips',
        fieldwork_date_status='full_survey_dates_not_established_by_extracted_sections',
        current_model_parameter_adopted=False)
    text = pdf.pages[18].extract_text()
    table = text.split('Table 1:', 1)[1].split('(For a detailed note', 1)[0]
    total = int(re.search(r'Distribution of sample of (\d+) respondents', table).group(1))
    if 'Western Line Central Line Harbour Line' not in ' '.join(table.split()):
        raise ValueError('Survey stratum columns changed')
    counts_match = re.search(r'^\s*line\s+(\d+)\s+(\d+)\s+(\d+)\s*$', table, re.MULTILINE)
    shares_match = re.search(r'^\s*([\d.]+)%\s+([\d.]+)%\s+([\d.]+)%\s*$', table, re.MULTILINE)
    if counts_match is None or shares_match is None:
        raise ValueError('Survey line count/share rows not found')
    line_counts = tuple(map(int, counts_match.groups()))
    if sum(line_counts) != total:
        raise ValueError('Survey line counts do not reconcile to printed sample size')
    classes = re.findall(r'^\s*(\d+)\s*\(([\d.]+)%\)\s+(\d+)\s*\(([\d.]+)%\)\s+(\d+)\s*\(([\d.]+)%\)\s*$', table, re.MULTILINE)
    if len(classes) != 3 or not all(label in table for label in ('2nd Class', '1st Class', 'Other Class')):
        raise ValueError('Survey class strata changed')
    strata = []
    line_names = ('Western Line', 'Central Line', 'Harbour Line')
    for line, count, share in zip(line_names, line_counts, shares_match.groups()):
        strata.append(dict(**common, source_pdf_page=19, source_printed_page=15, source_table=1,
            railway_line_as_printed=line, travel_class_as_printed='All classes',
            reported_respondents_persons=count, reported_share_percent=share,
            denominator_respondents_persons=total, denominator_scope='all_sampled_respondents',
            **percentage_check(count, total, share)))
    counts_by_line = [0 for _ in line_names]
    for class_name, cells in zip(('2nd Class', '1st Class', 'Other Class (Disabled and Luggage)'), classes):
        counts, shares = [int(v) for v in cells[::2]], cells[1::2]
        denominator = sum(counts)
        for index, (line, count, share) in enumerate(zip(line_names, counts, shares)):
            counts_by_line[index] += count
            strata.append(dict(**common, source_pdf_page=19, source_printed_page=15, source_table=1,
                railway_line_as_printed=line, travel_class_as_printed=class_name,
                reported_respondents_persons=count, reported_share_percent=share,
                denominator_respondents_persons=denominator, denominator_scope='sampled_respondents_in_this_class_across_lines',
                **percentage_check(count, denominator, share)))
    if tuple(counts_by_line) != line_counts:
        raise ValueError('Survey class counts disagree with line totals')
    time_text = ' '.join(pdf.pages[18].extract_text(extraction_mode='layout').split())
    time_match = re.search(r'comprises (\d+) off.peak observations and (\d+) peak observations', time_text)
    if not time_match:
        raise ValueError('Peak/off-peak sample design counts not found')
    offpeak, peak = map(int, time_match.groups())
    if offpeak + peak != total:
        raise ValueError('Time strata do not reconcile to sample size')
    access_text = pdf.pages[26].extract_text().split('Table 9:', 1)[1]
    header = ' '.join(access_text.split('Numbers', 1)[0].split())
    if not header.endswith('Walk Auto /Share Bus Train Taxi Own /Pvt Vehicle Metro'):
        raise ValueError('Access-mode column order changed')
    numbers = re.search(r'^Numbers\s+([^\n]+)', access_text, re.MULTILINE).group(1).split()
    percentages = re.search(r'^Percentage\s+([^\n]+)', access_text, re.MULTILINE).group(1).split()
    modes = ('Walk', 'Auto /Share', 'Bus', 'Train', 'Taxi', 'Own /Pvt Vehicle', 'Metro')
    if len(numbers) != len(modes) or len(percentages) != len(modes):
        raise ValueError('Incomplete access-mode table')
    observed_counts = [Decimal(v) for v in numbers if v != 'N/A']
    if any(v != v.to_integral_value() for v in observed_counts):
        raise ValueError('Non-integral respondent counts require review')
    denominator = int(sum(observed_counts))
    access = []
    for mode, number, share in zip(modes, numbers, percentages):
        if (number == 'N/A') != (share == 'N/A'):
            raise ValueError('Missing count and share indicators disagree')
        missing = number == 'N/A'
        check = (dict(recomputed_share_percent='', reported_minus_recomputed_percentage_points='',
                      consistent_with_printed_rounding='not_applicable') if missing else
                 percentage_check(int(Decimal(number)), denominator, share))
        access.append(dict(**common, source_pdf_page=27, source_printed_page=23, source_table=9,
            journey_scope='first_leg_from_home_to_rail_station', mode_as_printed=mode,
            count_as_printed=number, reported_respondents_persons='' if missing else int(Decimal(number)),
            share_as_printed=share, reported_share_percent='' if missing else share,
            derived_table_denominator_respondents_persons=denominator,
            source_value_status='not_applicable_as_printed_not_zero' if missing else 'observed_table_cell', **check))
    write('tiss_rail_survey_strata_2016.csv', strata)
    write('tiss_rail_access_modes_2016.csv', access)
    audit = dict(source_id=sid, source_sha256=record['sha256'], publication_year=2016,
        source_pdf_pages=[19, 27], visually_checked_table_columns=True,
        total_survey_respondents_persons=total, offpeak_respondents_persons=offpeak, peak_respondents_persons=peak,
        sample_strata_rows=len(strata), access_mode_rows=len(access), derived_access_table_respondents_persons=denominator,
        difference_from_full_sample_persons=total - denominator,
        strata_rounding_discrepancies=[dict(line=r['railway_line_as_printed'], travel_class=r['travel_class_as_printed'],
            reported_share_percent=r['reported_share_percent'], recomputed_share_percent=r['recomputed_share_percent'])
            for r in strata if not r['consistent_with_printed_rounding']],
        access_rounding_discrepancies=[r['mode_as_printed'] for r in access if r['consistent_with_printed_rounding'] is False],
        model_parameters_adopted=False, limitations=[
            'This 2016 report concerns a stratified sample of women rail users, not all residents, genders, trips or current travellers.',
            'Line/class/time strata overlap; all-class totals must not be added to their component class counts.',
            'The report defines off-peak to include weekends and travel against the heavy flow; it is not solely a clock-hour category.',
            'Access mode combines auto and shared auto, and combines own/private vehicles; no finer mode split is invented.',
            'The access-table denominator is derived from its numeric cells. Its difference from the full sample is unexplained here, not imputed nonresponse.',
            'Printed N/A remains missing/not-applicable, never a zero. Printed percentage discrepancies remain visible, not corrected in the source observations.',
            'Selection probabilities, population expansion weights and the full survey fieldwork dates are not established by these extracted sections.',
            'The source statement about walking time is qualitative narrative here, not a measured access-time distribution or current model coefficient.',
        ])
    Path(city.path('data/processed/acquisition/tiss_rail_access_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps(audit))


if __name__ == '__main__':
    main()
