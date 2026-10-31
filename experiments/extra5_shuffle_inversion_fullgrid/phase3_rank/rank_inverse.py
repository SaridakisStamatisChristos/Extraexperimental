#!/usr/bin/env python3
"""Exact low-bit GF(2) inversion for a one-word combination-rank sampler.

All five displayed numbers are used as an unordered set; they determine a
zero-based lexicographic 5-of-35 combination rank. This is a *hypothetical*
sampler. Modulo-only and full-word rejection are distinct consumption models.

xoroshiro128+ and xoshiro256+ compute the *genuine + output*, including
nonlinear carries, but the least significant output bit is GF(2)-linear.
Other low bits of addition are NOT treated as linear.
"""
from __future__ import annotations
import argparse
from dataclasses import dataclass
from itertools import combinations
from math import comb
import json
import time

N = comb(35,5)
M32=(1<<32)-1
M64=(1<<64)-1


def rotl(x,k): return ((x<<k)|(x>>(64-k)))&M64


def combination_rank(numbers):
    s=tuple(sorted(numbers))
    if len(s)!=5 or len(set(s))!=5 or any(not 1<=x<=35 for x in s):
        raise ValueError('expected five distinct integers in 1..35')
    ans=0;lo=1
    for j,v in enumerate(s):
        for a in range(lo,v):ans+=comb(35-a,4-j)
        lo=v+1
    return ans


def combination_unrank(rank):
    if not 0<=rank<N:raise ValueError('rank out of range')
    chosen=[];lo=1
    for j in range(5):
        for v in range(lo,36):
            count=comb(35-v,4-j) if 35-v>=4-j else 0
            if rank<count:
                chosen.append(v);lo=v+1;break
            rank-=count
        else:raise AssertionError('invalid combinadic index')
    return tuple(chosen)


def marsaglia_step(s):
    x,y,z,w=s
    t=(x^((x<<11)&M32))&M32
    w=(w^(w>>19)^t^(t>>8))&M32
    return (y,z,s[3],w),w


def xoroshiro_plus_step(s):
    x,y=s
    output=(x+y)&M64  # full nonlinear addition, output BEFORE transition
    y^=x
    return (rotl(x,24)^y^((y<<16)&M64),rotl(y,37)), output


def xoshiro_plus_step(s):
    a,b,c,d=s
    output=(a+d)&M64  # full nonlinear addition, output BEFORE transition
    t=(b<<17)&M64
    c^=a;d^=b;b^=c;a^=d;c^=t;d=rotl(d,45)
    return (a,b,c,d),output


@dataclass(frozen=True)
class Model:
    name:str
    word_bits:int
    words:int
    step:object
    proved_linear_low_bits:int

    @property
    def size(self):return self.words*self.word_bits
    def decode(self,s):
        if s<0 or s>>self.size:raise ValueError('state out of range')
        mask=(1<<self.word_bits)-1
        return tuple((s>>(self.word_bits*i))&mask for i in range(self.words))


MODELS={
    'marsaglia128':Model('marsaglia128',32,4,marsaglia_step,3),
    'xoroshiro128plus':Model('xoroshiro128plus',64,2,xoroshiro_plus_step,1),
    'xoshiro256plus':Model('xoshiro256plus',64,4,xoshiro_plus_step,1),
}


def generate(model,seed,n,gap=0,rejection=False):
    """Yield unordered 5-number sets; one-word modulo rank sampler.

    Rejection mode uses the largest multiple of N below 2**word_bits.
    The PRNG is advanced for every rejected word and all fixed gap words.
    """
    if gap<0:raise ValueError('negative gap')
    state=model.decode(seed)
    limit=(1<<model.word_bits)-((1<<model.word_bits)%N)
    for _ in range(n):
        while True:
            state,word=model.step(state)
            if not rejection or word<limit:break
        yield combination_unrank(word%N)
        for _ in range(gap):state,_=model.step(state)


def low_forms(model,n,gap):
    """Compute binary linear forms from unit-state basis. Since the first
    `proved_linear_low_bits` of the output are GF2-linear under model assumptions,
    each row defines an EXACT constraint on the full initial state.
    """
    if n<1 or gap<0:raise ValueError('bad n/gap')
    width=model.proved_linear_low_bits
    rows=[[0]*width for _ in range(n)]
    for bit in range(model.size):
        state=model.decode(1<<bit)
        for d in range(n):
            state,w=model.step(state)
            for k in range(width):
                if (w>>k)&1:rows[d][k]|=1<<bit
            for _ in range(gap):state,_=model.step(state)
    return rows


def solve(rows,size):
    """Exact GF2 Gaussian elimination, returning unique state, affine
    underdetermination, or a concrete dependent inconsistent equation.
    """
    pivots={};rank=0
    for i,(x,v) in enumerate(rows):
        if x<0 or x>>size or v not in (0,1):raise ValueError('invalid equation')
        while x:
            p=x.bit_length()-1
            if p not in pivots:
                pivots[p]=(x,v);rank+=1;break
            a,b=pivots[p];x^=a;v^=b
        else:
            if v:return {'status':'UNSAT','rank':rank,'inconsistent_equation':i}
    if rank<size:return {'status':'UNKNOWN','rank':rank,'nullity':size-rank}
    state=0
    for p in sorted(pivots):
        row,rhs=pivots[p]
        if rhs^((row&state).bit_count()&1):state|=1<<p
    return {'status':'CANDIDATE','rank':rank,'seed':state}


def recover(model,tickets,gap=0,rejection=False):
    """No oracle; only unordered sets. Rejection consumption requires a
    separate path search. If rejection=True and no path known, reject call.
    """
    if rejection:raise NotImplementedError('unknown variable consumption is not a fixed-alignment linear model')
    t0=time.monotonic()
    observed=[combination_rank(ticket) for ticket in tickets]
    rows=low_forms(model,len(observed),gap)
    eqs=[(rows[d][k],(v>>k)&1) for d,v in enumerate(observed) for k in range(model.proved_linear_low_bits)]
    x=solve(eqs,model.size)
    result={'model':model.name,'sampler':'single_word_rank_modulo','state_bits':model.size,
            'extracted_linear_bits_per_ticket':model.proved_linear_low_bits,
            'observations':len(observed),'gap':gap,'linear_rank':x['rank'],
            'equations':len(eqs),'seconds':round(time.monotonic()-t0,6)}
    if x['status']=='CANDIDATE':
        witness=x['seed']
        replay=all(a==b for a,b in zip(generate(model,witness,len(tickets),gap),tickets))
        result.update(status='SAT' if replay else 'UNSAT',full_ticket_replay=replay,
                      recovered_seed=f'0x{witness:0{model.size//4}x}',
                      justification='unique low-bit state and full replay' if replay else 'unique low-bit state contradicts full ticket')
    elif x['status']=='UNSAT':
        result.update(status='UNSAT',justification='inconsistent necessary GF(2) equations',
                      conflicting_equation=x['inconsistent_equation'])
    else:result.update(status='UNKNOWN',nullity=x['nullity'],justification='insufficient linear rank')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--model',choices=MODELS,default='xoroshiro128plus')
    p.add_argument('--seed',type=lambda x:int(x,0),default=0x123456789abcdef0fedcba9876543210)
    p.add_argument('--training',type=int,default=350)
    p.add_argument('--gap',type=int,default=0)
    a=p.parse_args();m=MODELS[a.model]
    data=list(generate(m,a.seed,a.training+100,a.gap))
    result=recover(m,data[:a.training],a.gap)
    if result['status']=='SAT':
        result['recovered_original_seed']=int(result['recovered_seed'],16)==a.seed
        result['heldout_replay']=all(x==y for x,y in zip(generate(m,int(result['recovered_seed'],16),len(data),a.gap),data))
    print(json.dumps(result,indent=2))
