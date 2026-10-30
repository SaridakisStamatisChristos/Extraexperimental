#!/usr/bin/env python3
import json,subprocess,concurrent.futures,time
from pathlib import Path
from sweep import choose,EXE,REAL
BASE=Path(__file__).resolve().parent
multipliers=[0x9E3779BB,0x85EBCA6B,0x2545F491]
trials=[(*shift,stride,mult) for shift in choose() for stride in range(5,11) for mult in multipliers]
def trial(t):
    a,b,c,stride,mult=t
    try:
        cp=subprocess.run([str(EXE),str(REAL),str(a),str(b),str(c),str(stride),'12','3526',str(mult)],capture_output=True,text=True,timeout=12,check=True)
        return json.loads(cp.stdout)
    except Exception as e:return {'family':f'xorshift32_{a}_{b}_{c}','stride':stride,'multiplier':mult,'exhaustive':False,'error':str(e)[:160]}
start=time.monotonic();results=[]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    for i,r in enumerate(pool.map(trial,trials),1):
        results.append(r)
        if i%200==0:print('progress',i,'/',len(trials),'elapsed',round(time.monotonic()-start,2),flush=True)
summary={'trials':len(trials),'exhaustive':sum(r.get('exhaustive',False) for r in results),
         'eliminated':sum(r.get('exhaustive',False) and r.get('states_matching_all_tickets',0)==0 for r in results),
         'incomplete':sum(not r.get('exhaustive',False) for r in results),
         'any_first':sum(r.get('states_matching_first_ticket',0)>0 for r in results),
         'any_two_in_filtered':sum(r.get('states_matching_first_two',0)>0 for r in results),
         'total_state_candidates':sum(r.get('states_full_rank',0) for r in results),
         'time_sec':round(time.monotonic()-start,3)}
(BASE/'star_sweep_results.json').write_text(json.dumps({'summary':summary,'results':results},indent=2)+'\n')
print('FINAL',json.dumps(summary),flush=True)
