#!/usr/bin/env python3
"""Exact low-bit observability inversion for GF(2)-linear PRNGs.

Hypothesis: each ticket's *unordered* lexicographic rank comes from an
unsigned generator word modulo C(35,5)=324632, possibly with rejection.
Because 324632 is divisible by 8, its lowest three rank bits are exactly
those of the generator word whenever no rejection occurs.

This yields linear equations for GF(2)-linear transitions and low-bit-linear
outputs. The equations are necessary constraints, *not* sufficient for a
correct rank. Full predictions are checked independently.
"""
from __future__ import annotations
import argparse, csv, json, math, time
from dataclasses import dataclass
from pathlib import Path

MASK32=(1<<32)-1
MASK64=(1<<64)-1
N=math.comb(35,5)
assert N == 324632 and N%8==0

@dataclass(frozen=True)
class Family:
    name: str
    bits: int
    output_bits: int
    observed_bits: int

FAMILIES=(Family('marsaglia128_11_8_19',128,32,3),
          Family('marsaglia128_15_4_21',128,32,3),
          Family('xorshift64_13_7_17',64,64,3),
          Family('xorshift64_12_25_27',64,64,3),
          Family('xoroshiro128plus',128,64,1),
          Family('xoshiro256plus',256,64,1))

def step(family:str, state:int)->tuple[int,int]:
    if family.startswith('marsaglia128_'):
        left,middle,right=(int(v) for v in family.split('_')[1:])
        x=state & MASK32
        y=(state>>32) & MASK32
        z=(state>>64) & MASK32
        w=(state>>96) & MASK32
        t=(x ^ ((x<<left)&MASK32)) & MASK32
        nw=(w ^ (w>>right) ^ t ^ (t>>middle)) & MASK32
        return y|(z<<32)|(w<<64)|(nw<<96),nw
    if family.startswith('xorshift64_'):
        a,b,c=(int(v) for v in family.split('_')[1:])
        x=state&MASK64
        x^=(x<<a)&MASK64
        x^=x>>b
        x^=(x<<c)&MASK64
        return x,x
    if family=='xoroshiro128plus':
        s0=state&MASK64;s1=(state>>64)&MASK64
        out=(s0+s1)&MASK64
        s1^=s0
        new0=(((s0<<55)|(s0>>(64-55)))^s1^((s1<<14)&MASK64))&MASK64
        new1=((s1<<36)|(s1>>(64-36)))&MASK64
        return new0|(new1<<64),out
    if family=='xoshiro256plus':
        s=[(state>>(64*j))&MASK64 for j in range(4)]
        out=(s[0]+s[3])&MASK64
        t=(s[1]<<17)&MASK64
        s[2]^=s[0];s[3]^=s[1];s[1]^=s[2];s[0]^=s[3];s[2]^=t
        s[3]=((s[3]<<45)|(s[3]>>(64-45)))&MASK64
        return sum(v<<(64*j) for j,v in enumerate(s)),out
    raise ValueError(family)

def ticket_rank(ticket):
    nums=sorted(ticket)
    assert len(nums)==5 and len(set(nums))==5 and nums[0]>=1 and nums[-1]<=35
    # 0-indexed lexicographic rank via skipped 5-combinations
    rank=0
    last=0
    for j,n in enumerate(nums):
        for v in range(last+1,n): rank+=math.comb(35-v,4-j)
        last=n
    assert 0<=rank<N
    return rank

def unrank(rank):
    assert 0<=rank<N
    values=[];prev=0
    for j in range(5):
        for v in range(prev+1,36):
            k=math.comb(35-v,4-j) if 35-v>=4-j else 0
            if rank<k:
                values.append(v);prev=v;break
            rank-=k
    return values

def load(path):
    with open(path,newline='') as f: rows=list(csv.DictReader(f))
    for i,r in enumerate(rows):
        assert int(r['draw_id'])==int(rows[0]['draw_id'])+i
        assert ticket_rank([int(r[f'n{k}']) for k in range(1,6)])==int(r['lex_rank'])
    return rows

def masks_for(family:Family,stride:int, count:int, *, output_word:int=0):
    """Returns bitmask per observation for every generator output bit of interest.

    Each observation is a linear Boolean functional of *initial* state bits.
    For xoroshiro+/xoshiro+ we only use bit0; addition bit0 is XOR.
    """
    output_masks=[[0]*family.observed_bits for _ in range(count)]
    bits=family.bits
    for i in range(bits):
        s=1<<i
        for t in range(count):
            for z in range(stride):s,out=step(family.name,s)
            word=out if not family.name.startswith('marsaglia128_') else (s>>(32*output_word))&MASK32
            for k in range(family.observed_bits):
                if (word>>k)&1:output_masks[t][k] |= 1<<i
    return output_masks

class GF2:
    """Incremental XOR Gaussian elimination; RHS inserted in high bit."""
    def __init__(self,n):self.n=n;self.pivots={};self.equations=0;self.first_bad=None
    def add(self,mask,rhs):
        self.equations+=1
        x=mask|((rhs&1)<<self.n)
        while True:
            lhs=x&((1<<self.n)-1)
            if lhs==0:
                if x>>self.n:
                    self.first_bad=self.equations
                    return False
                return True
            k=lhs.bit_length()-1
            if k in self.pivots:x ^= self.pivots[k]
            else:self.pivots[k]=x;return True
    @property
    def rank(self):return len(self.pivots)
    def solve_zero_free(self):
        assert self.first_bad is None
        s=0
        # descending pivot index solved starting lower pivot order (lower equations have lower bits)
        for k in sorted(self.pivots):
            row=self.pivots[k]
            rhs=(row>>self.n)&1
            lhs=(row & ((1<<self.n)-1)) & ~(1<<k)
            if ((lhs & s).bit_count()&1) != rhs:s |= 1<<k
        return s

def examine(family:Family,stride:int, ranks:list[int], *, word:int=0,limit:int=140):
    count=min(limit,len(ranks))
    targets=ranks[:count]
    # Fixed dimensionality and fixed stride means every low-bit equation is exact.
    masks=masks_for(family,stride,count,output_word=word)
    elim=GF2(family.bits)
    conflict_draw=None
    for j in range(count):
        for k in range(family.observed_bits):
            if not elim.add(masks[j][k],(targets[j]>>k)&1):
                conflict_draw=j+1;break
        if conflict_draw:break
    result={'family':family.name,'stride':stride,'word':word,'state_bits':family.bits,
            'observed_bits_per_draw':family.observed_bits,'rank':elim.rank,
            'first_parity_contradiction_draw':conflict_draw,'prefix_lowbit_consistent':min(count,conflict_draw-1 if conflict_draw else count)}
    if conflict_draw is None and elim.rank==family.bits:
        state=elim.solve_zero_free()
        result['solved_state_hex']=hex(state)
        s=state;matches=0;first_fail=None; raw_rejections=0
        for j,r in enumerate(ranks):
            for z in range(stride):s,out=step(family.name,s)
            word_out=out if not family.name.startswith('marsaglia128_') else (s>>(32*word))&MASK32
            modulus=1<<family.output_bits
            if word_out >= modulus-(modulus%N): raw_rejections+=1
            if word_out%N != r:
                first_fail=j+1;break
            matches+=1
        result.update(exact_prefix=matches,first_full_rank_failure_draw=first_fail,rejection_hits_checked=raw_rejections)
    return result

def synthetic(family:Family,stride:int, initial:int,count:int):
    s=initial;answer=[]
    for j in range(count):
        for z in range(stride):s,out=step(family.name,s)
        answer.append(out%N)
    return answer

def run(rows,outdir:Path,limit:int=140,maxstride:int=8):
    outdir.mkdir(parents=True,exist_ok=True)
    ranks=[int(r['lex_rank']) for r in rows]
    started=time.monotonic()
    data=[]
    for f in FAMILIES:
        for stride in range(1,maxstride+1):
            for word in range(4 if f.name.startswith('marsaglia128_') else 1):
                rec=examine(f,stride,ranks,word=word,limit=limit)
                data.append(rec)
                if rec['first_parity_contradiction_draw'] is None and rec.get('exact_prefix',0)>2:
                    print('SURVIVOR',rec,flush=True)
    result={'archive_size':len(rows),'draw_span':[rows[0]['draw_id'],rows[-1]['draw_id']],
            'constraint_train_draws':limit,'maxstride':maxstride,
            'models_checked':len(data),'method':'exhaustive_GF2_parity_constraint_elimination',
            'computation_seconds':round(time.monotonic()-started,3),
            'results':data}
    (outdir/'inverse_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'configs':len(data),'seconds':result['computation_seconds'],
                      'parity_inconsistent':sum(x['first_parity_contradiction_draw'] is not None for x in data),
                      'consistent':sum(x['first_parity_contradiction_draw'] is None for x in data),
                      'max_prefix':max(x['prefix_lowbit_consistent'] for x in data)},indent=2))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--outdir',default='.')
    p.add_argument('--limit',type=int,default=140);p.add_argument('--maxstride',type=int,default=8)
    a=p.parse_args();run(load(a.input),Path(a.outdir),limit=a.limit,maxstride=a.maxstride)
