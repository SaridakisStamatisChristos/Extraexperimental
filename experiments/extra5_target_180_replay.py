#!/usr/bin/env python3
"""Independent slow replay of synthetic historical seed candidates on 60/40 split.

All forty validation draws were already public at analysis time. Historical fit
is not prospective prediction; original operator seeds/keys remain unavailable.
"""
import argparse, csv, json, hashlib
from pathlib import Path
from extra5_seeded_replay import ticket,mask
from extra5_seed_switch_protocol import SAMPLERS,routes_supported,demo_nr_key

P=Path(__file__).resolve().parent

def evaluate(start=0,stop=128,out=P):
    assert 0<=start<stop<=128
    with (P/'extra5_last100_data.csv').open(newline='') as f:
        data=list(csv.DictReader(f))
    ids=[int(x['draw_id']) for x in data]
    assert ids==list(range(14256,14356))
    actual=[sum(1<<(int(x[f'n{i}'])-1) for i in range(1,6)) for x in data]
    routes=routes_supported();key=demo_nr_key()
    plans=[('fixed',r) for r in routes]+[('round_robin',routes[0]),('hash_switch',routes[0])]
    results=[]; failures=[]
    for seed in range(start,stop):
        for policy in ('fresh_fixture','previous_state_fixture'):
            for schedule,route in plans:
                for sampler in SAMPLERS:
                    cfg=dict(seed_index=seed,seed_policy=policy,schedule=schedule,
                        operation=route.operation,
                        sources='-'.join(route.names) if schedule=='fixed' else 'dynamic-31',
                        sampler=sampler)
                    try:
                        predicted=ticket(ids,seed,policy,route,sampler,schedule,routes,key)
                        hits=[(x & mask(t)).bit_count() for x,t in zip(actual,predicted)]
                    except (ValueError,RuntimeError,EOFError) as error:
                        failures.append({**cfg,'error':str(error)});continue
                    results.append({**cfg,'train_hits_60':sum(hits[:60]),
                        'holdout_hits_40':sum(hits[60:]),
                        'train_hits_80':sum(hits[:80]),
                        'holdout_hits_20':sum(hits[80:]),
                        'exact_holdout_40':sum(k==5 for k in hits[60:]),
                        'hits_4plus_holdout_40':sum(k>=4 for k in hits[60:])})
    assert len(results)+len(failures)==(stop-start)*198
    out.mkdir(parents=True,exist_ok=True)
    dest=out/'extra5_target_180_replay_scores.csv'
    with dest.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    print(json.dumps({'seeds':[start,stop],'completed':len(results),'failed':len(failures),
        'max40':max(x['holdout_hits_40'] for x in results),
        'max_train60':max(x['train_hits_60'] for x in results),
        'outputs_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()},indent=2))
    return results

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed-start',type=int,default=0)
    ap.add_argument('--seed-stop',type=int,default=128)
    ap.add_argument('--out',type=Path,default=P)
    args=ap.parse_args()
    evaluate(args.seed_start,args.seed_stop,args.out)
