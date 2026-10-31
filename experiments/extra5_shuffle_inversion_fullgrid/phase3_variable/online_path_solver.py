#!/usr/bin/env python3
"""Exact incremental GF(2) inversion with rejection-path branch pruning.

Restricted to the specified one-word lexicographic-combination-rank rejection
sampler and GF(2)-linear observed low bits. No claims about deployed EXTRA 5.
The transition/output and the sampler must both be explicitly specified.
"""
from __future__ import annotations
from math import comb
from time import perf_counter
from variable_rejection import ordinal_forms, threshold
from rank_inverse import N
from rank_inverse import combination_rank


def candidate_from_pivots(pivots):
    """Return the unique seed for a full-rank homogeneous-coefficient system."""
    seed=0
    for p in range(len(pivots)):
        row=pivots[p]
        if row is None:raise ValueError('underdetermined')
        x,v=row
        if v ^ ((x & seed).bit_count()&1):seed|=1<<p
    return seed


def count_allocations(draws,remaining):
    """Stars-and-bars count of vectors of nonnegative skip counts summing <= remaining."""
    if draws == 0:return 1
    return comb(draws+remaining,remaining)


def replay_until_mismatch(model,seed,ranks,gap,partial_counts,limit,max_rejections_per_ticket=100000):
    """Independent acceptance/rejection replay, stop at first incorrect rank.

    Never unrank a ticket: rank 0..N-1 already identifies the entire set.
    If an extreme rejection cycle exceeds the safety cap, return None
    (inconclusive), not False. This ensures proof status stays conservative.
    """
    s=model.decode(seed);counts=[]
    for d,expected in enumerate(ranks):
        r=0
        while True:
            s,w=model.step(s)
            if w<limit:break
            r+=1
            if r>max_rejections_per_ticket:return None
        if w%N != expected or (d<len(partial_counts) and r!=partial_counts[d]):return False
        counts.append(r)
        for _ in range(gap):s,_=model.step(s)
    return counts


def recover_online(model,tickets,gap=0,max_prefix_skips=3,prefix_length=None,
                   max_nodes=None,accept_multiple=None):
    """Online exact path enumeration with reversible linear basis.

    A contradiction prunes ALL future skip allocations for that prefix.
    A unique state can be independently forward replayed and pruned early.
    Return UNSAT only if every prefix path is ruled out with valid full-rank
    replay or a linear contradiction; rank-deficient leaves give UNKNOWN.
    Path-budget truncation also gives UNKNOWN. SAT witnesses are subject to
    actual acceptance/rejection replay, not just low-bit agreement.
    """
    if prefix_length is None:prefix_length=len(tickets)
    if not tickets or not 1<=prefix_length<=len(tickets) or gap<0 or max_prefix_skips<0:
        raise ValueError('invalid prefix/model')
    if max_nodes is not None and max_nodes<1:raise ValueError('node budget must be positive')
    t0=perf_counter();n=prefix_length;kmax=max_prefix_skips
    ranks=[combination_rank(t) for t in tickets]
    forms=ordinal_forms(model,n*(gap+1)+kmax)
    dim=model.size;width=model.proved_linear_low_bits
    pivots=[None]*dim
    visited=0;rank=0;rankdef=0;inconsistent=0;replay_reject=0
    rejected_subpaths=0;truncated=False;witness=None;path=[];full_ranks=0;indeterminate_replays=0
    total=count_allocations(n,kmax)
    # Applying equations only toggles new pivots, so undo just those touched.
    def add_equations(draw,position):
        nonlocal rank
        changed=[]
        for b in range(width):
            x=forms[position][b];v=(ranks[draw]>>b)&1
            while x:
                pivot=x.bit_length()-1
                old=pivots[pivot]
                if old is None:
                    pivots[pivot]=(x,v);changed.append(pivot);rank+=1;break
                x^=old[0];v^=old[1]
            else:
                if v:return False,changed
        return True,changed
    def undo(changed):
        nonlocal rank
        for j in changed:
            pivots[j]=None;rank-=1

    def dfs(d,ordinal,skips):
        nonlocal visited,rankdef,inconsistent,replay_reject,rejected_subpaths,truncated,witness,full_ranks,indeterminate_replays
        if witness is not None or truncated:return
        if max_nodes is not None and visited>=max_nodes:
            truncated=True;return
        visited+=1
        if d==n:
            if rank<dim:rankdef+=1;return
            # full-rank paths should already have been replayed when rank reached dim
            raise AssertionError('full rank reached a terminal node without replay')
        for extra in range(kmax-skips+1):
            pos=ordinal+extra
            ok,changed=add_equations(d,pos)
            path.append(extra)
            if not ok:
                inconsistent+=1
                rejected_subpaths+=count_allocations(n-d-1,kmax-skips-extra)
            elif rank==dim:
                full_ranks+=1
                seed=candidate_from_pivots(pivots)
                # The unique state must reproduce every known ticket using the
                # exact rejection decision. No future path can change this.
                counts=replay_until_mismatch(model,seed,ranks,gap,path,
                                             threshold(model,accept_multiple))
                if counts is None:
                    indeterminate_replays+=1
                elif counts and sum(counts[:n])<=kmax:
                        witness={
                            'seed':f'0x{seed:0{dim//4}x}',
                            'recovered_prefix_skip_counts':counts[:n],
                            'prefix_rejections':sum(counts[:n]),
                            'suffix_rejections':sum(counts[n:]),
                            'full_ticket_replay':len(tickets),
                            'early_rank_completion_draw':d+1,
                        }
                elif counts is not None:
                    replay_reject+=1
                    rejected_subpaths+=count_allocations(n-d-1,kmax-skips-extra)
            else:
                dfs(d+1,pos+1+gap,skips+extra)
            path.pop();undo(changed)
            if witness is not None or truncated:return
    dfs(0,0,0)
    status='SAT' if witness else 'UNKNOWN' if (truncated or rankdef or indeterminate_replays) else 'UNSAT'
    if status=='UNSAT' and rejected_subpaths!=total:
        raise AssertionError('UNSAT must account for every bounded skip path')
    return {
        'status':status,'model':model.name,'sampler':'one_word_rank_uniform_rejection',
        'gap':gap,'prefix_length':n,'max_prefix_skips':kmax,
        'total_prefix_paths':total,'nodes_visited':visited,
        'pruned_leaf_path_multiplicity':rejected_subpaths,
        'contradiction_nodes':inconsistent,'unique_state_replay_rejections':replay_reject,
        'full_rank_candidates_checked':full_ranks,'indeterminate_replays':indeterminate_replays,
        'rank_deficient_terminal_paths':rankdef,
        'search_complete':not truncated and witness is None,
        'accepted_threshold':threshold(model,accept_multiple),
        'canonical_rejection':accept_multiple is None,
        'budget_exceeded':truncated,
        'witness':witness,
        'elapsed_seconds':round(perf_counter()-t0,6),
        'scope':'Only paths with <= max_prefix_skips rejections in the prefix, any later rejections are replayed exactly',
    }
