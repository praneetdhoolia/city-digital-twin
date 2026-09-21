"""Audit acquired order attachments without treating a listing as active law."""
from collections import defaultdict
import csv
import io
import json
from pathlib import Path

from PIL import Image
from pypdf import PdfReader
import city
import harvest
from register_traffic_notices import notices

OUTPUT_INPUTS = {
    'data/processed/acquisition/traffic_notice_audit.json': [
        'data/processed/observed/traffic_notice_index.csv',
        'data/raw/roads/mtp_traffic_notices_*.zip'],
}


def main():
    with Path(city.path('data/processed/observed/traffic_notice_index.csv')).open(encoding='utf-8',newline='') as stream:
        rows = list(csv.DictReader(stream))
    index_ids = {row['index_source_id'] for row in rows}
    if len(index_ids) != 1:
        raise ValueError('The notice index must come from one acquired listing')
    which, _, _ = notices(next(iter(index_ids)))
    listing = harvest.members(which.id, which.category)
    acquired,missing,duplicates,containers = [],[],defaultdict(list),{}
    for row in rows:
        source_id = row['source_id']
        if source_id not in listing:
            missing.append(source_id)
            continue
        record,data = harvest.source(which.id,which.category,source_id,listing)
        path = io.BytesIO(data)
        sha = record['sha256']
        duplicates[sha].append(source_id)
        if sha not in containers:
            if record['format']=='pdf':
                pdf = PdfReader(path)
                page_lengths = [len((page.extract_text() or '').strip()) for page in pdf.pages]
                if not page_lengths:
                    raise ValueError('No pages in acquired order')
                containers[sha] = dict(format='pdf',pages=len(page_lengths),
                                       extracted_characters_by_page=page_lengths,
                                       pages_without_text=sum(n==0 for n in page_lengths))
            else:
                with Image.open(path) as im:
                    containers[sha] = dict(format=im.format,width_px=im.width,height_px=im.height,
                                           requires_visual_transcription_or_ocr=True)
                    im.verify()
        acquired.append(dict(source_id=source_id,sha256=sha,bytes=record['bytes'],**containers[sha]))
    result = dict(status='acquisition_audit_not_effective_order_validation',registered_attachments=len(rows),
                  acquired_attachments=len(acquired),missing_attachment_source_ids=missing,
                  all_registered_attachments_acquired_and_readable=not missing,
                  duplicate_content_groups=[dict(sha256=sha,source_ids=ids) for sha,ids in sorted(duplicates.items()) if len(ids)>1],
                  attachments=acquired,
                  limitations=['The server did not honour the requested date filter.',
                               'An index title or generic validity label cannot establish document identity or current effect.',
                               'Scanned attachments require transcription and image checks; a text layer alone is not a validated reading.',
                               'Dates, exceptions, road geometry and superseding orders remain to be reconciled.'])
    Path(city.path('data/processed/acquisition/traffic_notice_audit.json')).write_text(
        json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(dict(registered=len(rows),acquired=len(acquired),missing=len(missing),
                          duplicate_content_groups=len(result['duplicate_content_groups']),
                          pdf_pages_without_text=sum(r.get('pages_without_text',0) for r in acquired))))


if __name__=='__main__':
    main()
