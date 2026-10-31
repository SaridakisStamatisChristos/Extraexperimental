#!/usr/bin/env python3
"""Full research accounting; assert every output/configuration is included once."""
from __future__ import annotations
import csv, collections, hashlib, json
from pathlib import Path
from independent_verify import gen, expected_allowed, load_masks

ROOT=Path(__file__).resolve().parent
REAL=ROOT/'real_unordered.csv'
TOTAL_TRIPLES=31**3
MODELS_PER_SAMPLER=TOTAL_TRIPLES*2*5

def records(paths):
    for path in paths:
        with open(path,newline='') as f:
            yield from csv.DictReader(f)

def key(r):
    return tuple(int(r[k]) for k in ('direction','shift_a','shift_b','shift_c','extra_gap'))

def aggregate(paths):
    found={};count=collections.Counter();rank=collections.Counter();matches=[]
    for r in records(paths):
        k=key(r)
        assert k not in found,('DUPLICATE_CONFIG',k)
        found[k]=r
        count['configurations']+=1
        rank[int(r['matrix_rank'])]+=1
        if int(r['enumerated']):
            count['enumerated']+=1
            count['branches']+=int(r['branches'])
            count['compatible_index_assignments']+=int(r['linear_consistent_seeds'])
            count['passed_extra_constraints']+=int(r['passed_additional_fourth_constraints'])
            count['one_ticket_matches']+=int(r['one_exact'])
            count['two_ticket_matches']+=int(r['at_least_two_exact'])
        else:
            count['underdetermined']+=1
        if int(r['max_exact_prefix'])>0:
            matches.append({k2:r[k2] for k2 in ('direction','shift_a','shift_b','shift_c','extra_gap','matrix_rank','max_exact_prefix','witness_seed')})
    return found,dict(count),dict(rank),matches

def replay_first_match(r,sampler):
    a,b,c,dir,gap,seed=(int(r[k]) for k in ('shift_a','shift_b','shift_c','direction','extra_gap','witness_seed'))
    mask=0xffffffff
    real=[int(r['ticket_mask']) for r in load_masks(REAL)[:100]]
    s=seed
    for d,ticket in enumerate(real):
        chosen=[];available=list(range(1,36))
        for _ in range(5):
            if not dir:
                s^=(s<<a)&mask;s^=s>>b;s^=(s<<c)&mask
            else:
                s^=s>>a;s^=(s<<b)&mask;s^=s>>c
            s&=mask
            index=(s%len(available)) if sampler=='mod' else ((s*len(available))>>32)
            chosen.append(available.pop(index))
        for _ in range(gap):
            if not dir:
                s^=(s<<a)&mask;s^=s>>b;s^=(s<<c)&mask
            else:
                s^=s>>a;s^=(s<<b)&mask;s^=s>>c
            s&=mask
        calc=sum(1<<(v-1) for v in chosen)
        if calc!=ticket:return d
    return len(real)

def phase_data(stage_a,stage_b,sampler):
    first,cf,rf,match1=aggregate(stage_a)
    assert cf['configurations']==MODELS_PER_SAMPLER,cf
    second,cs,rs,match2=aggregate(stage_b)
    assert all(k in first and not int(first[k]['enumerated']) for k in second)
    assert cs['configurations']==cf['underdetermined'],(cs,cf)
    total=cf['enumerated']+cs['enumerated']
    unique={**first,**second}
    # When the second stage skipped a model, it's still unsolved, not refuted.
    total_left=MODELS_PER_SAMPLER-total
    matches=match1+match2
    for r in matches:
        assert replay_first_match(r,sampler)==int(r['max_exact_prefix']),(sampler,r)
    prim={tuple(int(t[k]) for k in ('direction','a','b','c')) for t in records([ROOT/'primitive_triples.csv'])}
    prim_rows=[r for k,r in unique.items() if k[:4] in prim]
    assert len(prim_rows)==len(prim)*5
    assert all(int(r['enumerated']) and int(r['max_exact_prefix'])==0 for r in prim_rows)
    return dict(sampler=sampler,total=cf['configurations'],seven_observation=cf,eight_observation=cs,
                fully_enumerated=total,not_fully_enumerated=total_left,
                primitive_models=len(prim_rows),primitive_models_fully_refuted=len(prim_rows),
                exact_first_ticket_model_states=len(matches),full_prefix_max=max([int(r['max_exact_prefix']) for r in matches],default=0),
                second_ticket_survivors=cf.get('two_ticket_matches',0)+cs.get('two_ticket_matches',0),
                model_witnesses=matches,rank7=rf,rank8=rs)

def main():
    modulo=phase_data(sorted(ROOT.glob('full_*.csv')),sorted(ROOT.glob('stage2_*.csv')),'mod')
    primitive={tuple(int(t[k]) for k in ('direction','a','b','c')) for t in records([ROOT/'primitive_triples.csv'])}
    ph,cp,rp,mp=aggregate([ROOT/'high_primitive_all.csv'])
    assert len(ph)==len(primitive)*5 and cp['enumerated']==cp['configurations'] and not mp
    high=phase_data(sorted(ROOT.glob('high_full_*.csv')),sorted(ROOT.glob('high_stage2_*.csv')),'high')
    result=dict(modulo=modulo, multiply_high=high, high_primitive=cp)
    (ROOT/'RESEARCH_RESULTS.json').write_text(json.dumps(result,indent=2))
    print('MODULO:',json.dumps({k:v for k,v in modulo.items() if k not in ('model_witnesses','rank7','rank8')},indent=2))
    print('HIGH:',json.dumps({k:v for k,v in high.items() if k not in ('model_witnesses','rank7','rank8')},indent=2))
    print('HIGH_PRIMITIVE:',json.dumps(cp,indent=2))
    return result

if __name__=='__main__':main()
