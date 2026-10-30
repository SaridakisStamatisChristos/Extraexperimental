#!/usr/bin/env python3
from sweep import trial
import argparse,itertools,concurrent.futures,json,time
from pathlib import Path
ap=argparse.ArgumentParser()
ap.add_argument('--max-shift',type=int,default=12)
ap.add_argument('--a-min',type=int,default=1)
ap.add_argument('--a-max',type=int,default=12)
ap.add_argument('--jobs',type=int,default=8)
ap.add_argument('--strides',nargs='+',type=int,default=[5,6,7,8])
ap.add_argument('--prefix',type=int,default=12)
a=ap.parse_args()
trials=[(i,j,k,stride,a.prefix) for i,j,k,stride in itertools.product(range(a.a_min,a.a_max+1),range(1,a.max_shift+1),range(1,a.max_shift+1),a.strides)]
results=[];begin=time.monotonic()
with concurrent.futures.ThreadPoolExecutor(max_workers=a.jobs) as p:
    for idx,r in enumerate(p.map(trial,trials),1):
        results.append(r)
        if idx%300==0:print(f'PROGRESS {idx}/{len(trials)} elapsed {time.monotonic()-begin:.1f} s',flush=True)
summary={'max_shift':a.max_shift,'a_range':[a.a_min,a.a_max],'strides':a.strides,'prefix':a.prefix,'total':len(trials),
         'complete':sum(r.get('exhaustive',False) for r in results),
         'eliminated':sum(r.get('exhaustive',False) and r.get('states_matching_first_two',0)==0 for r in results),
         'incomplete':sum(not r.get('exhaustive',False) for r in results),
         'models_matching_two':[(r['family'],r['stride'],r.get('states_matching_first_two')) for r in results if r.get('states_matching_first_two',0)>0],
         'states_matching_first_only':sum(r.get('states_matching_first_ticket',0) for r in results),
         'time_sec':round(time.monotonic()-begin,2)}
q=Path(__file__).parent
(q/f'grid_results_{a.a_min}_{a.a_max}.json').write_text(json.dumps({'summary':summary,'results':results},indent=2)+'\n')
print('FINAL',json.dumps(summary),flush=True)
