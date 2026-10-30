#!/usr/bin/env python3
"""Reconcile original malformed-dimension XLSX directly to frozen CSV.

ZIP/XML inspection intentionally ignores the erroneous dimension=A1 marker;
works without openpyxl/pandas and does not mutate either source file.
"""
from __future__ import annotations
import csv,datetime,hashlib,json,sys,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

HERE=Path(__file__).resolve().parent
NS={'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def check(xlsx,normalized=HERE/'extra5_authoritative_2026.csv'):
    xlsx=Path(xlsx); normalized=Path(normalized)
    with zipfile.ZipFile(xlsx,'r') as z:
        root=ET.fromstring(z.read('xl/worksheets/sheet1.xml'))
    found=[]
    for rr in root.findall('.//x:sheetData/x:row',NS):
        cells={''.join(c for c in el.get('r','') if c.isalpha()):''.join(el.itertext()).strip()
               for el in rr.findall('x:c',NS)}
        if not cells.get('A','').isdigit():continue
        draw=int(cells['A'])
        nums=tuple(int(cells[c]) for c in 'DEFGH')
        assert len(set(nums))==5 and min(nums)>=1 and max(nums)<=35
        date=datetime.datetime.strptime(cells['B'],'%d/%m/%Y').strftime('%Y-%m-%d')
        found.append((draw,date,cells['C'],nums))
    found.sort()
    with normalized.open(newline='',encoding='utf-8') as handle:rows=list(csv.DictReader(handle))
    normalized_records=[(int(r['draw_id']),r['date'],r['time'],tuple(int(r[f'n{i}']) for i in range(1,6))) for r in rows]
    assert found==normalized_records,[(a,b) for a,b in zip(found,normalized_records) if a!=b][:2]
    assert len(found)==604 and [f[0] for f in found]==list(range(13754,14358))
    return {'original_xlsx_sha256':hashlib.sha256(xlsx.read_bytes()).hexdigest(),
            'normalized_csv_sha256':hashlib.sha256(normalized.read_bytes()).hexdigest(),
            'xlsx_records_verified_against_csv':len(found),
            'identical_all_recorded_positions':True,
            'first_id':found[0][0],'last_id':found[-1][0],
            'corrected_14249_record':list(next(q for q in found if q[0]==14249)[3])}

if __name__=='__main__':
    if len(sys.argv)<2:raise SystemExit('Usage: python source_integrity.py path/to/extra5_2026.xlsx')
    report=check(sys.argv[1])
    (HERE/'source_integrity_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
