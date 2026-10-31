#!/usr/bin/env python3
"""Deterministic, bounded, replayable Phase 2 experiment evidence."""
import argparse
import json
import math
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from inverse_linear import MODELS, ticket, fourth_domain, forms, solve_equations, replay
from smt_unordered import Solver, build_formula, selected_domains

SAMPLES=[0x0123456789abcdef112233445566778899aabbccddeeff0013579bdf2468ace1,
         0xabcdef9876543210ffeeddccbbaa99887766554433221100deadbeefcafef00d]

def run(smt_ms=1200):
    entries=[];first_case=None
    for model in MODELS.values():
        for sampler in ('mod','high'):
            for gap in (0,2):
                for i,nominal_seed in enumerate(SAMPLES):
                    seed=nominal_seed % (1<<model.size)
                    state=model.from_integer(seed)
                    sets=[];indices=[]
                    for d in range(210):
                        state,out,idx=ticket(model,state,gap,sampler)
                        sets.append(out)
                        if d<160:indices.append((d,idx[3]))
                    if first_case is None:first_case=(model,sets)
                    start=time.perf_counter()
                    ff=forms(model,160,gap,sampler)
                    eq=[];rank_trace={};result=None;min_full_rank=None
                    for k,(d,v) in enumerate(indices,1):
                        eq.extend((ff[d][b],(v>>b)&1) for b in range(5))
                        result=solve_equations(eq,model.size)
                        if k in (8,16,26,32,52,64,80,160):rank_trace[str(k)]=result.rank
                        if result.rank==model.size and min_full_rank is None:min_full_rank=k
                    sec=time.perf_counter()-start
                    assert result.rank==model.size and result.seed==seed
                    assert replay(model,result.seed,sets,gap,sampler)
                    entries.append({'model':model.name,'state_bits':model.size,'sampler':sampler,'extra_gap':gap,
                        'seed_hex':f'{seed:0{model.size//4}x}','rank':result.rank,'nullity':len(result.nullspace),
                        'min_fourth_indices_for_full_rank':min_full_rank,'rank_by_observation':rank_trace,
                        'full_ticket_replay':210,'reserved_continuation':50,'recovered_seed_equals_planted':True,
                        'elapsed_seconds_gf2':sec})
    probes=[]
    model,tickets=first_case
    solver=Solver()
    for k in (24,35,50):
        ids=selected_domains(tickets[:160],k)
        formula=build_formula(model,tickets,ids)
        res=solver.run(formula,smt_ms)
        product=math.prod(len(fourth_domain(tickets[d])) for d in ids)
        probes.append({'model':model.name,'known_extraction_order':False,'selected_observations':k,'smt_input_bytes':len(formula.encode()),
            'domain_product_decimal_digits':len(str(product)),'z3_timeout_ms':smt_ms,**res})
    return {'timestamp_local':'2026-10-31','branch':'research/inverse-64-hybrid',
        'scope':'synthetic transition-only models; does not recover production RNG',
        'python':sys.version.split()[0], 'platform':platform.platform(),
        'cpu':platform.processor(),'libz3':'libz3.so.4',
        'cases':entries,'smt_unordered_probes':probes,
        'claim':'known fourth-selection index recovery; not unordered recovery for 128/256'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--smt-ms',type=int,default=1200)
    ap.add_argument('--output',type=Path,default=Path('PHASE2_RESULTS.json'))
    arg=ap.parse_args()
    data=run(arg.smt_ms)
    arg.output.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps({'cases':len(data['cases']),'exact_recoveries':sum(x['recovered_seed_equals_planted'] for x in data['cases']),
     'reserved_full_tickets':sum(x['reserved_continuation'] for x in data['cases']),
     'z3_probes':data['smt_unordered_probes']},indent=2))
