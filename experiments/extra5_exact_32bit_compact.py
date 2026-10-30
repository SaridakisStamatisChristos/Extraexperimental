#!/usr/bin/env python3
"""Enumerate exact 32-bit-state preimages for four historical EXTRA 5 draws.
Narrow synthetic 5-PRNG/3-sampler experiment, NOT the production lottery RNG.
"""
import json
N = 324632
MASK = (1 << 32)-1
RANKS = (55817,57278,268706,23073)
FAMS = ('xs13_17_5','xs5_13_6','lcg_nr','lcg_ansi','fmix_counter')
SAMPLERS = ('hi24','lo24','full32')
L24 = ((1 << 24)//N)*N
L32 = ((1 << 32)//N)*N

def undo_right(v,k):
    while k<32:
        v ^= v>>k
        k*=2
    return v&MASK

def fmix_inv(v):
    v=undo_right(v,16)
    v=(v*pow(0xc2b2ae35,-1,1<<32))&MASK
    v=undo_right(v,13)
    v=(v*pow(0x85ebca6b,-1,1<<32))&MASK
    return undo_right(v,16)

def fmix(v):
    v^=v>>16;v=v*0x85ebca6b&MASK
    v^=v>>13;v=v*0xc2b2ae35&MASK
    return (v^(v>>16))&MASK

def step(kind,s):
    if kind=='xs13_17_5':
        s^=s<<13&MASK;s^=s>>17;s^=s<<5&MASK
        return s&MASK,s&MASK
    if kind=='xs5_13_6':
        s^=s<<5&MASK;s^=s>>13;s^=s<<6&MASK
        return s&MASK,s&MASK
    if kind=='lcg_nr':
        s=(1664525*s+1013904223)&MASK
        return s,s
    if kind=='lcg_ansi':
        s=(1103515245*s+12345)&MASK
        return s,s
    s=(s+0x9e3779b9)&MASK
    return s,fmix(s)

def accepted(word,variant):
    r=word>>8 if variant=='hi24' else word&0xffffff if variant=='lo24' else word
    return r%N if r<(L32 if variant=='full32' else L24) else None

def first_words(variant):
    if variant=='full32':
        for k in range((1<<32)//N):
            yield RANKS[0]+k*N
    else:
        for k in range((1<<24)//N):
            v=RANKS[0]+k*N
            for b in range(256):
                yield v<<8|b if variant=='hi24' else b<<24|v

def one(kind,variant,state):
    for _ in range(1025):
        state,word=step(kind,state)
        r=accepted(word,variant)
        if r is not None:return state,r
    raise RuntimeError('unresolved rejection sequence')

def run():
    records=[];hits=[]
    for kind in FAMS:
        for variant in SAMPLERS:
            total=0;double=triple=quad=unresolved=0
            for first in first_words(variant):
                total+=1
                state=fmix_inv(first) if kind=='fmix_counter' else first
                matched=1
                try:
                    for target in RANKS[1:]:
                        state,r=one(kind,variant,state)
                        if r!=target:break
                        matched+=1
                except RuntimeError:
                    unresolved+=1;continue
                if matched>=2:
                    double+=1
                    if matched>=3:triple+=1
                    if matched>=4:quad+=1
                    hits.append({'model':kind,'sampler':variant,'first_word':first,'matching_draws':matched})
            records.append({'model':kind,'sampler':variant,'first_compatible_states':total,
                            'exact_2':double,'exact_3':triple,'exact_4':quad,'unresolved':unresolved})
    sums={'first_compatible_states':sum(x['first_compatible_states'] for x in records),
          'exact_2':sum(x['exact_2'] for x in records),
          'exact_3':sum(x['exact_3'] for x in records),
          'exact_4':sum(x['exact_4'] for x in records),
          'unresolved':sum(x['unresolved'] for x in records)}
    assert sums=={'first_compatible_states':196710,'exact_2':1,'exact_3':0,'exact_4':0,'unresolved':0}
    assert hits==[{'model':'fmix_counter','sampler':'full32','first_word':414935513,'matching_draws':2}]
    return {'ranks':list(RANKS),'model_results':records,'totals':sums,'witnesses':hits,
            'limitations':'Exact only for specified invertible 32bit algorithms/three samplers. Not operator RNG identification.'}

if __name__=='__main__':
    print(json.dumps(run(),indent=2))
