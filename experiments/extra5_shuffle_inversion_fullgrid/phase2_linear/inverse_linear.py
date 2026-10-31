"""GF(2) inverse-state engine for specified raw-output linear PRNG models.

The fifth modulus=31 is *not* linear: only the fourth selection's 32-way
index provides exactly five linear state equations. Known index observations
must come from a synthetic oracle or authenticated extraction order, never
from a published lottery permutation without a justification.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable

M32=(1<<32)-1
M64=(1<<64)-1


def rotl(x,k,width):
    m=(1<<width)-1
    return ((x<<k)|(x>>(width-k)))&m

@dataclass(frozen=True)
class LinearModel:
    name:str
    words:int
    bits:int
    transition:Callable[[tuple[int,...]],tuple[tuple[int,...],int]]

    @property
    def size(self): return self.words*self.bits

    def from_integer(self,state:int)->tuple[int,...]:
        if not (0<=state<1<<self.size): raise ValueError('state outside model')
        return tuple((state>>(self.bits*i)) & ((1<<self.bits)-1) for i in range(self.words))


def xorshift128_marsaglia(s):
    # Marsaglia 2003 four 32-bit words; new w is emitted on each transition.
    x,y,z,w=s
    t=(x^((x<<11)&M32))&M32
    w1=(w^(w>>19)^t^(t>>8))&M32
    return (y,z,w,w1),w1


def xoroshiro128_raw(s):
    # xoroshiro128+ state transition ONLY. Emit raw s0 after transition;
    # not the published '+', '++', or '**' output function.
    s0,s1=s
    s1^=s0
    new=(rotl(s0,24,64)^s1^((s1<<16)&M64), rotl(s1,37,64))
    return new,new[0]


def xoshiro256_raw(s):
    # xoshiro256** state transition ONLY; raw s0 output is a diagnostic
    # linear projection, NOT the published '**' scrambler.
    s0,s1,s2,s3=s
    t=(s1<<17)&M64
    s2^=s0;s3^=s1;s1^=s2;s0^=s3;s2^=t;s3=rotl(s3,45,64)
    new=(s0,s1,s2,s3)
    return new,s0

MODELS={
    'xorshift128':LinearModel('xorshift128',4,32,xorshift128_marsaglia),
    'xoroshiro128_raw':LinearModel('xoroshiro128_raw',2,64,xoroshiro128_raw),
    'xoshiro256_raw':LinearModel('xoshiro256_raw',4,64,xoshiro256_raw),
}


def ticket(model:LinearModel,state:tuple[int,...],gap:int=0,sampler:str='mod'):
    if sampler not in ('mod','high'): raise ValueError('sampler must be mod or high')
    pool=list(range(1,36));result=[];indices=[]
    for _ in range(5):
        state,word=model.transition(state)
        n=len(pool)
        index=word%n if sampler=='mod' else (word*n)>>model.bits
        indices.append(index)
        result.append(pool.pop(index))
    for _ in range(gap):state,_=model.transition(state)
    return state,tuple(sorted(result)),tuple(indices)


def fourth_domain(numbers):
    if len(numbers)!=5 or len(set(numbers))!=5 or not all(1<=n<=35 for n in numbers):
        raise ValueError('invalid unordered 5/35 ticket')
    numbers=sorted(numbers)
    a=set()
    for below,v in enumerate(numbers):
        for removed in range(max(0,below-1),min(3,below)+1):
            a.add(v-1-removed)
    return frozenset(a)


def forms(model:LinearModel,n:int,gap:int=0,sampler:str='mod'):
    """Each fourth selection encoded as 5 binary linear forms of initial state."""
    if n<0 or gap<0 or sampler not in ('mod','high'): raise ValueError('bad arguments')
    f=[[0]*5 for _ in range(n)]
    for bit in range(model.size):
        state=model.from_integer(1<<bit)
        for d in range(n):
            for j in range(5):
                state,word=model.transition(state)
                if j==3: fourth=word
            for _ in range(gap):state,_=model.transition(state)
            for k in range(5):
                if (fourth>>(k if sampler=='mod' else model.bits-5+k))&1:
                    f[d][k]|=1<<bit
    return [tuple(r) for r in f]


@dataclass
class LinearSolution:
    status:str
    rank:int
    seed:int|None
    nullspace:tuple[int,...]
    conflicting_row:int|None=None


def solve_equations(equations,dimension:int):
    """Exact RREF-style binary elimination and complete homogeneous basis."""
    pivots={};rank=0
    for row_index,(coeff,rhs) in enumerate(equations):
        if coeff>>dimension or coeff<0 or rhs not in (0,1):
            raise ValueError('out-of-range GF2 equation')
        x=coeff;v=rhs
        while x:
            p=x.bit_length()-1
            if p not in pivots:
                pivots[p]=(x,v);rank+=1;break
            q,b=pivots[p];x^=q;v^=b
        else:
            if v: return LinearSolution('UNSAT',rank,None,(),row_index)
    seed=0
    for p in sorted(pivots):
        row,bit=pivots[p]
        if (bit^(row&seed).bit_count()&1):seed|=1<<p
    null=[]
    for free in range(dimension):
        if free in pivots:continue
        v=1<<free
        for p in sorted(pivots):
            if (pivots[p][0]&v).bit_count()&1:v|=1<<p
        null.append(v)
    return LinearSolution('SAT',rank,seed,tuple(null))


def recover_known_fourth(model,observations,gap=0,sampler='mod'):
    """observations=(chronological ticket index, exact fourth index)."""
    obs=list(observations)
    if not obs:raise ValueError('no observations')
    if len(set(d for d,_ in obs))!=len(obs):raise ValueError('duplicate observation index')
    if any(d<0 or not 0<=v<32 for d,v in obs):raise ValueError('bad index/value')
    all_forms=forms(model,max(d for d,_ in obs)+1,gap,sampler)
    return solve_equations(
        ((all_forms[d][k],(v>>k)&1) for d,v in obs for k in range(5)),model.size)


def replay(model,state,tickets,gap=0,sampler='mod'):
    """True when all exact unordered sets match, starting from state."""
    s=model.from_integer(state)
    for target in tickets:
        s,observed,_=ticket(model,s,gap,sampler)
        if set(observed)!=set(target):return False
    return True
