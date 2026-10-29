#!/usr/bin/env python3
"""One public historical EXTRA 5 draw -> blind next-draw demonstration.

Historical *family*: AES-192-CFB zero-plaintext stream (Bikos et al. 2023).
The seed serialization, public SHA-512 KDF, full-block CFB128, continuous
state, bit order, and ticket sampler are EXPERIMENTAL NOT ALLWYN SPECIFICATION.

Never fetch the held-out draw. Training inputs only 14248: (13,16,22,30,31).
Searching a million public seeds is expected to yield several *accidental* fits.
The selection rule is FIRST seed index yielding an exact training ticket;
future ticket computed from *that same* initialized continuous stream.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

TRAIN_DRAW_ID = 14248
NEXT_DRAW_ID = 14249
TRAIN = (13,16,22,30,31)
TOTAL_COLUMNS = 10566 # metadata supplied by user, NOT seed material
COMBINATIONS = math.comb(35,5)
DOMAIN = b'EXTRA5-BLIND-14248-AES192-CFB-RESEARCH-v1|PUBLIC-SYNTHETIC-SEED|'

def unrank_5of35(r: int) -> tuple[int,...]:
    if not 0 <= r < COMBINATIONS: raise ValueError('rank out of range')
    a=1; out=[]; remain=5
    while remain:
        for n in range(a, 36):
            count = math.comb(35-n, remain-1) if 35-n >= remain-1 else 0
            if r < count:
                out.append(n);a=n+1;remain-=1;break
            r -= count
        else: raise AssertionError('invalid combinadic transition')
    return tuple(out)

def rank_5of35(ticket: tuple[int,...]) -> int:
    if len(ticket) != 5 or tuple(sorted(set(ticket)))!=tuple(ticket) or min(ticket)<1 or max(ticket)>35:
        raise ValueError('five sorted distinct numbers required')
    value=0; start=1; remain=5
    for actual in ticket:
        for v in range(start,actual):
            value+=math.comb(35-v,remain-1)
        start=actual+1; remain-=1
    return value

LIMIT = (1 << 24) // COMBINATIONS * COMBINATIONS

def decode_ticket(raw: bytes, pos: int) -> tuple[tuple[int,...], int]:
    while pos+3<=len(raw):
        v=int.from_bytes(raw[pos:pos+3],'big');pos+=3
        if v < LIMIT:
            return unrank_5of35(v % COMBINATIONS), pos
    raise ValueError('insufficient stream for rejection sampler')

def seed_to_key_iv(seed_index: int) -> tuple[bytes,bytes]:
    if not 0 <= seed_index < 2**64: raise ValueError('seed index out of domain')
    digest=hashlib.sha512(DOMAIN+seed_index.to_bytes(8,'big')).digest()
    return digest[:24],digest[24:40]

def tickets_for_seed(seed_index: int, count=2) -> tuple[tuple[int,...],...]:
    key,iv=seed_to_key_iv(seed_index)
    enc=Cipher(algorithms.AES(key),modes.CFB(iv)).encryptor()
    # Continuous AES-192 full-block CFB128 stream, not per-draw reseeding.
    raw=enc.update(bytes(128))
    pos=0; tickets=[]
    for _ in range(count):
        t,pos=decode_ticket(raw,pos);tickets.append(t)
    return tuple(tickets)

def fit(seed_start: int=0,seed_stop: int=1000000):
    if seed_start<0 or seed_stop<=seed_start or seed_stop>2**64: raise ValueError('invalid search interval')
    target_rank=rank_5of35(TRAIN)
    winners=[]
    for seed in range(seed_start,seed_stop):
        key,iv=seed_to_key_iv(seed)
        enc=Cipher(algorithms.AES(key),modes.CFB(iv)).encryptor()
        raw=enc.update(bytes(48))
        pos=0
        try:t,pos=decode_ticket(raw,pos)
        except ValueError:continue
        if t==TRAIN:
            second,_=decode_ticket(raw,pos)
            winners.append({'seed_index':seed,'training_ticket':list(t), 'blind_next_ticket':list(second)})
    return {'target_draw_id':TRAIN_DRAW_ID,'target_ticket':list(TRAIN),'next_draw_id':NEXT_DRAW_ID,
            'total_columns_metadata':TOTAL_COLUMNS,'seed_interval':[seed_start,seed_stop],
            'searched':seed_stop-seed_start,'exact_fits':len(winners),'all_matching_seed_hypotheses':winners,
            'selection_rule':'lowest numeric seed among exactly fitting synthetic candidates',
            'locked_candidate':winners[0] if winners else None,
            'method':'AES-192-CFB128 zero-stream, public SHA512 seed-index -> key and IV; continuous bitstream; 24bit rejection/combinadic rank',
            'actual_hidden_draw_accessed':False,
            'significance':'one fit expected every 324632 artificial independent candidates; fit alone is no evidence of a recovered production seed'}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed-start',type=int,default=0)
    ap.add_argument('--seed-stop',type=int,default=1000000)
    ap.add_argument('--out',type=Path,default=Path(__file__).with_name('extra5_blind_14249_prediction.json'))
    a=ap.parse_args()
    result=fit(a.seed_start,a.seed_stop)
    a.out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'searched':result['searched'],'exact_fits':result['exact_fits'],'selected':result['locked_candidate'],'all_exact_seed_indices':[x['seed_index'] for x in result['all_matching_seed_hypotheses']]},indent=2))
if __name__=='__main__':main()
