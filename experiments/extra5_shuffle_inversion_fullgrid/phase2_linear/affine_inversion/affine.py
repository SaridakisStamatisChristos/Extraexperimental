#!/usr/bin/env python3
"""Necessary GF(2) parity equations implied by an unordered ticket's fourth index."""
from itertools import combinations
from collections import Counter
from pathlib import Path
import csv

def fourth_domain(nums):
    a=set()
    for below,v in enumerate(sorted(nums)):
        for removed in range(max(0,below-1),min(3,below)+1):
            a.add(v-1-removed)
    assert all(0<=v<32 for v in a)
    return sorted(a)

def affine_constraints(values):
    # Enumerate all 31 nonzero parity masks on a 5-bit index, keep canonical independent ones.
    value0=values[0];basis=[];piv={}
    for v in values[1:]:
        x=v^value0
        while x:
            k=x.bit_length()-1
            if k not in piv:
                piv[k]=x;break
            x^=piv[k]
    candidates=[]
    for mask in range(1,32):
        if all(((v&mask).bit_count()&1)==((value0&mask).bit_count()&1) for v in values):
            candidates.append((mask,(value0&mask).bit_count()&1))
    chosen=[];piv2={}
    for mask,b in candidates:
        x=mask
        while x:
            k=x.bit_length()-1
            if k not in piv2:piv2[k]=x;chosen.append((mask,b));break
            x^=piv2[k]
    assert len(chosen)==5-len(piv)
    return chosen

def census():
    c=Counter();single=Counter();size=Counter()
    for nums in combinations(range(1,36),5):
        v=fourth_domain(nums);co=affine_constraints(v)
        c[len(co)]+=1;size[len(v)]+=1
        if co:single[len(v)]+=1
    return c,size,single

if __name__=='__main__':
    import time
    t=time.perf_counter();c,size,single=census()
    print('all 5/35 sets affine codimension',c,'elapsed',time.perf_counter()-t)
    print('domain sizes',size)
