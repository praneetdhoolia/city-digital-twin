"""Extract the notified planning-area village list without choosing a boundary."""
from collections import Counter
import json
from pathlib import Path
import re

from pypdf import PdfReader
import city
from extract_census_controls import source, write

OUTPUT_INPUTS = {
    'data/processed/observed/mmr_ena_villages_2024.csv': [
        'data/raw/boundaries/mmr_ena_spa_notification_20240709_*.pdf'],
    'data/processed/observed/_extended_area_villages_audit.json': [
        'data/raw/boundaries/mmr_ena_spa_notification_20240709_*.pdf',
        'data/raw/boundaries/mmr_ena_raigad_plan_notice_20250918_*.pdf'],
}


def main():
    sid = 'mmr_ena_spa_notification_20240709'
    record, path = source(sid, 'boundaries')
    document = PdfReader(path)
    rows, started = [], False
    for number, page in enumerate(document.pages, 1):
        text = page.extract_text()
        if 'SCHEDULE-IV' in text:
            if started:
                raise ValueError('Multiple English Schedule-IV sections')
            started = True
        if not started:
            continue
        for line in text.splitlines():
            match = re.fullmatch(r'\s*(\d+)\s+(.+?)\s*', line)
            if not match:
                continue
            serial, description = match.groups()
            urban = description.endswith(' (Urban)')
            if urban:
                description = description[:-len(' (Urban)')]
            parts = description.rsplit(None, 2)
            if len(parts) != 3 or not all(p.isalpha() for p in parts[-2:]):
                continue
            village, taluka, district = parts
            rows.append(dict(serial_number=int(serial), village_name=village,
                             taluka_name=taluka, district_name=district,
                             district_urban_annotation=str(urban).lower(),
                             source='observed', source_id=sid, source_sha256=record['sha256'],
                             source_pdf_page=number, notification_date='2024-07-09',
                             status='planning_list_only_boundary_reconciliation_pending'))
    if not rows or [r['serial_number'] for r in rows] != list(range(1, len(rows)+1)):
        raise ValueError('Village serials are incomplete or duplicated')
    counts = dict(sorted(Counter(r['district_name'] for r in rows).items()))
    notice_sid = 'mmr_ena_raigad_plan_notice_20250918'
    notice_record, notice_path = source(notice_sid, 'boundaries')
    claims = {}
    for number, page in enumerate(PdfReader(notice_path).pages, 1):
        text = ' '.join(page.extract_text().split())
        for count, district in re.findall(r'(\d+) villages of ([A-Za-z]+) district', text):
            if district in claims and claims[district]['count'] != int(count):
                raise ValueError('Conflicting claims within notice')
            claims[district] = dict(count=int(count), source_pdf_page=number)
    if not claims or set(claims) != set(counts):
        raise ValueError('Cannot reconcile notice district names')
    differences = {name: dict(listed=counts[name], later_notice=claim['count'])
                   for name, claim in claims.items() if counts[name] != claim['count']}
    write('mmr_ena_villages_2024.csv', rows)
    audit = dict(listed_rows=len(rows), district_counts=counts,
                 continuous_serials=True, later_notice_source_id=notice_sid,
                 later_notice_sha256=notice_record['sha256'], later_notice_claims=claims,
                 district_count_conflicts=differences,
                 status='source_conflict' if differences else 'list_counts_reconciled',
                 limitations=[
                     'This Special Planning Authority list is not the whole metropolitan region.',
                     'Later KSC New Town transfers change planning responsibility, not necessarily MMR inclusion.',
                     'Names lack census codes and require historical geography reconciliation.',
                     'No village has been inserted, dropped or assigned a model polygon to resolve count conflicts.'])
    Path(city.path('data/processed/observed/_extended_area_villages_audit.json')).write_text(
        json.dumps(audit, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(audit, indent=2))


if __name__ == '__main__':
    main()
