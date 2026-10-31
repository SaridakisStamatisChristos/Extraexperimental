#!/usr/bin/env python3
"""Reproducible planted subspace recovery benchmark and negative tests.
The unknown generator state has 128 bits of storage but is explicitly limited
by initialization to the 64-bit linear subspace (x,y,0,0).
No oracle removal indices are provided to the inverse engine.
"""
import argparse,csv,hashlib,json,platform,subprocess,time
from pathlib import Path
# Source-independent Python oracle; do not reuse the solver recurrence.
def independent_transition(s):
    x,y,z,w=s
    mask=(1<<32)-1
    t=(x^((x<<11)&mask))&mask
    out=(w^(w>>19)^t^(t>>8))&mask
    return (y,z,w,out),out
ROOT=Path(__file__).resolve().parent
SEEDS=(0x123456789abcdef0,0x020456789abcdef0,0xa185aa00003918ca)

def ref_draw(state,gap,sampler):
    remaining=list(range(1,36));chosen=[]
    for i in range(5):
        state,word=independent_transition(state)
        n=len(remaining)
        k=word%n if sampler=='mod' else (word*n)>>32
        chosen.append(remaining.pop(k))
    for _ in range(gap):state,_=independent_transition(state)
    return state,tuple(sorted(chosen))

def generate(seed,gap,sampler,n):
    state=(seed&0xffffffff,seed>>32,0,0)
    for _ in range(n):
        state,t=ref_draw(state,gap,sampler)
        yield t

def write(path,tickets):
    with path.open('w',newline='') as f:
        w=csv.writer(f);w.writerow(['ticket_mask'])
        for x in tickets:w.writerow([sum(1<<(v-1) for v in x)])

def run(binary,data,train,gap,high,budget=300000000):
    t=time.perf_counter()
    p=subprocess.run([str(binary),str(data),str(train),str(gap),str(budget),'75',str(train),str(int(high))],text=True,capture_output=True,check=True)
    r=json.loads(p.stdout);r['process_wall_seconds']=time.perf_counter()-t
    return r

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',default=str(ROOT/'P2B_RESULTS.json'))
    parser.add_argument('--real',default=None)
    args=parser.parse_args()
    binary=ROOT/'inverse128_subspace'
    cases=[];train=500;heldout=100
    for seed in SEEDS:
        for sampler in ('mod','high'):
            for gap in (0,2):
                tickets=list(generate(seed,gap,sampler,train+heldout))
                p=ROOT/f'control_{seed:016x}_{sampler}_gap{gap}.csv'
                write(p,tickets[:train])
                result=run(binary,p,train,gap,sampler=='high')
                state=result['witness_state'];independent=list(generate(state,gap,sampler,train+heldout)) if result['status']=='SAT' else []
                holdout_matches=sum(a==b for a,b in zip(independent[train:],tickets[train:]))
                recovered=result['status']=='SAT' and state==seed
                cases.append({'seed_hex':hex(seed),'sampler':sampler,'gap':gap,
                              'status':result['status'],'rank':result['rank'],
                              'assignments':result['assignments_examined'],
                              'domain_product':result['selection_domain_product'],
                              'found_seed_hex':hex(state),'exact_seed_recovered':recovered,
                              'independent_holdout_correct':holdout_matches,
                              'heldout':heldout,'seconds':result['seconds']})
                print(f'{hex(seed)} {sampler} gap={gap}: {result["status"]} rank={result["rank"]} assignments={result["assignments_examined"]} holdout={holdout_matches}/{heldout} sec={result["seconds"]:.3f}',flush=True)
    data={'model':'Marsaglia xorshift128, with x,y unknown / z=w=0 subspace; 64 free bits','train':train,'holdout':heldout,
        'positive_controls':cases,'exact_recoveries':sum(x['exact_seed_recovered'] for x in cases),
        'independent_reserved_tickets':sum(x['independent_holdout_correct'] for x in cases),
        'software':{'python':platform.python_version(),'compiler':subprocess.run(['g++','--version'],capture_output=True,text=True).stdout.splitlines()[0]}}
    if args.real:
        real=[]
        for sampler in ('mod','high'):
            for gap in (0,1,2):
                r=run(binary,args.real,3526,gap,sampler=='high',budget=300000000)
                real.append({'sampler':sampler,'gap':gap,'status':r['status'],'rank':r['rank'],'assignments':r['assignments_examined'], 'domain_product':r['selection_domain_product'],'observed_rows':r['observed_training_rows'],'seconds':r['seconds']})
                print(f'real model={sampler} gap={gap}: {r["status"]}, rank={r["rank"]} branches={r["assignments_examined"]}',flush=True)
        data['real_sparse_results']=real
        data['real_sparse_sha256']=hashlib.sha256(Path(args.real).read_bytes()).hexdigest()
    Path(args.output).write_text(json.dumps(data,indent=2)+'\n')
    assert data['exact_recoveries']==len(cases),data['exact_recoveries']
    assert data['independent_reserved_tickets']==len(cases)*heldout
if __name__=='__main__': main()
