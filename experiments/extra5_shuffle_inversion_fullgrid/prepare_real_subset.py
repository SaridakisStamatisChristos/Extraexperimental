#!/usr/bin/env python3
"""Derive a minimal audit subset from the unchanged authoritative EXTRA 5 CSV.

No changes to the source data or prediction locks. Missing rows are written
as ticket_mask=0, and the inverse engine preserves their chronological steps.
"""
import argparse
import csv
import hashlib
from pathlib import Path

EXPECTED_SHA="61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307"
DEFAULT_SOURCE=Path(__file__).resolve().parents[1]/'extra5_five_year'/'extra5_2022_2026_authoritative.csv'

def domain(nums):
    nums=sorted(nums);allowed=set()
    for below,v in enumerate(nums):
        for removed in range(max(0,below-1),min(3,below)+1):
            allowed.add(v-1-removed)
    return allowed

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,default=DEFAULT_SOURCE)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--extra-rows',type=int,default=130)
    a=p.parse_args()
    data=a.source.read_bytes()
    sha=hashlib.sha256(data).hexdigest()
    if sha!=EXPECTED_SHA:raise ValueError('authoritative CSV checksum mismatch: '+sha)
    with a.source.open(newline='') as f:rows=list(csv.DictReader(f))
    if len(rows)!=3526:raise ValueError('expected 3,526 draws')
    records=[]
    for i,r in enumerate(rows):
        if int(r['draw_id'])!=10832+i:raise ValueError('out-of-order draw ID')
        nums=[int(r[f'n{k}']) for k in range(1,6)]
        if len(set(nums))!=5 or any(not 1<=x<=35 for x in nums):
            raise ValueError('invalid lottery ticket')
        records.append((sum(1<<(x-1) for x in nums),len(domain(nums))))
    ranked=sorted(range(2,len(rows)),key=lambda i:(records[i][1],i))
    ids={0,1}|set(ranked[:a.extra_rows])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['ticket_mask'])
        for i,(mask,_) in enumerate(records):
            w.writerow([mask if i in ids else 0])
    print(f'source_sha256={sha} total_draws={len(rows)} kept={len(ids)}')
    print('selected_zero_based_indices='+','.join(map(str,sorted(ids))))
if __name__=='__main__':main()
