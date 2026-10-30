#!/usr/bin/env python3
"""Run a bounded deterministic family sweep of the complete shuffle-invariant state solver.
A trial is called eliminated only if exhaustive and has zero whole-ticket states.
"""
import argparse,concurrent.futures,hashlib,json,subprocess,time,random
from pathlib import Path
BASE=Path(__file__).resolve().parent
EXE=BASE/'unordered_attack'
REAL=BASE/'real_unordered.csv'
KNOWN=[(13,17,5),(5,17,13),(7,9,13),(3,7,11),(13,7,17),(11,8,19),(15,4,21),(1,3,10),(16,5,1),(1,17,5)]
def choose():
    rng=random.Random(20261030)
    extra=set()
    while len(extra)<40:
        x=tuple(rng.randrange(1,32) for _ in range(3))
        if x not in KNOWN:extra.add(x)
    return KNOWN+sorted(extra)

def trial(args):
    a,b,c,stride,n=args
    t0=time.monotonic()
    try:
        cp=subprocess.run([str(EXE),str(REAL),str(a),str(b),str(c),str(stride),str(n),'3526'],capture_output=True,text=True,timeout=15,check=True)
        result=json.loads(cp.stdout)
        result['elapsed']=round(time.monotonic()-t0,4)
        return result
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError,ValueError) as e:
        return {'family':f'xorshift32_{a}_{b}_{c}','stride':stride,'prefix':n,'exhaustive':False,'error':str(e)[:150]}

def main():
    p=argparse.ArgumentParser();p.add_argument('--jobs',type=int,default=6);p.add_argument('--out',default=str(BASE/'sweep_results.json'));p.add_argument('--prefix',type=int,default=12)
    p.add_argument('--maxshift-triples',type=int,default=50);p.add_argument('--strides',type=int,nargs='+',default=[5,6,7,8,9,10])
    x=p.parse_args()
    trials=[(*sh,st,x.prefix) for sh in choose()[:x.maxshift_triples] for st in x.strides]
    t0=time.monotonic();out=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=x.jobs) as pool:
        for idx,res in enumerate(pool.map(trial,trials),1):
            out.append(res)
            if idx%50==0:print('trials',idx,'/',len(trials),'complete', 'elapsed',round(time.monotonic()-t0,2),'seconds',flush=True)
    report={'method':'exhaustive_32bit_GF2_disjunctions_full_ticket_verification',
            'definition':'32bit left-right-left xorshift, fixed 5-output without-replacement modulo sampler, fixed gap, unknown independent shuffle',
            'trials':len(trials),'exhaustive':sum(r.get('exhaustive',False) for r in out),
            'no_exact_state':sum(r.get('exhaustive') and r.get('states_matching_all_tickets')==0 for r in out),
            'underconstrained':sum(not r.get('exhaustive',False) for r in out),
            'any_first_ticket':sum((r.get('states_matching_first_ticket',0)>0) for r in out),
            'any_two_tickets':sum((r.get('states_matching_first_two',0)>0) for r in out),
            'found':[(r['family'],r['stride'],r['recovered_states']) for r in out if r.get('states_matching_all_tickets',0)>0],
            'elapsed_seconds':round(time.monotonic()-t0,3),'outcomes':out}
    Path(x.out).write_text(json.dumps(report,indent=2)+'\n')
    print('FINAL',json.dumps({k:v for k,v in report.items() if k!='outcomes'}),flush=True)

if __name__=='__main__':main()
