#!/usr/bin/env python3
"""Construct mathematically distinct finite-field algorithms that fit every past EXTRA 5 draw.

The two models interpolate historical draw IDs exactly, but can be made to
predict arbitrary *different* unseen results. This is a constructive proof
that historical fitting alone cannot identify an RNG or its next output.

Not a plausible historical EXTRA 5 generator or betting model.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
from extra5_walkforward_fit import load_data

P=524287 # Mersenne prime 2^19-1, greater than total 5/35 combinations
TOTAL=math.comb(35,5)


def rank_combination(numbers):
    a=1; r=0
    for j,x in enumerate(numbers):
        for v in range(a,x):
            r += math.comb(35-v,4-j) if 35-v>=4-j else 0
        a=x+1
    assert 0<=r<TOTAL
    return r


def unrank_combination(rank):
    if not 0<=rank<TOTAL:raise ValueError(rank)
    result=[];a=1;rem=5
    for _ in range(5):
        for x in range(a,36):
            count=math.comb(35-x,rem-1) if 35-x>=rem-1 else 0
            if rank<count:
                result.append(x);a=x+1;rem-=1;break
            rank-=count
    return result


def barycentric_weights(xs):
    assert len(set(xs))==len(xs)
    w=[]
    for i,xi in enumerate(xs):
        denom=1
        for j,xj in enumerate(xs):
            if i!=j: denom=denom*(xi-xj)%P
        w.append(pow(denom,-1,P))
    return w


def interpolate(xs,ys,w,x):
    if x in xs:return ys[xs.index(x)]
    product=1;s=0
    for xi,yi,wi in zip(xs,ys,w):
        d=(x-xi)%P
        product=product*d%P
        s=(s + yi*wi*pow(d,-1,P))%P
    return product*s%P


def vanisher(xs,x):
    z=1
    for xi in xs:z=z*((x-xi)%P)%P
    return z


def make_fit(xs,ys,w,x,target_next_rank):
    # F_c(X) = interpolant(X) + c * product(X-x_i) (mod prime).
    # At *any* recorded Xi the product vanishes; next value is tunable.
    base=interpolate(xs,ys,w,x)
    van=vanisher(xs,x)
    if van==0:raise ValueError('next ID already in training')
    c=(target_next_rank-base)*pow(van,-1,P)%P
    return {'coefficient':int(c),'next_rank':int((base+c*van)%P),
            'next_ticket':unrank_combination(int((base+c*van)%P))}


def main():
    ap=argparse.ArgumentParser()
    here=Path(__file__).resolve().parent
    ap.add_argument('--data',type=Path,default=here/'extra5_last100_data.csv')
    ap.add_argument('--out',type=Path,default=here/'extra5_exact_fit_counterexample_results.json')
    args=ap.parse_args()
    ids,X=load_data(args.data)
    ys=[rank_combination((X[i].nonzero()[0]+1).tolist()) for i in range(len(ids))]
    w=barycentric_weights(ids)
    assert all(interpolate(ids,ys,w,xi)==y for xi,y in zip(ids,ys))
    arbitrary_1=[1,2,3,4,5]
    arbitrary_2=[31,32,33,34,35]
    targets={
       '14356':{'low':make_fit(ids,ys,w,14356,rank_combination(arbitrary_1)),
                'high':make_fit(ids,ys,w,14356,rank_combination(arbitrary_2))},
       '14357':{'low':make_fit(ids,ys,w,14357,rank_combination(arbitrary_1)),
                'high':make_fit(ids,ys,w,14357,rank_combination(arbitrary_2))},
    }
    assert all(v['low']['next_ticket']!=v['high']['next_ticket'] for v in targets.values())
    result={'historical_ids':[min(ids),max(ids)],'exact_history_matches':len(ids),
            'prime':P,'total_unordered_tickets':TOTAL,'family':'finite-field polynomial interpolation plus historical vanishing polynomial',
            'coefficients_for_arbitrary_future_outcomes':targets,
            'claim':'100/100 exact historical fit is compatible with completely conflicting unseen outputs; proves nonidentification from fit alone, not predictive performance',
            'data_sha256':hashlib.sha256(args.data.read_bytes()).hexdigest()}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print('Exact-fit interpolation: 100 / 100 historical draws reproduced')
    print('14357 future can be forced as',arbitrary_1,'OR',arbitrary_2,'without changing fit')
    print('saved',args.out)

if __name__=='__main__':main()
