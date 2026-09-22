"""Import a public browser response captured by the browser harness.

Use only for a catalogued public GET when ordinary verified downloads fail.
The input JSON contains id, url, final_url, content_type, retrieved, bytes and
base64 from the same successful browser fetch. It must never contain cookies,
headers, account details or a response obtained by accepting unapproved terms.

A second path (`--portal-download FILE --id ID --portal-page URL`, 9.209) imports
a file the USER downloaded from a logged-in portal whose download form a
script cannot pass (the OGD platform's captcha'd purpose form, MoSPI's NADA
login): the bytes are hashed and stored under the catalogue entry, the
provenance names the portal page and the file's own modification time as the
retrieval, and the transport says the user's browser fetched it. The catalogue
entry's own URL stays what it was; nothing from the session is recorded.
"""
import argparse
import base64
from datetime import datetime
import hashlib
import io
import json
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image
from pypdf import PdfReader
import city


def portal_download(path, source_id, portal_page, entries, allowed):
    """Import a user-downloaded portal file as `source_id`'s acquisition."""
    import csv
    from datetime import timezone
    entry = entries[source_id]
    if urlparse(portal_page).scheme != 'https' or urlparse(portal_page).hostname not in allowed:
        raise ValueError('Unapproved portal page origin')
    content = path.read_bytes()
    if not content:
        raise ValueError('Empty download')
    if entry['format'] == 'csv':
        rows = list(csv.reader(io.StringIO(content.decode('utf-8-sig'))))
        if len(rows) < 2 or any(len(r) != len(rows[0]) for r in rows[1:] if r):
            raise ValueError('Not a rectangular CSV')
    elif entry['format'] == 'pdf':
        if not content.startswith(b'%PDF-') or not PdfReader(io.BytesIO(content)).pages:
            raise ValueError('Invalid PDF')
    elif entry['format'] in ('zip', 'xlsx', 'docx'):
        if not content.startswith(b'PK'):
            raise ValueError('Not a ZIP container')
    else:
        raise ValueError('Portal import validates CSV, PDF and ZIP containers only')
    sha = hashlib.sha256(content).hexdigest()
    directory = Path(city.path('data/raw', entry['category']))
    directory.mkdir(parents=True, exist_ok=True)
    provenance = directory / ('provenance_' + entry['id'] + '.json')
    if provenance.exists():
        prior = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
        if prior['sha256'] != sha:
            raise ValueError('Immutable acquisition differs: use a new source id')
        print('VERIFIED', entry['id'], len(content))
        return
    target = directory / (entry['id'] + '_' + sha[:16] + '.' + entry['format'])
    with target.open('xb') as stream:
        stream.write(content)
    retrieved = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    record = dict(url=entry['url'], final_url=portal_page, content_type=None, retrieved=retrieved,
                  bytes=len(content), path=city.rel(str(target)), sha256=sha, source=entry['title'],
                  licence=entry['licence'], coverage=entry['coverage'],
                  producing_script='extract/import_browser_acquisition.py',
                  transport="the user's logged-in browser download from the portal page named as final_url "
                            "(a download form a script cannot pass); the file's modification time is the retrieval",
                  validation_status='acquired_unvalidated')
    provenance.write_text(json.dumps({'files': [record]}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print('ACQUIRED', entry['id'], len(content), record['path'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('response_json', type=Path, nargs='?')
    parser.add_argument('--portal-download', type=Path, help='a file the user downloaded from a logged-in portal')
    parser.add_argument('--id', help='the catalogue source id the portal file is')
    parser.add_argument('--portal-page', help='the https portal page it was downloaded from')
    args = parser.parse_args()
    if Path(city.path()).resolve() != Path(__file__).resolve().parents[1]:
        raise ValueError('Select the city that owns this script')
    entries = {e['id']:e for e in json.loads(Path(city.path('extract/sources.json')).read_text(encoding='utf-8'))['sources']}
    allowed = set(json.loads(Path(city.REPO,'.claude/settings.json').read_text(encoding='utf-8'))['sandbox']['network']['allowedDomains'])
    if args.portal_download:
        if not (args.id and args.portal_page):
            raise ValueError('--portal-download needs --id and --portal-page')
        portal_download(args.portal_download, args.id, args.portal_page, entries, allowed)
        return
    bundle = json.loads(args.response_json.read_text(encoding='utf-8'))
    bundles = bundle if isinstance(bundle,list) else [bundle]
    for data in bundles:
        if set(data) != {'id','url','final_url','content_type','retrieved','bytes','base64'}:
            raise ValueError('Unexpected browser response fields')
        entry = entries[data['id']]
        if entry.get('method','GET') != 'GET' or entry['url'] != data['url']:
            raise ValueError('Browser request does not match public catalogue GET')
        if any(urlparse(data[k]).scheme!='https' or urlparse(data[k]).hostname not in allowed
               for k in ('url','final_url')):
            raise ValueError('Unapproved browser response origin')
        if datetime.fromisoformat(data['retrieved'].replace('Z','+00:00')).tzinfo is None:
            raise ValueError('Retrieval time needs a timezone')
        content = base64.b64decode(data['base64'],validate=True)
        if not content or len(content) != data['bytes']:
            raise ValueError('Browser response length mismatch')
        if entry['format']=='pdf':
            if not content.startswith(b'%PDF-') or not PdfReader(io.BytesIO(content)).pages:
                raise ValueError('Invalid PDF')
        elif entry['format']=='png':
            with Image.open(io.BytesIO(content)) as im:
                if im.format != 'PNG':
                    raise ValueError('Unexpected image format')
                im.verify()
        elif entry['format']=='json':
            json.loads(content.decode('utf-8-sig'))
        else:
            raise ValueError('Browser import currently validates PDF, PNG and JSON only')
        sha = hashlib.sha256(content).hexdigest()
        directory = Path(city.path('data/raw',entry['category']))
        directory.mkdir(parents=True,exist_ok=True)
        provenance = directory/('provenance_'+entry['id']+'.json')
        if provenance.exists():
            prior = json.loads(provenance.read_text(encoding='utf-8'))['files'][0]
            if prior['sha256'] != sha or prior['url'] != data['url']:
                raise ValueError('Immutable acquisition differs: use a new source id')
            existing = Path(city.path(prior['path']))
            if hashlib.sha256(existing.read_bytes()).hexdigest() != sha:
                raise ValueError('Existing immutable file differs')
            print('VERIFIED',entry['id'],len(content))
            continue
        target = directory/(entry['id']+'_'+sha[:16]+'.'+entry['format'])
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest()!=sha:
                raise ValueError('Existing content-addressed path differs')
        else:
            with target.open('xb') as stream:
                stream.write(content)
        record = {k:data[k] for k in ('url','final_url','content_type','retrieved','bytes')}
        record.update(path=city.rel(str(target)),sha256=sha,source=entry['title'],
                      licence=entry['licence'],coverage=entry['coverage'],
                      producing_script='extract/import_browser_acquisition.py',
                      transport='Connected Chrome public fetch; default certificate verification',
                      validation_status='acquired_unvalidated')
        provenance.write_text(json.dumps({'files':[record]},indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print('ACQUIRED',entry['id'],len(content),record['path'])


if __name__ == '__main__':
    main()
