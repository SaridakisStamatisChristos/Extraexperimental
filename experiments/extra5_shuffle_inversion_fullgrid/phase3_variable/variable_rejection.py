#!/usr/bin/env python3
"""Exact finite-budget variable-consumption inversion for one-word 5-of-35 rank sampling.

Models a GF(2)-linear state transition with an output having one or more
provably linear low bits (including true xoroshiro128+ / xoshiro256+ LSB).
Enumerates *paths* of rejected output words instead of assuming fixed
alignment. A path's accepted-word positions are known, giving exact GF(2)
equations. Recovered state is always checked by full independently computed
rejection-rule replay. No seed brute force and no claim about actual EXTRA 5.

'accept_multiple' is an OPTIONAL deliberately inefficient uniform-rejection
stress control. The actual conventional scheme uses max floor(2^W/N).
"""
from __future__ import annotations
from itertools import combinations_with_replacement
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "phase3_rank"))
import time
from math import comb
from rank_inverse import MODELS, N, combination_rank, combination_unrank, solve


def threshold(model, accept_multiple=None):
    maximum=(1<<model.word_bits)//N
    if accept_multiple is None:
        multiple=maximum
    else:
        multiple=int(accept_multiple)
        if multiple<=0 or multiple>maximum:raise ValueError('out of range acceptance multiplier')
    return N*multiple


def generate_trace(model,seed,n,gap=0,accept_multiple=None):
    """Return (tickets, rejected_words_per_draw, raw accepted words) independently of recovery."""
    if n<0 or gap<0:raise ValueError('bad n or gap')
    state=model.decode(seed);limit=threshold(model,accept_multiple)
    tickets=[];skips=[];words=[]
    for _ in range(n):
        rejected=0
        while True:
            state,w=model.step(state)
            if w<limit:break
            rejected+=1
        tickets.append(combination_unrank(w%N))
        skips.append(rejected);words.append(w)
        for _ in range(gap):state,_=model.step(state)
    return tickets,skips,words


def ordinal_forms(model,steps):
    """All output-word linear projection forms; ordinal index 0 = first step."""
    if steps<0:raise ValueError('negative steps')
    out=[[0]*model.proved_linear_low_bits for _ in range(steps)]
    for j in range(model.size):
        s=model.decode(1<<j)
        for t in range(steps):
            s,w=model.step(s)
            for k in range(model.proved_linear_low_bits):
                if (w>>k)&1:out[t][k]|=1<<j
    return out


def ordinal_positions(n,gap,skip_positions):
    """Index of accepted word for each draw; skip positions are zero-based draw IDs.

    Repeated index denotes multiple rejected words before one accepted word.
    """
    if n<1 or gap<0 or any(not 0<=p<n for p in skip_positions):raise ValueError('invalid path')
    t=0;positions=[];j=0
    for d in range(n):
        while j<len(skip_positions) and skip_positions[j]==d:
            t+=1;j+=1
        positions.append(t)
        t+=1+gap
    return positions


def recover_bounded(model,tickets,gap=0,max_skips=1,max_paths=None,
                    accept_multiple=None,minimum_skips=0):
    """Joint inversion of seed and rejection path within a finite skip budget.

    On SAT: a FULL-TICKET verified witness, but other witnesses might exist.
    On UNSAT: all bounded paths were exhausted AND all cases had full-rank
      equations or mathematical contradictions, with zero valid witnesses.
    On UNKNOWN: a budget was reached, or some path remains underdetermined.
      No claim about paths with >max_skips rejections.
    """
    if not tickets or gap<0 or max_skips<0 or not 0<=minimum_skips<=max_skips or (max_paths is not None and max_paths<1):
        raise ValueError('invalid arguments')
    t0=time.monotonic();n=len(tickets);width=model.proved_linear_low_bits
    ranks=[combination_rank(x) for x in tickets]
    forms=ordinal_forms(model,n*(gap+1)+max_skips)
    limit=threshold(model,accept_multiple)
    paths_tested=0;rank_deficient=0;linear_inconsistent=0;unique_replay_fail=0
    total_paths=sum(comb(n+k-1,k) for k in range(minimum_skips,max_skips+1))
    complete=True
    for k in range(minimum_skips,max_skips+1):
        for path in combinations_with_replacement(range(n),k):
            if max_paths is not None and paths_tested>=max_paths:
                complete=False;break
            paths_tested+=1
            ordinal=ordinal_positions(n,gap,path)
            equations=[(forms[t][b],(ranks[d]>>b)&1) for d,t in enumerate(ordinal) for b in range(width)]
            result=solve(equations,model.size)
            if result['status']=='UNKNOWN':
                rank_deficient+=1;continue
            if result['status']=='UNSAT':
                linear_inconsistent+=1;continue
            seed=result['seed']
            replay,actual_skips,words=generate_trace(model,seed,n,gap,accept_multiple)
            if replay==list(tickets) and tuple(i for d,c in enumerate(actual_skips) for i in [d]*c)==path:
                return {'status':'SAT','seed':f'0x{seed:0{model.size//4}x}',
                    'model':model.name,'sampler':'one_word_rank_uniform_rejection',
                    'accepted_limit':limit,'canonical_rejection':accept_multiple is None,
                    'gap':gap,'max_skips':max_skips,'minimum_skips':minimum_skips,'recovered_path':list(path),
                    'actual_rejections':sum(actual_skips),'exact_training_tickets':n,
                    'linear_rank':result['rank'],'paths_tested':paths_tested,
                    'total_bounded_paths':total_paths,'search_complete':paths_tested==total_paths,
                    'seconds':round(time.monotonic()-t0,6)}
            unique_replay_fail+=1
        if not complete:break
    return {'status':'UNKNOWN' if (not complete or rank_deficient) else 'UNSAT',
            'model':model.name,'sampler':'one_word_rank_uniform_rejection',
            'accepted_limit':limit,'canonical_rejection':accept_multiple is None,
            'gap':gap,'max_skips':max_skips,'minimum_skips':minimum_skips,'paths_tested':paths_tested,
            'total_bounded_paths':total_paths,'search_complete':complete,
            'rank_deficient_paths':rank_deficient,
            'linearly_inconsistent_paths':linear_inconsistent,
            'unique_state_replay_failures':unique_replay_fail,
            'seconds':round(time.monotonic()-t0,6),
            'limitation':'Only paths with <= max_skips discarded outputs are analyzed'}


def recover_from_prefix(model, tickets, prefix_length, gap=0, max_prefix_skips=2,
                        max_paths=None, accept_multiple=None):
    """Exact prefix-bounded inversion; suffix rejection count is NOT bounded.

    Enumerate rejected output-word placements only within an informative prefix.
    Each full-rank seed is replayed against *all* tickets with actual rejection
    decisions. If all prefix paths are full rank or contradictory and no replay
    witness exists, this proves UNSAT for the model with <=K prefix rejections,
    regardless of later rejections (which are determined by the initial state).
    """
    if not tickets or not 1<=prefix_length<=len(tickets) or gap<0 or max_prefix_skips<0:
        raise ValueError('invalid prefix parameters')
    if max_paths is not None and max_paths<1:raise ValueError('invalid path cap')
    n=prefix_length;start=time.monotonic();width=model.proved_linear_low_bits
    ranks=[combination_rank(x) for x in tickets[:n]]
    forms=ordinal_forms(model,n*(gap+1)+max_prefix_skips)
    total=sum(comb(n+k-1,k) for k in range(max_prefix_skips+1))
    tested=0;rank_deficient=0;linear_contradictions=0;replay_mismatches=0
    truncated=False
    for k in range(max_prefix_skips+1):
        for path in combinations_with_replacement(range(n),k):
            if max_paths is not None and tested>=max_paths:
                truncated=True;break
            tested+=1
            indices=ordinal_positions(n,gap,path)
            equations=[(forms[idx][bit],(ranks[d]>>bit)&1)
                       for d,idx in enumerate(indices) for bit in range(width)]
            ans=solve(equations,model.size)
            if ans['status']=='UNKNOWN':rank_deficient+=1;continue
            if ans['status']=='UNSAT':linear_contradictions+=1;continue
            seed=ans['seed']
            replay,counts,_=generate_trace(model,seed,len(tickets),gap,accept_multiple)
            actual_prefix=tuple(d for d,c in enumerate(counts[:n]) for _ in range(c))
            if replay==list(tickets) and actual_prefix==path:
                return {'status':'SAT','model':model.name,'seed':f'0x{seed:0{model.size//4}x}',
                        'training_tickets_replayed':len(tickets),'prefix_length':n,
                        'max_prefix_skips':max_prefix_skips,'recovered_prefix_path':list(path),
                        'realized_suffix_rejections':sum(counts[n:]),
                        'paths_tested':tested,'total_prefix_paths':total,
                        'search_complete':tested==total,'gap':gap,
                        'seconds':round(time.monotonic()-start,6)}
            replay_mismatches+=1
        if truncated:break
    return {'status':'UNKNOWN' if (truncated or rank_deficient) else 'UNSAT',
            'model':model.name,'training_tickets_replayed':len(tickets),
            'prefix_length':n,'max_prefix_skips':max_prefix_skips,
            'paths_tested':tested,'total_prefix_paths':total,
            'search_complete':not truncated,'rank_deficient_paths':rank_deficient,
            'linearly_inconsistent_paths':linear_contradictions,
            'full_replay_rejected_candidates':replay_mismatches,'gap':gap,
            'suffix_rejection_bound':'NONE; determined by forward replay',
            'seconds':round(time.monotonic()-start,6)}
