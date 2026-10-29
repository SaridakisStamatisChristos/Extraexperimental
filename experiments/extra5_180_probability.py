#!/usr/bin/env python3
"""Exact probability of 180 individual overlaps in 40 random 5-of-35 draws.

Requires no external package. Predictions must be fixed before the 40 draws.
"""
import math
from decimal import Decimal, localcontext
from pathlib import Path

N=math.comb(35,5)
WEIGHTS=[math.comb(5,k)*math.comb(30,5-k) for k in range(6)]

def exact_tail(draws=40,target=180):
    if not (draws>=1 and 0<=target<=5*draws):
        raise ValueError('invalid count/threshold')
    assert sum(WEIGHTS)==N
    counts=[1]
    for _ in range(draws):
        nxt=[0]*(len(counts)+5)
        for i,x in enumerate(counts):
            for j,w in enumerate(WEIGHTS):
                nxt[i+j]+=x*w
        counts=nxt
    numerator=sum(counts[target:])
    denominator=N**draws
    with localcontext() as ctx:
        ctx.prec=80
        p=Decimal(numerator)/Decimal(denominator)
    return p,numerator,denominator

if __name__=='__main__':
    p,_,_=exact_tail()
    print('fixed-model exact P(overlap >=180/200):',p)
    print('conservative 23343-candidate union bound:',p*23343)
