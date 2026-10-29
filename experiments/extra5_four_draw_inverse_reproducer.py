#!/usr/bin/env python3
"""Four-draw EXTRA 5 fixed-algorithm inverse-seed experiment.

Not a model of the installed lottery machine: xorshift96/xorshift128 and
seed serialization are hypothetical. The unbiased 24-bit rejection/combinadic
sampler matches our prior *synthetic* sampler. The fixed no-rejection branch
sets each 24-bit raw integer to the lexicographic ticket rank (k=0).

Reproducible, pure-Python, zero external dependencies.
"""
from __future__ import annotations
import itertools, json, math

N=math.comb(35,5)
LIMIT=(1<<24)//N*N
MASK=(1<<32)-1
DRAWS=((2,4,30,32,35),(2,5,9,30,33),(10,18,21,25,29),(1,7,9,14,18))
IDS=(14249,14250,14251,14252)

def rank(t):
    if len(t)!=5 or tuple(t)!=tuple(sorted(set(t))) or not 1<=t[0]<=t[-1]<=35:
        raise ValueError('invalid five-number set')
    total=0;previous=0
    for j,n in enumerate(t):
        for k in range(previous+1,n):total+=math.comb(35-k,4-j)
        previous=n
    return total

def unrank(r):
    if not 0<=r<N:raise ValueError('invalid rank')
    out=[];lo=1
    for j in range(5):
        for n in range(lo,36):
            count=math.comb(35-n,4-j) if 35-n>=4-j else 0
            if r<count:
                out.append(n);lo=n+1;break
            r-=count
        else:raise AssertionError('unrank overflow')
    return tuple(out)

RANKS=tuple(map(rank,DRAWS))

def step64(s):
    mask=(1<<64)-1
    s ^= (s<<13)&mask; s ^= s>>7; s ^= (s<<17)&mask
    s &= mask
    return s,(s>>32)&MASK

def step96(s):
    x=s&MASK;y=(s>>32)&MASK;z=(s>>64)&MASK
    t=x^((x<<16)&MASK);t^=t>>5;t^=(t<<1)&MASK
    nz=(t^y^z)&MASK
    return y|(z<<32)|(nz<<64),nz

def step128(s):
    x=s&MASK;y=(s>>32)&MASK;z=(s>>64)&MASK;w=(s>>96)&MASK
    t=x^((x<<11)&MASK)
    nw=(w^(w>>19)^t^(t>>8))&MASK
    return y|(z<<32)|(w<<64)|(nw<<96),nw

def output_words(kind,seed,count):
    step={'xorshift64':step64,'xorshift96':step96,'xorshift128':step128}[kind]
    words=[]
    for _ in range(count):seed,v=step(seed);words.append(v)
    return words

def decode(kind,seed,count=5):
    b=b''.join(w.to_bytes(4,'big') for w in output_words(kind,seed,48))
    result=[];rejects=0
    for pos in range(0,len(b)-2,3):
        v=int.from_bytes(b[pos:pos+3],'big')
        if v>=LIMIT:rejects+=1;continue
        result.append({'raw24':v,'rank':v%N,'numbers':list(unrank(v%N))})
        if len(result)==count:return result,rejects
    raise ValueError('bit preview exhausted')

def matrix(kind):
    size={'xorshift64':64,'xorshift96':96,'xorshift128':128}[kind]
    columns=[output_words(kind,1<<i,3) for i in range(size)]
    rows=[sum(1<<i for i in range(size) if (columns[i][j]>>bit)&1)
          for j in range(3) for bit in range(32)]
    return size,rows

def solve(rows,values,size):
    pivots={}
    for j,v in enumerate(values):
        for bit in range(32):
            row=rows[j*32+bit];b=(v>>bit)&1
            while row:
                pivot=row.bit_length()-1
                if pivot not in pivots:
                    pivots[pivot]=(row,b)
                    break
                old,oldb=pivots[pivot];row^=old;b^=oldb
            else:
                if b:return None
    seed=0
    for bit in sorted(pivots):
        row,b=pivots[bit]
        if ((row&seed).bit_count()&1)!=b:seed|=1<<bit
    return seed,len(pivots),size-len(pivots)

def seeded_fit(kind,ranks=RANKS):
    if len(ranks)!=4 or any(not 0<=r<LIMIT for r in ranks):raise ValueError('bad raw branch')
    raw=b''.join(int(r).to_bytes(3,'big') for r in ranks)
    words=[int.from_bytes(raw[i:i+4],'big') for i in (0,4,8)]
    size,rows=matrix(kind)
    result=solve(rows,words,size)
    if result is None:return None
    seed,rank_,free=result
    got,_=decode(kind,seed)
    if tuple(tuple(d['numbers']) for d in got[:4])!=DRAWS:raise AssertionError('not a four-draw match')
    return {'algorithm':kind,'seed_bits':size,'state_hex':f'{seed:0{size//4}x}',
            'equation_rank':rank_,'free_bits':free,'seed_multiplicity_for_raw_branch':str(1<<free),
            'training_numbers':[d['numbers'] for d in got[:4]],'raw24_training':list(ranks),
            'fifth_ticket':got[4]}

def run():
    smaller=seeded_fit('xorshift64')
    canonical=seeded_fit('xorshift96')
    alternate=seeded_fit('xorshift96',(RANKS[0]+N,)+RANKS[1:])
    larger=seeded_fit('xorshift128')
    if not canonical or not alternate or not larger:raise AssertionError('missing expected state')
    assert canonical['state_hex']=='92a140efbdfe8769d18dcbdc'
    assert canonical['fifth_ticket']['numbers']==[9,24,25,30,33]
    assert alternate['fifth_ticket']['numbers']==[15,17,22,29,35]
    assert smaller is None
    assert larger['free_bits']==32
    result={
     'experiment':'EXTRA5-4DRAW-XORSHIFT96-INVERSE-20261030',
     'training_draws':[{'id':i,'ticket':list(t),'lexicographic_rank':r} for i,t,r in zip(IDS,DRAWS,RANKS)],
     'target_draw_id':14253,'target_result_was_not_accessed':True,
     'sampler':'continuous 32bit big-endian PRNG output bytes; 24bit chunks; reject raw>=floor(2^24/N)*N; map raw % N via lexicographic unrank',
     'branch':'assume zero rejected raw chunks in first four accepted tickets; canonical raw chunks exactly equal combination ranks',
     'xorshift64_canonical_raw_branch':{'consistent':False,'state_bits':64},
     'canonical_xorshift96':canonical,'different_raw_branch_same_four_training':alternate,
     'xorshift128_example':larger,
     'number_of_accepted_raw24_values_per_known_ticket':(1<<24)//N,
     'at_least_distinct_xorshift96_seeds_with_zero_initial_rejections':((1<<24)//N)**4,
     'interpretation':'Exact four-draw initial-state recovery in a FIXED toy linear generator, but not a unique seed when 24bit-to-ticket mapping is noninjective. No evidence of deployed Allwyn generator or predictive skill; fifth ticket is an untested historical holdout.'
    }
    return result

if __name__=='__main__':
    data=run()
    print(json.dumps(data,indent=2))
