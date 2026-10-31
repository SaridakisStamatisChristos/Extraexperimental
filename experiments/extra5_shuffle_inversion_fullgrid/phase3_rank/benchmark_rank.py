#!/usr/bin/env python3
"""Fully reproducible planted controls; excludes preprocessing from solve timing only when separately labelled."""
import json,platform,sys,time
from pathlib import Path
from rank_inverse import MODELS,generate,recover

SEEDS={
 128:(1,0x123456789abcdef0fedcba9876543210,0x99887766554433221100ffeeddccbbaa),
 256:(1,int('123456789abcdef0fedcba9876543210cafebabedeadbeef0123456789abcdef',16),
      int('a185aa00003918cafedcba98765432100112233445566778899aabbccddeeff',16)),
}
train={128:200,256:335}
results=[]
start=time.perf_counter()
for name,model in MODELS.items():
 for gap in (0,2):
  for seed in SEEDS[model.size]:
   dataset=list(generate(model,seed,train[model.size]+100,gap))
   t=time.perf_counter(); result=recover(model,dataset[:train[model.size]],gap);elapsed=time.perf_counter()-t
   recovered=int(result['recovered_seed'],16) if result['status']=='SAT' else None
   replay=(list(generate(model,recovered,len(dataset),gap))==dataset) if recovered is not None else False
   result.update(planted=f'0x{seed:0{model.size//4}x}',exact_state=recovered==seed,
                 full_train_and_heldout_replay=replay,heldout_tickets=100,
                 measured_end_to_end_recover_seconds=round(elapsed,6))
   results.append(result)
   print(name,'gap',gap,'state',f'{seed:x}'[-10:],'status',result['status'],
         'rank',result['linear_rank'],'replay',replay,'sec',round(elapsed,3),flush=True)
assert len(results)==18 and all(r['status']=='SAT' and r['exact_state'] and r['full_train_and_heldout_replay'] for r in results)
out={'experiment':'phase3_single_word_combination_rank_modulo','date':'2026-10-31',
     'python_version':sys.version.split()[0], 'platform':platform.platform(),
     'time_total_seconds':round(time.perf_counter()-start,4),
     'number_of_planted_recoveries':len(results),
     'heldout_full_tickets_matched':sum(r['heldout_tickets'] for r in results),
     'important_assumption':'one accepted full 32/64-bit word per ticket, modulo combination count, continuous state, fixed gap, no rejection',
     'results':results}
Path(__file__).with_name('RANK_RESULTS.json').write_text(json.dumps(out,indent=2)+'\n')
print('total',out['time_total_seconds'])
