"""Acquire MBMT passenger queries and documents linked by its public websites.

The per-route passenger queries are three harvests (harvest.py): route
details, route stops and route alignments, one archive each. The operator
documents and the map client are loose single acquisitions.
"""
import argparse
import json
from pathlib import Path
import re
import time
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup
import requests
import city
import harvest
from acquire_sources import acquire
from acquire_nmmt_schedules import register
from extract_census_controls import source

LICENCE = 'Operator/vendor publication; reuse terms unverified'
DETAILS = harvest.Harvest(
    'mbmt_route_details', 'transit',
    title='MBMT public route details, one passenger query per route',
    licence=LICENCE, url='https://mbmcwebportal.amnex.com/ListofRoutes/GetRoutesDetails',
    coverage='Passenger information snapshot. Dates, completeness and current operation need validation.',
    discovered_from='mbmt_routes_page', harvester='acquire_mbmt_sources.py')
STOPS = harvest.Harvest(
    'mbmt_route_stops', 'transit',
    title='MBMT public route stops, one passenger query per route',
    licence=LICENCE, url='https://mbmcwebportal.amnex.com/ListofRoutes/getStation',
    coverage='Passenger information snapshot. Dates, completeness and current operation need validation.',
    discovered_from='mbmt_routes_page', harvester='acquire_mbmt_sources.py')
ALIGNMENTS = harvest.Harvest(
    'mbmt_route_alignments', 'transit',
    title='MBMT public route alignments, one passenger-map query per route',
    licence=LICENCE, url='https://mbmcwebportal.amnex.com/ListofRoutesLocations/PlotRoutesOnMap/', method='POST',
    coverage='Passenger map geometry. Direction, road matching and current operation need validation.',
    discovered_from='mbmt_public_map_script', harvester='acquire_mbmt_sources.py')
HARVEST_OF_KIND = {'details': DETAILS, 'stops': STOPS, 'path': ALIGNMENTS}


def entries():
    """(harvest members by kind, loose entries)."""
    _, path = source('mbmt_routes', 'transit')
    routes = json.loads(path.read_text(encoding='utf-8-sig'))
    ids = [row['RouteId'] for row in routes]
    if any(type(i) is not int or i <= 0 for i in ids) or len(ids) != len(set(ids)):
        raise ValueError('Route directory IDs are invalid or duplicated')
    record, path = source('mbmt_routes_page', 'transit')
    text = path.read_text(encoding='utf-8-sig')
    queries = re.findall(r"url:\s*['\"](/ListofRoutes/(?:GetRoutesDetails|getStation))['\"]", text)
    if len(queries) != 2 or len(set(queries)) != 2:
        raise ValueError('Expected observed detail and stop queries in passenger client')
    members = {'details': [], 'stops': [], 'path': []}
    for route_id in sorted(ids):
        for endpoint in sorted(queries):
            kind = 'details' if endpoint.endswith('GetRoutesDetails') else 'stops'
            which = HARVEST_OF_KIND[kind]
            if urljoin(record['url'], endpoint) != which.url:
                raise ValueError('Observed passenger query moved: ' + endpoint)
            members[kind].append(dict(id=f'mbmt_route_{kind}_{route_id}', category='transit', format='json',
                                      url=which.url + '?' + urlencode({'RouteId': route_id}),
                                      title=f'MBMT public route {kind} {route_id}',
                                      licence=LICENCE, coverage=which.coverage,
                                      discovered_from='mbmt_routes_page'))
    loose = []
    soup = BeautifulSoup(text, 'html.parser')
    scripts = [s['src'] for s in soup.find_all('script', src=True)
               if s['src'].endswith('/Map_Common.js')]
    if len(scripts) != 1:
        raise ValueError('Public map script link is ambiguous')
    loose.append(dict(id='mbmt_public_map_script', category='transit', format='js',
                      url=urljoin(record['url'], scripts[0]), title='MBMT public passenger map client',
                      licence=LICENCE, coverage='Read-only endpoint discovery; never execute downloaded code.',
                      discovered_from='mbmt_routes_page'))
    script_provenance = Path(city.path('data/raw/transit/provenance_mbmt_public_map_script.json'))
    if script_provenance.exists():
        script_record, script_path = source('mbmt_public_map_script', 'transit')
        script_text = script_path.read_text(encoding='utf-8-sig')
        endpoints = set(re.findall(r"url:\s*DomainUrl\(\)\s*\+\s*'([^']+)'", script_text))
        if endpoints != {'ListofRoutesLocations/PlotRoutesOnMap/'}:
            raise ValueError('Public map query endpoint changed')
        endpoint = next(iter(endpoints))
        if urljoin(script_record['url'], '/' + endpoint) != ALIGNMENTS.url:
            raise ValueError('Public map query moved')
        for route_id in sorted(ids):
            members['path'].append(dict(id=f'mbmt_route_path_{route_id}', category='transit', format='json',
                                        method='POST', url=ALIGNMENTS.url,
                                        request_form={'routeid': str(route_id)},
                                        title=f'MBMT public route alignment {route_id}',
                                        licence=LICENCE, coverage=ALIGNMENTS.coverage,
                                        discovered_from='mbmt_public_map_script'))
    record, path = source('mbmt_operator_profile', 'transit')
    soup = BeautifulSoup(path.read_text(encoding='utf-8-sig'), 'html.parser')
    patterns = {
        'mbmt_budget_2024_25': 'Transport Department Budget 2024-2025',
        'mbmt_bus_maintenance_agreement': 'Agreement regarding maintenance and repair responsibility of buses',
        'mbmt_electric_bus_agreement': 'Bus Operator Agreement for supply, operation, and maintenance of electric buses',
        'mbmt_ticket_monitoring_agreement': 'Agreement for ticket collection supervision and monitoring',
        'mbmt_diesel_bus_work_order': 'Work Order_346',
        'mbmt_service_notice_20240314': 'new bus route from 14/03/2024',
    }
    for sid, pattern in patterns.items():
        matches = [a for a in soup.find_all('a', href=True)
                   if pattern in ' '.join(a.get_text(' ', strip=True).split())]
        if len(matches) != 1:
            raise ValueError('Operator document link is missing or ambiguous: ' + sid)
        loose.append(dict(id=sid, category='transit', format='pdf',
                          url=urljoin(record['url'], matches[0]['href']),
                          title='MBMT ' + ' '.join(matches[0].get_text(' ', strip=True).split()),
                          licence='Municipal/operator publication; reuse terms unverified',
                          coverage='Published contract, budget or notice. Procurement and planned service are not current operating observations.',
                          discovered_from='mbmt_operator_profile'))
    return members, loose


def check_list(item, data):
    if not isinstance(json.loads(data.decode('utf-8-sig')), list):
        raise ValueError('Passenger query did not return a list')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pause-seconds', type=float, default=0.25, help='Request courtesy delay only.')
    args = parser.parse_args()
    if not 0 <= args.pause_seconds <= 60:
        raise ValueError('Request pause must be between zero and sixty seconds')
    allowed = harvest.allowed_domains()
    members, loose = entries()
    # A fresh checkout needs the linked client before its map query can be
    # discovered. Finish that dependency in this invocation, not a second run.
    if not Path(city.path('data/raw/transit/provenance_mbmt_public_map_script.json')).exists():
        script = next(e for e in loose if e['id'] == 'mbmt_public_map_script')
        register([script])
        with requests.Session() as session:
            session.headers['User-Agent'] = 'city-digital-twin public transport research/1.0'
            acquire(script, session, allowed)
        members, loose = entries()
    register(loose)
    failures = []
    with requests.Session() as session:
        session.headers['User-Agent'] = 'city-digital-twin public transport research/1.0'
        for entry in loose:
            cached = Path(city.path('data/raw/transit', 'provenance_' + entry['id'] + '.json')).exists()
            try:
                record = acquire(entry, session, allowed)
                print('ACQUIRED', entry['id'], record['bytes'], flush=True)
            except (requests.RequestException, ValueError, OSError) as exc:
                failures.append(entry['id'])
                print('UNRESOLVED', entry['id'], type(exc).__name__, str(exc)[:180], flush=True)
            if not cached:
                time.sleep(args.pause_seconds)
        for kind, which in HARVEST_OF_KIND.items():
            if not members[kind]:
                continue
            _, unresolved = harvest.pack(which, members[kind], session, allowed, args.pause_seconds,
                                         check=check_list)
            harvest.register(which, members[kind])
            failures.extend(unresolved)
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
