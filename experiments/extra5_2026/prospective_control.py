#!/usr/bin/env python3
"""Commit-reproducible null-control ticket, NOT a fitted RNG forecast.

Uses only the frozen 2026 CSV through draw 14357. No API calls, secret seeds,
or discretionary candidate selection. A control records evidence integrity,
not a betting advantage.
"""
from __future__ import annotations
import hashlib,json,math
from pathlib import Path
from toy_inverse import unrank

HERE=Path(__file__).resolve().parent
SOURCE=HERE/'extra5_authoritative_2026.csv'
DOMAIN=b'EXTRA5-NULL-CONTROL-V1|immutable-csv-sha256|'
TARGET=14360
DATE_LOCAL='2026-10-31 15:00 Europe/Athens (scheduled; not operator-confirmed)'

def derive(target=TARGET):
    if target<14358:raise ValueError('Target already present in dataset')
    h=hashlib.sha256(SOURCE.read_bytes()).digest()
    label=DOMAIN+str(target).encode('ascii')+b'|'+h
    digest=hashlib.sha256(label).digest()
    N=math.comb(35,5)
    limit=(1<<64)//N*N
    rolls=0
    while True:
        draw=int.from_bytes(digest[:8],'big')
        if draw<limit:break
        digest=hashlib.sha256(digest).digest();rolls+=1
    idx=draw%N
    ticket=unrank(idx)
    return {
      'experiment':'EXTRA5-V1-FROZEN-UNIFORM-NULL-CONTROL',
      'target_draw_id':target,
      'target_schedule_if_normal':DATE_LOCAL if target==TARGET else None,
      'source_last_draw_id':14357,
      'source_sha256':h.hex(),
      'domain_hex':DOMAIN.hex(),
      'method':'sha256(DOMAIN || decimal_target || b"|" || sha256(csv)); interpret first 8 bytes big-endian and reject if >=floor(2^64/C(35,5))*C(35,5); use rank modulo C(35,5) then lexicographic unrank',
      'ticket_rank':idx,
      'ticket':ticket,
      'rejected_words_before_acceptance':rolls,
      'status':'LOCKED NULL CONTROL ONLY; mathematically no advantage over fair chance; unseen results must never be used to alter this ticket',
      'cannot_be_called_blind_if_committed_after_draw':True,
    }

def main():
    result=derive()
    target=HERE/'prospective_null_control_14360_LOCK.json'
    data=json.dumps(result,indent=2)+'\n'
    if target.exists() and target.read_text()!=data:
        raise RuntimeError('Immutable control lock conflicts with current sources; refusing overwrite')
    if not target.exists():target.write_text(data)
    print(json.dumps(result,indent=2))
if __name__=='__main__':main()
