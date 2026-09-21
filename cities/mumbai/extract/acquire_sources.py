"""Acquire catalogued public inputs with immutable bytes and per-file provenance.

Select this city with CITYSIM_CITY. Downloads are evidence, not validated model
inputs. The catalogue records coverage and licence limitations separately.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from urllib.parse import urlparse, urlencode

import requests
import city


def check_request(entry, allowed):
    """Refuse anything but an observed public read query on an allowlisted host."""
    if Path(city.path()).resolve() != Path(__file__).resolve().parents[1]:
        raise ValueError('CITYSIM_CITY must select the city that owns this acquisition script')
    url = entry['url']
    method = entry.get('method', 'GET')
    if method not in ('GET', 'POST'):
        raise ValueError('unsupported acquisition method')
    public_read_queries = {
        'https://portal.mmrcl.com/en/api/v2/fare-calculator/',
        *('https://nmmtitmsmobileapi.amnex.co.in/api/' + path for path in (
            'TimeTable/GetAllRoutes', 'TimeTable/GetScheduelByRoute',
            'TimeTable/GetScheduelDetail', 'TimeTable/GetScheduelByStation',
            'Masters/GetStationList', 'Ticket/GetAllActiveServiceTypes',
            'BusTracking/GetBusList', 'BusTracking/GetVehicleTripDetails_v2',
            'BusTracking/GetRoutePathData', 'BusTracking/SearchByRouteDetails_v4',
            'NearByStation/GetNearByStationSchedule', 'PIS/GetPlatformWiseETA')),
    }
    public_form_queries = {
        'https://esankhyiki.mospi.gov.in/dashboard/EC/filterDistrict6',
        'https://esankhyiki.mospi.gov.in/dashboard/EC/submitForm6',
    }
    form = entry.get('request_form')
    valid_form = (url in public_form_queries and isinstance(form, dict) and
                  set(form) <= {'ec', 'state', 'param1', 'top5opt', 'nop', 'sof',
                                'activity', 'ownership', 'sector', 'pageNum', 'randomnum'} and
                  all(isinstance(v, str) for v in form.values()) and
                  form.get('ec') == '6')
    valid_form = valid_form or (
        url == 'https://mtperp.mahatrafficechallan.gov.in/PublicNotice.htm' and
        isinstance(form, dict) and set(form) == {'fDate','tDate'} and
        all(isinstance(v,str) and re.fullmatch(r'\d{2}/\d{2}/\d{4}',v) for v in form.values()))
    valid_form = valid_form or (
        url == 'https://mbmcwebportal.amnex.com/ListofRoutesLocations/PlotRoutesOnMap/' and
        isinstance(form, dict) and set(form) == {'routeid'} and
        isinstance(form['routeid'], str) and re.fullmatch(r'[1-9]\d*', form['routeid']))
    if entry.get('request_json') is not None and form is not None:
        raise ValueError('A request cannot have both JSON and form bodies')
    if method == 'GET' and (form is not None or entry.get('request_json') is not None):
        raise ValueError('GET acquisition cannot carry a request body')
    if method == 'POST' and not ((url in public_read_queries and
                                  isinstance(entry.get('request_json'), dict)) or valid_form):
        raise ValueError('POST acquisition is restricted to observed public information queries')
    if urlparse(url).hostname not in allowed:
        raise ValueError('source host is not in the repository acquisition allowlist')
    return url, method, form


def check_magic(entry, magic):
    """The declared format must match the bytes; an error page is not a PDF."""
    if entry['format'] == 'pdf' and not magic.startswith(b'%PDF'):
        raise ValueError('response is not a PDF')
    if entry['format'] in ('zip', 'xlsx', 'docx') and not magic.startswith(b'PK'):
        raise ValueError('response is not a ZIP container')
    if entry['format'] == 'xls' and not magic.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
        raise ValueError('response is not an Excel binary container')
    if entry['format'] == 'tif' and magic[:4] not in (b'II*\x00', b'MM\x00*', b'II+\x00', b'MM\x00+'):
        raise ValueError('response is not a TIFF container')


def check_parses(entry, stream):
    """A declared JSON, XML or image response must parse. Leaves `stream` at 0."""
    stream.seek(0)
    if entry['format'] == 'json':
        json.loads(stream.read().decode('utf-8-sig'))
    elif entry['format'] == 'xml':
        ET.parse(stream)
    elif entry['format'] in ('png', 'jpg'):
        from PIL import Image
        with Image.open(stream) as source_image:
            source_image.verify()
    stream.seek(0)


def request_record(entry, method, form, record):
    if method != 'GET':
        body_key = 'request_form' if form is not None else 'request_json'
        record.update(method=method, **{body_key: entry[body_key]})
    return record


def fetch(entry, session, allowed, sink):
    """Download one catalogued response into `sink` (a seekable binary file).

    Returns the provenance record of the bytes: url, final url, licence,
    retrieval time, sha256, size and content type. Nothing lands under
    data/raw here - `store` keeps a loose file, a harvest keeps an archive.
    """
    url, method, form = check_request(entry, allowed)
    if entry.get('transport') == 'windows_system_tls':
        return fetch_system_tls(entry, allowed, sink)
    response = session.request(method, url, json=entry.get('request_json'), data=form,
                               headers={'X-Requested-With': 'XMLHttpRequest'} if form is not None else None,
                               stream=True, timeout=(20, 60))
    response.raise_for_status()
    if urlparse(response.url).hostname not in allowed:
        response.close()
        raise ValueError('redirect host needs an acquisition allowlist entry: ' + urlparse(response.url).hostname)
    digest = hashlib.sha256()
    size = 0
    for chunk in response.iter_content(chunk_size=1024*1024):
        sink.write(chunk)
        digest.update(chunk)
        size += len(chunk)
    response.close()
    if not size:
        raise ValueError('empty response')
    sink.seek(0)
    check_magic(entry, sink.read(16))
    check_parses(entry, sink)
    record = dict(url=url, final_url=response.url,
                  source=entry['title'], licence=entry['licence'],
                  retrieved=datetime.now(timezone.utc).isoformat(),
                  sha256=digest.hexdigest(), bytes=size, content_type=response.headers.get('Content-Type'),
                  producing_script='extract/acquire_sources.py',
                  validation_status='acquired_unvalidated', coverage=entry['coverage'])
    return request_record(entry, method, form, record)


def store(entry, directory, provenance, stream, record):
    """Keep the fetched bytes as one immutable loose file beside its provenance."""
    target = directory / (entry['id'] + '_' + record['sha256'][:16] + '.' + entry['format'])
    if not target.exists():
        stream.seek(0)
        with target.open('xb') as output:
            while chunk := stream.read(1024*1024):
                output.write(chunk)
    record = dict(path=city.rel(str(target)), **record)
    provenance.write_text(json.dumps({'files':[record]},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return record


def previous_record(entry, provenance):
    """The verified record of an acquisition already made under this id, or None."""
    if not provenance.exists():
        return None
    previous = json.loads(provenance.read_text(encoding='utf-8'))
    record = previous['files'][0]
    target = Path(city.path(record['path']))
    if record['url'] != entry['url']:
        raise ValueError('source URL changed: use a new acquisition id')
    if (record.get('method', 'GET') != entry.get('method', 'GET') or
            record.get('request_json') != entry.get('request_json') or
            record.get('request_form') != entry.get('request_form')):
        raise ValueError('source request changed: use a new acquisition id')
    if not target.exists():
        raise ValueError('previous immutable acquisition is missing')
    with target.open('rb') as stream:
        matches = hashlib.file_digest(stream, 'sha256').hexdigest() == record['sha256']
    if not matches:
        raise ValueError('previous immutable acquisition is missing or has changed')
    return record


def acquire(entry, session, allowed):
    """One catalogue entry to one loose file under data/raw/<category>/ with its provenance."""
    check_request(entry, allowed)
    directory = Path(city.path('data/raw', entry['category']))
    directory.mkdir(parents=True, exist_ok=True)
    provenance = directory / ('provenance_' + entry['id'] + '.json')
    record = previous_record(entry, provenance)
    if record is not None:
        return record
    with tempfile.TemporaryFile() as stream:
        record = fetch(entry, session, allowed, stream)
        return store(entry, directory, provenance, stream, record)


def fetch_system_tls(entry, allowed, sink):
    """Use the verified Windows trust store for servers with incomplete chains.

    Certificate verification remains enabled. URL and output path are passed as
    environment data, never interpolated into PowerShell code.
    """
    timeout_seconds = entry.get('download_timeout_seconds', 150)
    if (isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, int)
            or not 1 <= timeout_seconds <= 1800):
        raise ValueError('Download timeout must be an integer from 1 to 1800 seconds')
    with tempfile.TemporaryDirectory(prefix='city-data-') as temporary:
        output = Path(temporary, 'download')
        env = dict(os.environ, ACQUISITION_SOURCE_URL=entry['url'],
                   ACQUISITION_OUTPUT_PATH=str(output),
                   ACQUISITION_TIMEOUT_SECONDS=str(timeout_seconds),
                   ACQUISITION_METHOD=entry.get('method', 'GET'),
                   ACQUISITION_FORM_BODY=urlencode(entry.get('request_form', {})),
                   ACQUISITION_REQUEST_JSON=json.dumps(entry.get('request_json')))
        command = ('$ErrorActionPreference="Stop"; $ProgressPreference="SilentlyContinue"; '
                   '$params=@{Method=$env:ACQUISITION_METHOD}; '
                   'if ($env:ACQUISITION_METHOD -eq "POST") {'
                   'if ($env:ACQUISITION_FORM_BODY) {'
                   '$params.Body=$env:ACQUISITION_FORM_BODY; '
                   '$params.ContentType="application/x-www-form-urlencoded"; '
                   '$params.Headers=@{"X-Requested-With"="XMLHttpRequest"} '
                   '} else {'
                   '$params.Body=$env:ACQUISITION_REQUEST_JSON; '
                   '$params.ContentType="application/json"}}; '
                   '$r=Invoke-WebRequest -UseBasicParsing -Uri $env:ACQUISITION_SOURCE_URL '
                   '-OutFile $env:ACQUISITION_OUTPUT_PATH -PassThru -TimeoutSec ([int]$env:ACQUISITION_TIMEOUT_SECONDS) @params; '
                   '@{final_url=$r.BaseResponse.ResponseUri.AbsoluteUri; '
                   'content_type=$r.Headers["Content-Type"]} | ConvertTo-Json -Compress')
        result = subprocess.run(['powershell.exe','-NoProfile','-NonInteractive','-Command',command],
                                env=env,capture_output=True,text=True,timeout=timeout_seconds + 30,
                                creationflags=subprocess.CREATE_NO_WINDOW)
        if result.returncode:
            raise ValueError(result.stderr.strip()[:600])
        metadata = json.loads(result.stdout)
        if urlparse(metadata['final_url']).hostname not in allowed:
            raise ValueError('redirect host needs an acquisition allowlist entry')
        if not output.stat().st_size:
            raise ValueError('empty response')
        digest = hashlib.sha256()
        with output.open('rb') as source:
            while chunk := source.read(1024*1024):
                sink.write(chunk)
                digest.update(chunk)
        sink.seek(0)
        check_magic(entry, sink.read(16))
        check_parses(entry, sink)
        record = dict(url=entry['url'],**metadata,
                      source=entry['title'],licence=entry['licence'],
                      retrieved=datetime.now(timezone.utc).isoformat(),sha256=digest.hexdigest(),
                      bytes=output.stat().st_size,producing_script='extract/acquire_sources.py',
                      validation_status='acquired_unvalidated',coverage=entry['coverage'],
                      transport='Windows system TLS; certificate verification enabled')
        return request_record(entry, entry.get('method', 'GET'), entry.get('request_form'), record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id', action='append', help='Acquire selected catalogue ids only.')
    args = parser.parse_args()
    catalogue = json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))
    settings = json.loads(Path(city.REPO, '.claude/settings.json').read_text(encoding='utf-8'))
    allowed = set(settings['sandbox']['network']['allowedDomains'])
    failures = []
    with requests.Session() as session:
        session.headers['User-Agent'] = 'city-digital-twin research acquisition/1.0'
        for entry in catalogue['sources']:
            if args.id and entry['id'] not in args.id:
                continue
            if entry.get('kind') == 'harvest':
                # many queries, one archive: acquired by the harvester the entry
                # names (harvest.py), which owns the member list
                print('HARVEST', entry['id'], 'is acquired by', entry['harvester'], flush=True)
                continue
            try:
                record = acquire(entry, session, allowed)
                print('ACQUIRED', entry['id'], record['bytes'], record['path'], flush=True)
            except (requests.RequestException, ValueError, OSError, KeyError,
                    ET.ParseError, subprocess.TimeoutExpired) as exc:
                failures.append({'id':entry['id'],'url':entry['url'],'error':str(exc)})
                print('UNOBTAINED', entry['id'], str(exc), flush=True)
    log = Path(city.path('data/raw/_acquisition_attempts.json'))
    prior = json.loads(log.read_text(encoding='utf-8')) if log.exists() else []
    prior.append({'retrieved':datetime.now(timezone.utc).isoformat(),'failures':failures})
    log.write_text(json.dumps(prior,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return bool(failures)


if __name__ == '__main__':
    raise SystemExit(main())
