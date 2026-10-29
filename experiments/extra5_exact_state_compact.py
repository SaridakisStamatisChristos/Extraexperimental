"""Exact first-output-state enumeration for 5 toy 32-bit PRNGs x 3 samplers."""
import json
from itertools import product
from pathlib import Path

N=324632
RANKS=(55817,57278,268706,23073)
FAMILIES=('xorshift32_13_17_5','xorshift32_5_13_6','lcg32_nr','lcg32_ansi','splitmix32_fmix')
MAPPINGS=('high24','low24','full32')
MASK=0xffffffff
GAMMA=0x9e3779b9

def undo_right(y,shift):
    x=y
    for _ in range(32):x=y^(x>>shift)
    return x

def fmix(x):
    x^=x>>16;x=x*0x85ebca6b&MASK
    x^=x>>13;x=x*0xc2b2ae35&MASK
    return x^(x>>16)

def unmix(x):
    x=undo_right(x,16)*pow(0xc2b2ae35,-1,1<<32)&MASK
    x=undo_right(x,13)*pow(0x85ebca6b,-1,1<<32)&MASK
    return undo_right(x,16)

def next_word(f,w):
    if f=='splitmix32_fmix':return fmix((unmix(w)+GAMMA)&MASK)
    if f.startswith('xorshift32'):
        a,b,c=(13,17,5) if f=='xorshift32_13_17_5' else (5,13,6)
        w^=(w<<a)&MASK;w^=w>>b;w^=(w<<c)&MASK
        return w&MASK
    a,c=(1664525,1013904223) if f=='lcg32_nr' else (1103515245,12345)
    return (a*w+c)&MASK

def sample(w,m):
    width=32 if m=='full32' else 24
    v=w if m=='full32' else w>>8 if m=='high24' else w&0xffffff
    return v%N if v<((1<<width)//N)*N else None

def first_words(m):
    width=32 if m=='full32' else 24
    for q in range((1<<width)//N):
        v=q*N+RANKS[0]
        for tail in range(1 if m=='full32' else 256):
            yield v if m=='full32' else (v<<8)|tail if m=='high24' else (tail<<24)|v

def follow(f,m,w):
    for _ in range(1025):
        w=next_word(f,w)
        r=sample(w,m)
        if r is not None:return r,w
    raise RuntimeError('unresolved rejection run')

def experiment():
    rows=[]
    for f,m in product(FAMILIES,MAPPINGS):
        counts=[0,0,0,0]; witnesses=[]
        for w in first_words(m):
            assert sample(w,m)==RANKS[0]
            counts[0]+=1
            state=w
            for i in range(1,4):
                rank,state=follow(f,m,state)
                if rank!=RANKS[i]:break
                counts[i]+=1
                if i==1:
                    r3,w3=follow(f,m,state)
                    r4,_=follow(f,m,w3)
                    witnesses.append({'first_accepted_word':w,'next_two_ranks':[r3,r4]})
        rows.append({'family':f,'mapping':m,'first':counts[0],
                     'two':counts[1],'three':counts[2],'four':counts[3],
                     'two_draw_witnesses':witnesses})
    return {'draws':[14249,14250,14251,14252],'ranks':list(RANKS),
            'model':'fixed 32-bit reversible generator; one word per ticket; no reseeding; rejection-based ticket-rank sampler',
            'results':rows,
            'aggregate':{'first_output_states':sum(r['first'] for r in rows),
                         'two':sum(r['two'] for r in rows),
                         'three':sum(r['three'] for r in rows),
                         'four':sum(r['four'] for r in rows)},
            'caveat':'Exhaustive only for these five synthetic 32-bit mechanisms and three ticket mappings. Not an Allwyn RNG recovery.'}

if __name__=='__main__':
    result=experiment()
    Path(__file__).with_name('extra5_exact_state_compact_results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result['aggregate'])
