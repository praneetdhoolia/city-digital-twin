"""Keep dated train capacity, service counts and stock receipts distinct."""
import json
from pathlib import Path
import re

from bs4 import BeautifulSoup
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/suburban_first_ac_capacity_2017.csv': ['data/raw/rail/pib_first_ac_emu_2017_*.html'],
    'data/processed/observed/suburban_service_counts_202604.csv': [
        'data/raw/rail/pib_suburban_services_20260402_*.html', 'data/raw/transit/pib_suburban_capacity_20260313_*.html'],
    'data/processed/observed/suburban_stock_claims_202604.csv': [
        'data/raw/rail/pib_suburban_services_20260402_*.html', 'data/raw/transit/pib_suburban_capacity_20260313_*.html'],
    'data/processed/acquisition/suburban_fleet_claims_audit.json': [
        'data/raw/rail/pib_first_ac_emu_2017_*.html', 'data/raw/rail/pib_suburban_services_20260402_*.html',
        'data/raw/transit/pib_suburban_capacity_20260313_*.html'],
}


def publication(sid, release_id, category='rail'):
    record, path = source(sid, category)
    soup = BeautifulSoup(path.read_bytes(), 'html.parser')
    body = soup.select_one('.innner-page-main-about-us-content-right-part')
    if body is None:
        raise ValueError('PIB article body missing')
    text = ' '.join(body.get_text(' ', strip=True).split())
    if 'Release ID: ' + release_id not in text:
        raise ValueError('PIB release identity changed')
    return record, body, text


def one(pattern, text):
    matches = re.findall(pattern, text)
    if len(matches) != 1:
        raise ValueError('Expected one publication match for ' + pattern)
    return matches[0]


def main():
    sid = 'pib_first_ac_emu_2017'
    record, body, text = publication(sid, '1514002')
    if '24 DEC 2017' not in text:
        raise ValueError('First AC publication date changed')
    cars = int(one(r'consisting of (\d+)-car', text))
    tables = [t for t in body.find_all('table') if 'Driving Motor Coach' in t.get_text()]
    if len(tables) != 1:
        raise ValueError('Ambiguous coach capacity table')
    table = [[' '.join(c.get_text(' ', strip=True).split()) for c in tr.find_all(['td', 'th'])]
             for tr in tables[0].find_all('tr')]
    if table[0] != ['Coach Type', 'Seating Capacity', 'Standing capacity', 'Total']:
        raise ValueError('Coach table column meanings changed')
    if [r[0] for r in table[1:]] != ['Driving Motor Coach', 'Trailer Coach', 'Non-Driving Motor Coach']:
        raise ValueError('Coach table type coverage changed')
    capacities, checks = [], []

    def capacity(name, seats, standing, total, unit, anchor):
        residual = total - seats - standing
        checks.append(dict(scope=name, residual_passengers=residual))
        if residual:
            raise ValueError('Published capacity components disagree: ' + name)
        capacities.append(dict(source='published_design_capacity', source_id=sid,
                               source_sha256=record['sha256'], publication_date='2017-12-24',
                               fleet_scope='first_BHEL_12_car_AC_rake_introduced_on_WR_2017',
                               capacity_scope=name, seats_persons=seats, standing_places_persons=standing,
                               total_capacity_persons=total, units=unit, formation_cars=cars,
                               source_anchor=anchor, standing_density_persons_per_m2='',
                               standing_density_status='not_stated_in_this_publication',
                               operational_assignment_status='historical_design_not_assigned_to_current_trips'))

    for name, seats, standing, total in table[1:]:
        capacity(name, int(seats), int(standing), int(total), 'persons_per_coach', 'Passenger Carrying Capacity Coach Type-wise')
    total, seats, standing = map(int, one(
        r'total capacity of the rake is (\d+) passengers with (\d+) seating capacity and (\d+) standing capacity', text))
    capacity('Complete rake', seats, standing, total, 'persons_per_rake', 'Paragraph following coach capacity table')
    write('suburban_first_ac_capacity_2017.csv', capacities)

    sid = 'pib_suburban_services_20260402'
    record, _, text = publication(sid, '2248576')
    if '02 APR 2026' not in text:
        raise ValueError('Service publication date changed')
    all_services = int(one(r'At present, (\d+) EMU local services including AC EMU services', text))
    all_ac = int(one(r'With \d+ Sub Urban Services \((\d+) AC Locals\)', text))
    wr, wr_ac = map(int, one(r'Western Railway operates (\d+) services including (\d+) AC services', text))
    cr, cr_ac = map(int, one(r'Central Railway operates (\d+) services including (\d+) AC services', text))
    if wr + cr != all_services or wr_ac + cr_ac != all_ac:
        raise ValueError('Railway service components do not match combined counts')
    common = dict(source_id=sid, source_sha256=record['sha256'], publication_date='2026-04-02',
                  reference_day='not_explicitly_dated_beyond_present_tense_publication',
                  current_trip_assignment_status='unresolved')
    services = []
    for operator, count, ac in (('WR', wr, wr_ac), ('CR', cr, cr_ac), ('WR+CR', all_services, all_ac)):
        for category, value in (('All EMU local services', count), ('AC EMU local services', ac)):
            services.append(dict(**common, source='published_operational_count', operator=operator,
                                 category=category, daily_services_count=value,
                                 counting_unit='train_service_not_physical_rake_or_passenger',
                                 overlap='AC is a subset of All; WR+CR overlaps both operators',
                                 source_anchor='Opening paragraph; combined AC count in release heading'))
    # the Parliament answer of 13 March 2026 (pib_suburban_capacity_20260313):
    # the trains handled daily in the Mumbai area, rounded as printed, a second
    # dated count beside the operators' own of 2 April
    march_sid = 'pib_suburban_capacity_20260313'
    march_record, _, march_text = publication(march_sid, '2239780', 'transit')
    if '13 MAR 2026' not in march_text:
        raise ValueError('March capacity publication date changed')
    march_suburban = int(one(r'about (\d[\d,]*) suburban trains are handled daily', march_text).replace(',', ''))
    march_express = int(one(r'about (\d+) originating Mail/Express trains', march_text))
    march_common = dict(source_id=march_sid, source_sha256=march_record['sha256'], publication_date='2026-03-13',
                        reference_day='present_tense_publication_rounded_as_printed',
                        current_trip_assignment_status='unresolved')
    for category, value in (('All suburban trains handled daily, Mumbai area (about)', march_suburban),
                            ('Originating Mail/Express trains daily, Mumbai area (about)', march_express)):
        services.append(dict(**march_common, source='published_operational_count', operator='WR+CR',
                             category=category, daily_services_count=value,
                             counting_unit='train_handled_not_physical_rake_or_passenger',
                             overlap='a rounded Parliament answer; the 2 April operator counts sum to %d' % all_services,
                             source_anchor='Opening paragraph'))
    write('suburban_service_counts_202604.csv', services)
    receipts = one(r'During the year 2025-26, four (\d+)-car rakes of AC EMU \((\d+) each to CR & WR\) and one (\d+)-car rake of Non-AC EMU to WR has been received', text)
    ac_cars, each, non_ac_cars = map(int, receipts)
    if each * 2 != 4:
        raise ValueError('Per-operator AC receipts do not match published four-rake total')
    stocks = []
    for operator, category, count, formation in (('CR', 'AC EMU', each, ac_cars),
                                                ('WR', 'AC EMU', each, ac_cars),
                                                ('WR', 'Non-AC EMU', 1, non_ac_cars)):
        stocks.append(dict(**common, source='published_stock_receipt', operator=operator,
                           category=category, rakes_count=count, formation_cars=formation,
                           reference_period='FY2025-26', status='received_not_total_active_fleet',
                           source_anchor='Additional rakes item 1'))
    sanctioned, formation = map(int, one(r'(\d+) rakes of (\d+) cars each with doors have been sanctioned', text))
    stocks.append(dict(**common, source='published_procurement_status', operator='MRVC MUTP-III and IIIA',
                       category='EMU with doors', rakes_count=sanctioned, formation_cars=formation,
                       reference_period='as_reported_in_publication', status='sanctioned_procurement_not_operational_fleet',
                       source_anchor='New generation trains paragraph'))
    march_sanctioned, march_formation = map(int, one(r'(\d+) rakes of (\d+) cars each with doors have been sanctioned', march_text))
    if (march_sanctioned, march_formation) != (sanctioned, formation):
        raise ValueError('The two Parliament answers disagree on the sanctioned rakes')
    stocks.append(dict(**march_common, source='published_procurement_status', operator='MRVC MUTP-III and IIIA',
                       category='EMU with doors', rakes_count=march_sanctioned, formation_cars=march_formation,
                       reference_period='as_reported_in_publication', status='sanctioned_procurement_not_operational_fleet',
                       source_anchor='Passenger carrying capacity paragraph'))
    write('suburban_stock_claims_202604.csv', stocks)
    audit = dict(capacity_rows=len(capacities), capacity_checks=checks, service_rows=len(services),
                 service_totals=dict(all_services=all_services, ac_subset=all_ac, operator_sum_status='exact',
                                     march_2026_trains_handled_daily_rounded=march_suburban),
                 stock_claim_rows=len(stocks), model_parameters_adopted=False,
                 limitations=[
                     'The 2017 capacity statement describes the first BHEL AC rake, not every later rake or an observed passenger load.',
                     'The standing-density basis is unspecified here. A different technical specification cannot silently supply it.',
                     'Coach types and complete-rake capacity have different units and must not be added together.',
                     'The release distinguishes general and ladies coaches and reserved seats; aggregate capacity alone does not model eligibility or compartment crowding.',
                     'The original 2018 Monday-Friday service and maintenance calendar is historical, not a calendar for current AC services.',
                     'The 2026 publication says present service counts but does not date an individual operating day or supply exceptions.',
                     'Rake receipts, total services and sanctioned procurements are different quantities; no trip-specific formation is inferred.',
                 ])
    Path(city.path('data/processed/acquisition/suburban_fleet_claims_audit.json')).write_text(
        json.dumps(audit, indent=2) + '\n', encoding='utf-8', newline='\n')
    print(json.dumps({key: audit[key] for key in ('capacity_rows', 'service_rows', 'service_totals', 'stock_claim_rows')}))


if __name__ == '__main__':
    main()
