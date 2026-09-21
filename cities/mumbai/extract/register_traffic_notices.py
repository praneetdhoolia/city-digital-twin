"""Register public road-order attachments from an immutable official index.

A listing marked 'Till Next Order' does not establish that an order remains
active. The PDF, effective dates, spatial extent and supersession need review.
The attachments of one index are one harvest archive (harvest.py), stored
uncompressed: 1,840 PDFs and JPEGs of 3.5 GB do not deflate.
"""
import argparse
import re
from pathlib import Path
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup
import requests
import harvest
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/traffic_notice_index.csv': ['data/raw/roads/mtp_notifications_*.html'],
}
LICENCE = 'Government publication; reuse terms unverified'


def notices(index_id):
    """The harvest of one index and its member attachments."""
    record, path = source(index_id, 'roads')
    which = harvest.Harvest(
        'mtp_traffic_notices_' + index_id.removeprefix('mtp_notifications_'), 'roads',
        title='Mumbai Traffic Police public road-order attachments listed in ' + index_id,
        licence=LICENCE, url=urljoin(record['url'], 'GetPublicNotice/'),
        coverage='Official road order attachments; effective dates, geometry and supersession require review.',
        discovered_from=index_id, harvester='register_traffic_notices.py', compress=False)
    return which, record, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--acquire',action='store_true')
    parser.add_argument('--index-id',default='mtp_notifications_20260101_20260918')
    args = parser.parse_args()
    which, record, path = notices(args.index_id)
    soup = BeautifulSoup(path.read_text(encoding='utf-8'),'html.parser')
    rows,entries,notice_ids = [],[],[]
    for tr in soup.select('tr'):
        anchors = tr.select('a[href^="GetPublicNotice/"]')
        if not anchors:
            continue
        cells = [td.get_text(' ',strip=True) for td in tr.select('td')]
        if len(cells)<6:
            raise ValueError('Incomplete notification row')
        hrefs = list(dict.fromkeys(a['href'] for a in anchors))
        row_ids = set()
        for attachment_index,href in enumerate(hrefs,start=1):
            match = re.match(r'GetPublicNotice/(\d+)/',href)
            format = Path(href).suffix.lower().lstrip('.')
            if not match or format not in ('pdf','jpg'):
                raise ValueError('Unexpected official attachment path')
            row_ids.add(match[1])
            source_id = 'mtp_notice_'+match[1]+('_attachment_'+str(attachment_index) if attachment_index>1 else '')
            url = quote(urljoin(record['url'],href),safe=":/()'")
            entries.append(dict(id=source_id,url=url,title=cells[1]+': '+cells[4],category='roads',format=format,
                                licence=LICENCE,transport='windows_system_tls',
                                coverage='Official road order attachment; listed '+cells[2]+'. Effective dates, geometry and supersession require review.',
                                discovered_from=args.index_id))
            rows.append(dict(source_id=source_id,notice_id=cells[1],listed_date=cells[2],listed_valid_until=cells[3],
                             subject=cells[4],notice_text=cells[5],attachment_number=attachment_index,
                             attachment_count=len(hrefs),attachment_url=url,index_source_id=args.index_id,
                             index_source_sha256=record['sha256'],source='official_notice_listing',
                             status='effective_scope_and_supersession_unresolved'))
        if len(row_ids)!=1:
            raise ValueError('Different notice ids within one index row')
        notice_ids.append(next(iter(row_ids)))
    total = re.search(r'Total\s*:\s*(\d+)',soup.get_text(' ',strip=True))
    if not total or len(notice_ids)!=int(total[1]) or len(set(notice_ids))!=len(notice_ids) or len({r['source_id'] for r in rows})!=len(rows):
        raise ValueError('Official index count mismatch')
    write('traffic_notice_index.csv',rows)
    print('REGISTERED',len(notice_ids),'notices',len(rows),'distinct attachments',flush=True)
    if args.acquire:
        with requests.Session() as session:
            # Every listed attachment is a member; the permanent orders are no
            # longer fetched first because the archive is complete or it is not.
            _, unresolved = harvest.pack(which, entries, session, harvest.allowed_domains(), 0.25)
        harvest.register(which, entries)
        return bool(unresolved)
    harvest.register(which, entries)
    return False


if __name__=='__main__':
    raise SystemExit(main())
