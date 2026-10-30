#!/usr/bin/env python3
"""Extract and validate five yearly user-authoritative EXTRA 5 XLSX archives.

The exported five-year CSV contains recorded number order (n1..n5), sorted
numbers (s1..s5) and lexicographic combinadic rank. No betting model is fitted.
Run from any directory: python prepare_five_year.py
"""
from __future__ import annotations
import csv
from collections import Counter
from datetime import datetime, timedelta
from hashlib import sha256
import json
from pathlib import Path
from math import comb
import os
from artifact_tool import Blob, SpreadsheetFile
ROOT=Path(__file__).resolve().parent
INPUTS=Path(os.environ.get('EXTRA5_INPUT_DIR','/mnt/data'))
HEADERS=['draw_id','date','time']+[f'n{i}' for i in range(1,6)]+[f's{i}' for i in range(1,6)]+['lex_rank','source_workbook']

def combinadic_rank(ticket):
    total=0; prev=0
    for j,n in enumerate(sorted(ticket)):
        for k in range(prev+1,n):total+=comb(35-k,4-j)
        prev=n
    return total

def parse_year(year):
    file=INPUTS/f'extra5_{year}.xlsx'
    workbook=SpreadsheetFile.import_xlsx(Blob.load(str(file)))
    sheet=workbook.worksheets.get_item_at(0)
    end={2022:1521,2023:1521,2024:735,2025:733,2026:607}[year]
    data=sheet.get_range(f'A4:H{end}').values
    records=[];errors=[]
    for excelrow, row in enumerate(data,start=4):
        if row[0] is None or str(row[0]).strip()=='':continue
        if not str(row[0]).strip().isdigit():
            errors.append(f'{year}: row {excelrow} non-draw id {row[0]!r}');continue
        try:
            id_=int(row[0]); day=datetime.strptime(str(row[1]).strip(),'%d/%m/%Y').date()
            t=str(row[2]).strip(); vals=tuple(int(str(v).strip()) for v in row[3:8])
            assert day.year==year
            assert t in ('15:00','19:00')
            assert len(set(vals))==5 and all(1<=n<=35 for n in vals)
            record={'draw_id':id_,'date':day.isoformat(),'time':t}
            record.update({f'n{i}':n for i,n in enumerate(vals,1)})
            record.update({f's{i}':n for i,n in enumerate(sorted(vals),1)})
            record['lex_rank']=combinadic_rank(vals)
            record['source_workbook']=file.name
            records.append(record)
        except Exception as e:errors.append(f'{year}: row {excelrow}: {e!r}; {row!r}')
    return records,errors,sha256(file.read_bytes()).hexdigest()

def run():
    rows=[];issues=[];sources={}
    for year in range(2022,2027):
        part,errors,digest=parse_year(year)
        rows.extend(part);issues.extend(errors)
        sources[str(year)]={'workbook':f'extra5_{year}.xlsx','sha256':digest,'records':len(part),
                            'min_id':min(r['draw_id'] for r in part),'max_id':max(r['draw_id'] for r in part)}
    rows.sort(key=lambda r:r['draw_id'])
    ids=[r['draw_id'] for r in rows]
    assert ids==list(range(ids[0],ids[-1]+1)), 'gaps or duplicate IDs detected'
    assert len(rows)==3526 and ids[0]==10832 and ids[-1]==14357
    assert len({(r['date'],r['time']) for r in rows})==len(rows)
    # The date-clock succession is expected to be two daily draws, no exceptions.
    for a,b in zip(rows,rows[1:]):
        expecteddate=a['date'] if a['time']=='15:00' else (datetime.fromisoformat(a['date']).date()+timedelta(days=1)).isoformat()
        expectedtime='19:00' if a['time']=='15:00' else '15:00'
        assert (b['date'],b['time'])==(expecteddate,expectedtime),(a['draw_id'],b['draw_id'])
    # Check every 2026 record against the independently normalized archive.
    prior=INPUTS/'extra5_campaign'/'extra5_authoritative_2026.csv'
    if prior.exists():
        priorrows=list(csv.DictReader(prior.open(newline='')))
        latest=[r for r in rows if r['date'][:4]=='2026']
        assert len(priorrows)==len(latest)
        for a,b in zip(latest,priorrows):
            for col in ['draw_id','date','time']+[f'n{i}' for i in range(1,6)]+[f's{i}' for i in range(1,6)]+['lex_rank']:
                assert str(a[col])==b[col],(a['draw_id'],col,a[col],b[col])
    assert not issues,issues[:10]
    out=ROOT/'extra5_2022_2026_authoritative.csv'
    with out.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS);writer.writeheader();writer.writerows(rows)
    # Establish a physical training/evaluation boundary: 2025/2026 outcome
    # fields are not available to the generator-selection process.
    train=ROOT/'train_2022_2024.csv'
    with train.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=HEADERS);writer.writeheader();writer.writerows(rows[:2192])
    calendar=ROOT/'evaluation_calendar_2025_2026.csv'
    with calendar.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['draw_id','date','time']);writer.writeheader()
        writer.writerows([{k:r[k] for k in ('draw_id','date','time')} for r in rows[2192:]])
    meta={'count':len(rows),'id_start':ids[0],'id_end':ids[-1],
          'first_timestamp':rows[0]['date']+' '+rows[0]['time'],
          'last_timestamp':rows[-1]['date']+' '+rows[-1]['time'],
          'source_files':sources,'csv_sha256':sha256(out.read_bytes()).hexdigest(),
          'missing_ids':0,'duplicates':0,'date_clock_gaps':0,'invalid_rows':len(issues),
          'extraction_order_verified':False,
          'train_2022_2024_count':sum(r['date'][:4]<'2025' for r in rows),
          'validation_2025_count':sum(r['date'][:4]=='2025' for r in rows),
          'heldout_2026_count':sum(r['date'][:4]=='2026' for r in rows),
          'interpretation':'workbooks authoritative by user designation; clock order present; n1..n5 represent workbook column order, not independently authenticated extraction order.'}
    (ROOT/'provenance.json').write_text(json.dumps(meta,indent=2,ensure_ascii=False)+'\n')
    print(json.dumps(meta,indent=2))
    return rows,meta

if __name__=='__main__':run()
