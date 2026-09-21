"""Extract dated holidays and match only the explicit CR holiday names."""
import calendar
from datetime import date
import json
from pathlib import Path
import re

import city
from extract_census_controls import source, write
from extract_population_projections import page_text

OUTPUT_INPUTS = {
    'data/processed/observed/maha_holidays_2026.csv': ['data/raw/calendar/maha_public_holidays_2026_*.pdf'],
    'data/processed/observed/cr_holiday_date_evidence_2026.csv': [
        'data/raw/calendar/maha_public_holidays_2026_*.pdf', 'data/raw/transit/cr_public_holidays_2026_*.pdf'],
    'data/processed/acquisition/holiday_evidence_audit.json': [
        'data/raw/calendar/maha_public_holidays_2026_*.pdf', 'data/raw/transit/cr_public_holidays_2026_*.pdf'],
}

# City-owned source-name equivalences, not additions to CR's holiday list.
NAMES = {
    'Republic Day': 'Republic Day',
    'Dr. Ambedkar Jayanti': 'Dr.Babasaheb Ambedkar Jayanti',
    'Maharashtra Day': 'Maharashtra Din',
    'Independence Day': 'Independence Day',
    'Gandhi Jayanti': 'Mahatma Gandhi Jayanti',
    'Christmas': 'Christmas',
    'Holi 2nd day': 'Holi (Second Day)',
    'Gudi Padwa': 'Gudhi Padwa',
    'Good Friday': 'Good Friday',
    'Ramzan -Id': 'Ramzan-Id (Id-Ul-Fitra) (Shawal-1)',
    'Ganesh Chaturthi': 'Ganesh Chaturthi',
    'Dassera': 'Dasara',
}


def extract_rows(text, page, scope, record):
    pattern = re.compile(
        r'^\s*(\d+)\.?\s+(.+?)\s{2,}(\d{2})(?:st|nd|rd|th)\s+([A-Za-z]+)\s*,\s*(\d{4})'
        r'\s{2,}(.+?)\s{2,}(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s*$', re.M)
    matches = list(pattern.finditer(text))
    rows = []
    for index, match in enumerate(matches):
        serial, name, day, month, year, saka, weekday = match.groups()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        continuation = ' '.join(text[match.end():end].split())
        if continuation:
            if not re.fullmatch(r'[A-Za-z()0-9 .-]+', continuation):
                raise ValueError('Unexpected holiday table continuation: ' + continuation)
            name += ' ' + continuation
        when = date(int(year), list(calendar.month_name).index(month), int(day))
        if calendar.day_name[when.weekday()] != weekday:
            raise ValueError('Printed weekday disagrees with date: ' + name)
        rows.append(dict(source='published_holiday', source_id='maha_public_holidays_2026',
                         source_sha256=record['sha256'], source_page=page,
                         section_scope=scope, serial=int(serial), holiday_name_as_printed=name,
                         gregorian_date=when.isoformat(), weekday_as_printed=weekday,
                         saka_date_as_printed=saka, railway_operation_status='not_established_by_state_notification'))
    return rows


def main():
    record, path = source('maha_public_holidays_2026', 'calendar')
    fifth, sixth, twelfth = (page_text(path, page) for page in (5, 6, 12))
    if 'Public Holidays, 2026.' not in fifth or '(B) For Banks' not in sixth:
        raise ValueError('Holiday publication structure changed')
    first = fifth.split('    1      Republic Day', 1)
    if len(first) != 2:
        raise ValueError('Public holiday first row changed')
    # Discard the footer after the last table row, preserving name continuations.
    table5 = ('    1      Republic Day' + first[1]).split('\n\n\n', 1)[0]
    public6, bank6 = sixth.split('(B) For Banks', 1)
    bank6 = bank6.split('By order and in the name', 1)[0].rstrip()
    extra12 = twelfth.split('By order and in the name', 1)[0].rstrip()
    rows = extract_rows(table5.rstrip(), 5, 'public_holidays', record)
    rows += extract_rows(public6.rstrip(), 6, 'public_holidays', record)
    rows += extract_rows(bank6, 6, 'banks_only', record)
    rows += extract_rows(extra12, 12, 'specified_state_and_local_government_bodies', record)
    public = [r for r in rows if r['section_scope'] == 'public_holidays']
    if [r['serial'] for r in public] != list(range(1, 25)) or len(rows) != 26:
        raise ValueError('Expected 24 public, one bank-only and one additional holiday')
    write('maha_holidays_2026.csv', rows)

    cr, cr_path = source('cr_public_holidays_2026', 'transit')
    text = page_text(cr_path, 1)
    heading = 'AS PER SUNDAY SCHEDULE.'
    if heading not in text:
        raise ValueError('CR Sunday schedule heading changed')
    rules = [line.strip() for line in text.split(heading, 1)[1].splitlines() if line.strip()]
    by_name = {r['holiday_name_as_printed']: r for r in public}
    joined = []
    matched_names = set()
    for rule in rules:
        normalised = ' '.join(rule.split())
        names = [name for name in NAMES if normalised.startswith(name)]
        common = dict(source='derived_name_match', source_id='cr_public_holidays_2026',
                      source_sha256=cr['sha256'], source_page=1, cr_rule_as_printed=rule,
                      date_source_id='maha_public_holidays_2026', date_source_sha256=record['sha256'],
                      reference_year=2026, operation_rule='Sunday_schedule',
                      application_status='date_evidence_only_not_a_complete_service_calendar')
        if len(names) == 1:
            name = names[0]
            matched_names.add(name)
            state = by_name[NAMES[name]]
            fixed = re.search(r'(\d+)(?:st|nd|rd|th)\s+(' + '|'.join(calendar.month_name[1:]) + r')\b', rule)
            if fixed:
                when = date.fromisoformat(state['gregorian_date'])
                if (when.day, calendar.month_name[when.month]) != (int(fixed[1]), fixed[2].rstrip('.')):
                    raise ValueError('CR fixed date disagrees with state holiday')
            joined.append(dict(**common, matched_state_holiday=state['holiday_name_as_printed'],
                               candidate_date=state['gregorian_date'], match_status='name_and_published_date_matched',
                               date_source_page=state['source_page']))
        elif normalised == 'Diwali 1st & 2nd day as per calander.':
            diwali = [r for r in public if r['holiday_name_as_printed'].startswith('Diwali')]
            if len(diwali) != 2:
                raise ValueError('Diwali date evidence changed')
            joined.append(dict(**common,
                               matched_state_holiday=';'.join(r['holiday_name_as_printed'] for r in diwali),
                               candidate_date=';'.join(r['gregorian_date'] for r in diwali),
                               match_status='unresolved_CR_first_and_second_day_definition', date_source_page=6))
        else:
            raise ValueError('Unmapped CR holiday rule: ' + rule)
    if matched_names != set(NAMES) or len(joined) != 13:
        raise ValueError('CR holiday rule coverage changed')
    write('cr_holiday_date_evidence_2026.csv', joined)
    audit = dict(state_rows=len(rows), public_holiday_names=len(public),
                 distinct_public_dates=len({r['gregorian_date'] for r in public}),
                 cr_rules=len(joined), matched_rules=len(matched_names), unresolved_rules=1,
                 all_printed_weekdays_match=True, model_calendar_adopted=False,
                 limitations=[
                     'The CR holiday sheet is undated; its acquisition identifier does not establish annual validity.',
                     'State public holidays are not automatically railway holidays, school closures or zero-demand days.',
                     'Two state Diwali holidays are not consecutive; CR first/second-day wording still needs an operating notice.',
                     'Festival amendments and actual railway notices, including lunar-date changes, remain to be reconciled.',
                     'The bank-only and additional government-body holiday have distinct applicability.',
                     'Saka dates are transcribed from the English table, not cross-validated against the Marathi table.',
                 ])
    Path(city.path('data/processed/acquisition/holiday_evidence_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({k: v for k, v in audit.items() if k != 'limitations'}))


if __name__ == '__main__':
    main()
