#!/usr/bin/env python3
"""Deterministic planted synthetic research benchmark; no real lottery draws in fixture generation."""
import json,platform,time,sys,hashlib
from pathlib import Path
from affine import census
from recover_affine import recover
from test_affine_inversion import oracle_tickets
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from inverse_linear import MODELS

def main():
    t=time.perf_counter();counts,_,_=census()
    seeds=[0x8877665544332211ffeeddccbbaa9988,
           0x13579bdf2468ace0011223344556677889abcdef01234567fedcba9876543210]
    results=[]
    for name,m in MODELS.items():
        for sampler in ('mod','high'):
            for gap in (0,2):
                for seed in seeds:
                    seed%=1<<m.size
                    fixtures=oracle_tickets(m,seed,1100,gap,sampler)
                    r=recover(fixtures[:1000],m,gap,sampler)
                    witness=int(r.get('recovered_seed','0'),16)
                    holdout_correct=0
                    if r['status']=='SAT':
                        replay=oracle_tickets(m,witness,1100,gap,sampler)
                        holdout_correct=sum(a==b for a,b in zip(fixtures[1000:],replay[1000:]))
                    results.append(dict(model=name,sampler=sampler,gap=gap,planted_seed_hex=hex(seed),
                       status=r['status'],rank=r['rank'],state_bits=m.size,
                       linear_equations=r['total_parity_equations'],
                       full_state_equal=witness==seed,heldout_tickets=100,
                       independently_replayed_heldout=holdout_correct,elapsed_s=r['seconds']))
                    assert r['status']=='SAT' and r['rank']==m.size and witness==seed and holdout_correct==100,r
    out={'research_scope':'unrestricted 128-/256-bit linear state inversion from unordered 5/35 sets',
       'generator_note':'xoroshiro128_raw and xoshiro256_raw use diagnostic UNSCRAMBLED linear output projections',
       'python':platform.python_version(),'os':platform.platform(),
       'combination_census':{str(k):counts[k] for k in range(5)},
       'positive_cases':len(results),'positive_exact_states':sum(x['full_state_equal'] for x in results),
       'heldout_full_sets_replayed':sum(x['independently_replayed_heldout'] for x in results),
       'heldout_total':sum(x['heldout_tickets'] for x in results),
       'wall_seconds':time.perf_counter()-t,'cases':results,
       'real_data_status':'independent JavaScript connector validation for six Marsaglia models; Python canonical-data replay not available in isolated container'}
    p=Path(__file__).with_name('AFFINE_RESULTS.json');p.write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k!='cases'},indent=2))
if __name__=='__main__':main()
