#!/usr/bin/env python3
"""Deterministic synthetic controls and measured Phase 3B result artifact."""
import json, platform, sys, time, math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent / "phase3_rank"))
from rank_inverse import MODELS,N
from variable_rejection import recover_bounded,generate_trace
from test_variable_rejection import forced_first_rejection, forced_later_rejection

ROOT=Path(__file__).resolve().parent

def bench():
    cases=[
      ('marsaglia128','late_1',forced_later_rejection(14),65,100,0,1,None,None),
      ('marsaglia128','initial_1_identifiable_alias',forced_first_rejection(),65,100,0,1,None,None),
      ('marsaglia128','two_skips_stress',37,68,100,0,2,13124,None),
      ('xoroshiro128plus','no_rejection',0xabcdeeddfedcba987654321123456789,175,100,0,0,None,None),
    ]
    mask64=(1<<64)-1; first=0x123456789abcdef0; last=mask64-first
    cases.extend([
        ('xoroshiro128plus','forced_initial_reject_plus',first|(last<<64),170,100,0,1,None,1),
        ('xoshiro256plus','forced_initial_reject_plus',first|(0x7777777777777777<<64)|(0xfedcba9876543210<<128)|(last<<192),300,100,0,1,None,1),
    ])
    outputs=[]
    for name,label,seed,n,holdout,gap,max_skips,multiplier,min_skips in cases:
        model=MODELS[name]
        data,skips,_=generate_trace(model,seed,n+holdout,gap=gap,accept_multiple=multiplier)
        r=recover_bounded(model,data[:n],gap=gap,max_skips=max_skips,
                          accept_multiple=multiplier,minimum_skips=min_skips or 0)
        if r['status']!='SAT': raise AssertionError((label,r))
        witness=int(r['seed'],16)
        replay=generate_trace(model,witness,n+holdout,gap=gap,accept_multiple=multiplier)[0]
        continuation=sum(x==y for x,y in zip(replay[n:],data[n:]))
        if continuation!=holdout:raise AssertionError('held-out mismatch')
        outputs.append({'case':label,'model':name,'seed_planted_hex':f'0x{seed:0{model.size//4}x}',
                        'seed_recovered_hex':r['seed'],
                        'original_seed_equal':witness==seed,
                        'actual_training_skip_draws':[i for i,z in enumerate(skips[:n]) for _ in range(z)],
                        'predicted_skip_draws':r['recovered_path'],
                        'training_full_replay':r['exact_training_tickets'],
                        'heldout_full_replay':continuation,'recovery':r})
        print(name,label,r['status'],f'heldout={continuation}/{holdout}',
              f'seed_equal={witness==seed}',r['seconds'],'sec',flush=True)
    r32=((1<<32)%N)/(1<<32);r64=((1<<64)%N)/(1<<64)
    artifact={'version':'phase3b-v1','python':platform.python_version(),
         'platform':platform.platform(),'N':N,'rejection_probabilities_ideal_uniform_words':
            {'32bit':r32,'64bit':r64,'expected_rejected_32bit_over_3526':r32*3526,
             'probability_no_rejection_in_3526_independent_32bit_words':(1-r32)**3526},
         'cases':outputs, 'source_assumptions':'Uniform output-word probabilities only for probabilities. No deployed RNG attribution.',
         'original_seed_alias_warning':'A rejected first word permits a shifted initial state with identical accepted stream.'}
    (ROOT/'PHASE3B_RESULTS.json').write_text(json.dumps(artifact,indent=2)+'\n')
    return artifact
if __name__=='__main__':bench()
