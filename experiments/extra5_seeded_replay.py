#!/usr/bin/env python3
"""Replay public synthetic seed hypotheses. NOT live Allwyn keys or prediction.
8 indices x 2 seed policies x (31 fixed + 2 switching) x 3 samplers.
Run from experiments/: python extra5_seeded_replay.py --seeds 8 --null-replicates 3000
"""
import argparse,csv,hashlib,json
from pathlib import Path
import numpy as np
from extra5_historical_engine import RoutedBits
from extra5_seed_switch_protocol import (SAMPLERS,DrawSpec,SeedInputs,demo_nr_key,
    derive_seed,sources_from_seed,sample_ticket,routes_supported)
P=Path(__file__).resolve().parent
D=b'EXTRA5-INDEPENDENT-SEED-SEARCH-v1|NOT-OPERATOR-SEEDS|'

class BudgetBits:
    def __init__(self,source): self.source,self.remaining=source,1024
    def bit(self):
        if not self.remaining: raise ValueError('sampler exhausted 1024-bit safety budget')
        self.remaining-=1
        return self.source.bit()

def ticket(ids,seed,policy,route,sampler,schedule,routes,key):
    tag=D+seed.to_bytes(4,'big');prev=None;pred=[]
    for j,id in enumerate(ids):
        coupons=b'UNVERIFIED-COUPONS/'+tag+b'/'+str(id).encode()
        if policy=='fresh_fixture':
            e1=hashlib.sha256(tag+b'/entropy1/'+str(id).encode()).digest()
            e2=hashlib.sha256(tag+b'/entropy2/'+str(id).encode()).digest()
            inputs=SeedInputs(samples=(e1,e2))
        else:
            if prev is None:prev=hashlib.sha256(tag+b'/initial-state').digest()
            inputs=SeedInputs(previous_state=prev)
        if schedule=='fixed': chosen=route
        elif schedule=='round_robin':chosen=routes[(j+seed)%31]
        else:
            s=D+b'SWITCH/'+seed.to_bytes(4,'big')+j.to_bytes(4,'big')
            chosen=routes[int.from_bytes(hashlib.sha256(s).digest()[:4],'big')%31]
        spec=DrawSpec(id,coupons,inputs,chosen,sampler)
        tr=derive_seed(id,coupons,inputs,key)
        stream=BudgetBits(RoutedBits(sources_from_seed(tr.master),chosen,spec.block_bits))
        pred.append(sample_ticket(stream,sampler))
        if policy=='previous_state_fixture':
            prev=hashlib.sha256(D+b'NEXT-STATE'+inputs.previous_state+tr.master+id.to_bytes(8,'big')).digest()
    return pred

def mask(seq):return sum(1<<(v-1) for v in seq)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--seeds',type=int,default=8)
    ap.add_argument('--null-replicates',type=int,default=3000)
    ap.add_argument('--out',type=Path,default=P)
    a=ap.parse_args();a.out.mkdir(exist_ok=True,parents=True)
    rows=list(csv.DictReader(open(P/'extra5_last100_data.csv',newline='')))
    ids=[int(r['draw_id']) for r in rows]
    assert ids==list(range(14256,14356))
    actual=[tuple(int(r[f'n{i}']) for i in range(1,6)) for r in rows]
    assert all(len(set(t))==5 and all(1<=v<=35 for v in t) for t in actual)
    true=np.array([mask(t) for t in actual],dtype=np.uint64)
    routes=routes_supported()
    plans=[('fixed',r) for r in routes]+[('round_robin',routes[0]),('hash_switch',routes[0])]
    good=[];bad=[];masks=[]
    for seed in range(a.seeds):
        for policy in ('fresh_fixture','previous_state_fixture'):
            for schedule,route in plans:
                for sampler in SAMPLERS:
                    cfg=dict(seed_index=seed,seed_policy=policy,schedule=schedule,
                        operation=route.operation,sources='-'.join(route.names) if schedule=='fixed' else 'dynamic-31',sampler=sampler)
                    try:
                        pred=ticket(ids,seed,policy,route,sampler,schedule,routes,demo_nr_key())
                    except (ValueError,RuntimeError,EOFError) as e:
                        bad.append({**cfg,'error':str(e)});continue
                    m=np.array([mask(t) for t in pred],dtype=np.uint64)
                    hits=np.bitwise_count(true&m)
                    good.append({**cfg,'train_hits_80':int(hits[:80].sum()),
                        'holdout_hits_20':int(hits[80:].sum()),
                        'train_exact':int((hits[:80]==5).sum()),
                        'holdout_exact':int((hits[80:]==5).sum()),
                        'holdout_three_plus':int((hits[80:]>=3).sum()),
                        'last20':'|'.join('-'.join(map(str,t)) for t in pred[80:])})
                    masks.append(m[80:])
    assert len(good)+len(bad)==a.seeds*2*33*3
    k=lambda r:(r['seed_index'],r['seed_policy'],r['schedule'],r['operation'],r['sources'],r['sampler'])
    winner=sorted(good,key=lambda r:(-r['train_hits_80'],k(r)))[0]
    hindsight=sorted(good,key=lambda r:(-r['holdout_hits_20'],k(r)))[0]
    exceed=0;maxes=[]
    if a.null_replicates:
        rng=np.random.default_rng(20261029);models=np.array(masks,dtype=np.uint64)
        for start in range(0,a.null_replicates,60):
            b=min(60,a.null_replicates-start)
            picks=np.argpartition(rng.random((b,20,35)),5,axis=2)[:,:,:5]
            fair=np.bitwise_or.reduce(np.left_shift(np.uint64(1),picks.astype(np.uint64)),axis=2)
            maxima=np.bitwise_count(models[None,:,:]&fair[:,None,:]).sum(axis=2).max(axis=1)
            exceed+=int((maxima>=hindsight['holdout_hits_20']).sum())
            maxes.extend(map(int,maxima))
    summary={'historical_ids':[14256,14355],'training_ids':[14256,14335],
       'pseudo_holdout_ids':[14336,14355], 'seed_domain':D.decode(),
       'seeds':a.seeds,'attempted':len(good)+len(bad),'completed':len(good),
       'failures':bad, 'best_training_selected':winner,
       'best_posthoc_holdout':hindsight,'holdout_expected_hits':20*25/35,
       'exact_holdout_models':sum(x['holdout_exact']>0 for x in good),
       'null_replicates':a.null_replicates,'null_exceed':exceed,
       'p_posthoc_max_plus_one':(exceed+1)/(a.null_replicates+1) if a.null_replicates else None,
       'null_max_mean':float(np.mean(maxes)) if maxes else None,
       'note':'Synthetic public seeds, toy group keys, hypothetical sampler/switching, no production seed or prediction.'}
    (a.out/'extra5_seeded_replay_results.json').write_text(json.dumps(summary,indent=2)+'\n')
    with (a.out/'extra5_seeded_replay_scores.csv').open('w',newline='') as f:
        cols=[x for x in good[0] if x!='last20'];w=csv.DictWriter(f,fieldnames=cols)
        w.writeheader();w.writerows({k:r[k] for k in cols} for r in good)
    print(json.dumps({k:v for k,v in summary.items() if k not in ('failures','best_training_selected','best_posthoc_holdout')},indent=2))
    print('train chosen:',{k:v for k,v in winner.items() if k!='last20'})
    print('posthoc chosen:',{k:v for k,v in hindsight.items() if k!='last20'})
if __name__=='__main__':main()
