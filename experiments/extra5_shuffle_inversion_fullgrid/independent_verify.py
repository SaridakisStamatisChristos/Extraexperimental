#!/usr/bin/env python3
"""Independent Python oracle for shuffle-invariant inverse-state hypotheses.

No dependence on C++ generator. Reference enumerates allowed fourth indices
combinatorially; replays planted seeds; audits full search outputs.
"""
from __future__ import annotations
import csv
import hashlib
import itertools
import math
from pathlib import Path
from collections import Counter

HERE=Path(__file__).resolve().parent
INPUT=HERE
MASK32=(1<<32)-1


def expected_allowed(ticket):
    vals=[i+1 for i in range(35) if ticket & (1<<i)]
    assert len(vals)==5
    mask=0
    for x in vals:
        for previous in itertools.combinations([v for v in vals if v!=x],3):
            idx=x-1-sum(v<x for v in previous)
            assert 0<=idx<32
            mask|=1<<idx
    return mask


def load_masks(path):
    with open(path,newline='') as f:return [dict(row) for row in csv.DictReader(f)]


def gen(seed,a,b,c,dir,gap,n):
    state=seed
    for _ in range(n):
        available=list(range(1,36));result=[]
        for _ in range(5):
            if dir==0:
                state^=(state<<a)&MASK32;state^=state>>b;state^=(state<<c)&MASK32
            else:
                state^=state>>a;state^=(state<<b)&MASK32;state^=state>>c
            state&=MASK32
            result.append(available.pop(state % len(available)))
        for _ in range(gap):
            if dir==0:
                state^=(state<<a)&MASK32;state^=state>>b;state^=(state<<c)&MASK32
            else:
                state^=state>>a;state^=(state<<b)&MASK32;state^=state>>c
            state&=MASK32
        yield sum(1<<(v-1) for v in result)


def test_all_masks():
    files=[INPUT/'real_unordered.csv']+sorted(INPUT.glob('synthetic_xorshift32_*_stride*.csv'))
    count=0
    for p in files:
        rows=load_masks(p)
        for row in rows:
            found=int(row['allowed_fourth_mask']);computed=expected_allowed(int(row['ticket_mask']))
            assert found==computed,(p,row['index'],found,computed)
            count+=1
    return count


def test_planted():
    planted={(13,17,5):0x89ABCDEF,(5,17,13):0x9A876543,(7,9,13):0x6A5F1234}
    result=[]
    for (a,b,c),seed in planted.items():
        for stride in (5,7):
            path=INPUT/f'synthetic_xorshift32_{a}_{b}_{c}_stride{stride}.csv'
            observed=[int(r['ticket_mask']) for r in load_masks(path)]
            expected=list(gen(seed,a,b,c,0,stride-5,len(observed)))
            assert observed==expected
            fitted=load_masks(HERE/f'synthetic_{a}_{b}_{c}_stride{stride}_recovery.csv')
            witness=[r for r in fitted if int(r['direction'])==0 and int(r['extra_gap'])==stride-5][0]
            assert int(witness['max_exact_prefix'])==60
            assert int(witness['witness_seed'])==seed
            assert list(gen(seed^1,a,b,c,0,stride-5,1))!=observed[:1]
            result.append(dict(model=f'{a}_{b}_{c}_gap{stride-5}',draws=len(observed),recovered_seed=f'{seed:#010x}'))
    return result


def check_results(p):
    rows=[]
    for r in load_masks(p):
        if not (r.get('max_exact_prefix') and r.get('witness_seed')):continue
        assert all(int(r[k])>=0 for k in ['branches','linear_consistent_seeds','passed_additional_fourth_constraints','one_exact','at_least_two_exact','max_exact_prefix'])
        assert int(r['passed_additional_fourth_constraints'])>=int(r['one_exact'])>=int(r['at_least_two_exact'])
        assert int(r['max_exact_prefix'])<=100
        if int(r['max_exact_prefix'])>0:
            a,b,c,dir,gap=[int(r[k]) for k in ['shift_a','shift_b','shift_c','direction','extra_gap']]
            seed=int(r['witness_seed']);real=[int(z['ticket_mask']) for z in load_masks(INPUT/'real_unordered.csv')][:100]
            predicted=list(gen(seed,a,b,c,dir,gap,len(real)))
            prefix=0
            for x,y in zip(predicted,real):
                if x!=y:break
                prefix+=1
            assert prefix==int(r['max_exact_prefix']),(r,prefix)
        rows.append(r)
    return rows

if __name__=='__main__':
    count=test_all_masks()
    planted=test_planted()
    print('COMBINATORIAL_MASKS_VERIFIED',count)
    print('INDEPENDENT_PLANTED_RECOVERIES',planted)
    print('INDIVIDUAL_TESTS_PASS',1+len(planted))
