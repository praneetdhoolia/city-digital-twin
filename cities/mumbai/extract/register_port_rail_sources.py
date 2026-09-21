"""Register all rail statistics PDFs linked by the acquired Mumbai Port index.

The statistics PDFs of one index are one harvest archive (harvest.py).
"""
import argparse
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
import requests
import harvest
from extract_census_controls import source

INDEX_ID = 'mumbai_port_rail_traffic_index_20260918'
STATISTICS = harvest.Harvest(
    'mumbai_port_rail_statistics', 'freight',
    title='Mumbai Port rail traffic statistics, every PDF linked by the port\'s rail traffic index',
    licence='Government/operator publication; reuse terms unverified',
    url='https://mumbaiport.gov.in/',
    coverage='Published rail statistics; preserve loaded/empty and received/sent definitions. Not a train timetable or cargo-to-vehicle conversion.',
    discovered_from=INDEX_ID, harvester='register_port_rail_sources.py', compress=False)


def entries():
    record, path = source(INDEX_ID, 'freight')
    soup = BeautifulSoup(path.read_text(encoding='utf-8'), 'html.parser')
    found = {}
    for table in soup.find_all('table'):
        heading = ''
        for row in table.find_all('tr'):
            links = [a for a in row.select('a[href]') if urlparse(a['href']).path.lower().endswith('.pdf')]
            text = row.get_text(' ', strip=True)
            if not links:
                heading = text
                continue
            prefix = text.split(links[0].get_text(' ', strip=True), 1)[0].strip(' :')
            if prefix:
                heading = prefix
            for link in links:
                url = urljoin(record['url'], link['href'])
                identifier = Path(urlparse(url).path).stem
                if not identifier.isdigit():
                    raise ValueError('Unexpected attachment identifier: ' + identifier)
                sid = 'mumbai_port_rail_' + identifier
                found[sid] = dict(id=sid, category='freight', format='pdf', url=url,
                                  title='Mumbai Port ' + heading + ': ' + link.get_text(' ', strip=True),
                                  licence=STATISTICS.licence, coverage=STATISTICS.coverage,
                                  discovered_from=INDEX_ID, transport='windows_system_tls')
    if not found:
        raise ValueError('No public rail attachments found in acquired index')
    return [found[key] for key in sorted(found)]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire', action='store_true')
    args = parser.parse_args()
    members = entries()
    print('REGISTERED', len(members), flush=True)
    unresolved = []
    if args.acquire:
        with requests.Session() as session:
            _, unresolved = harvest.pack(STATISTICS, members, session, harvest.allowed_domains(), .25)
    harvest.register(STATISTICS, members)
    return bool(unresolved)


if __name__ == '__main__':
    raise SystemExit(main())
