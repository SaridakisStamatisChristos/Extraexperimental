#!/usr/bin/env python3
"""Expanded *synthetic* seed sweep for the historic-family EXTRA 5 reconstruction.

No operator secrets are known. Fit to past results cannot identify a secret seed.
For reproducibility, sweep consecutive seed indices and preserve the entire set
of scored models, failures, null simulation settings and generated commands.

The per-draw NR seed is cached across routes and samplers, and samplers share
an identical memoized prefix of the generated bits. The memoized source is
rewound to bit index zero for each independent sampler hypothesis.
"""
from __future__ import annotations
import argparse, csv, hashlib, json, math, platform, time
from dataclasses import dataclass
from pathlib import Path
import numpy as np
from scipy.stats import hypergeom
from extra5_historical_engine import RoutedBits
from extra5_seed_switch_protocol import SAMPLERS, SeedInputs, demo_nr_key, derive_seed, sources_from_seed, sample_ticket, routes_supported
from extra5_seeded_replay import D, mask

P = Path(__file__).resolve().parent
BIT_BUDGET = 1024

@dataclass
class MemoBitStream:
    source: object
    cache: list[int]
    at: int = 0
    limit: int = BIT_BUDGET

    def bit(self):
        if self.at == self.limit:
            raise ValueError(f'sampler exhausted {self.limit}-bit safety budget')
        if self.at == len(self.cache):
            self.cache.append(self.source.bit())
        value = self.cache[self.at]
        self.at += 1
        return value

    def rewind(self):
        self.at = 0


def seeded_masters(ids, seed, policy, key):
    tag = D + seed.to_bytes(4, 'big')
    prev = None
    for did in ids:
        coupons = b'UNVERIFIED-COUPONS/' + tag + b'/' + str(did).encode()
        if policy == 'fresh_fixture':
            e1 = hashlib.sha256(tag+b'/entropy1/'+str(did).encode()).digest()
            e2 = hashlib.sha256(tag+b'/entropy2/'+str(did).encode()).digest()
            inputs = SeedInputs(samples=(e1,e2))
        else:
            if prev is None:
                prev = hashlib.sha256(tag+b'/initial-state').digest()
            inputs = SeedInputs(previous_state=prev)
        master = derive_seed(did, coupons, inputs, key).master
        yield master
        if policy == 'previous_state_fixture':
            prev = hashlib.sha256(D+b'NEXT-STATE'+inputs.previous_state+master+did.to_bytes(8,'big')).digest()


def chosen_route(routes, seed, index, schedule, base):
    if schedule == 'fixed':
        return base
    if schedule == 'round_robin':
        return routes[(index+seed)%31]
    if schedule == 'hash_switch':
        s = D+b'SWITCH/'+seed.to_bytes(4,'big')+index.to_bytes(4,'big')
        return routes[int.from_bytes(hashlib.sha256(s).digest()[:4],'big')%31]
    raise ValueError(schedule)


def fixed_configs():
    routes=routes_supported()
    return routes, [('fixed',route) for route in routes] + [
        ('round_robin',routes[0]), ('hash_switch',routes[0])]


def exact_holdout_tail(k,draws=20):
    pmf = hypergeom.pmf(np.arange(6),35,5,5)
    distribution = np.array([1.0])
    for _ in range(draws):
        distribution=np.convolve(distribution,pmf)
    return float(sum(distribution[k:]))


def run(seed_start=0,seed_stop=64,null_replicates=2000,out=P,progress=True):
    if not 0<=seed_start<seed_stop<=2**32:
        raise ValueError('seed bounds must be in uint32 range, and start < stop')
    out.mkdir(parents=True, exist_ok=True)
    records=list(csv.DictReader((P/'extra5_last100_data.csv').open(newline='')))
    ids=[int(row['draw_id']) for row in records]
    if ids!=list(range(14256,14356)):
        raise ValueError('expected original consecutive draw IDs 14256..14355')
    actual=[tuple(int(row[f'n{i}']) for i in range(1,6)) for row in records]
    if not all(len(set(t))==5 and all(1<=n<=35 for n in t) for t in actual):
        raise ValueError('dataset contains invalid ticket')
    true=np.array([mask(t) for t in actual],dtype=np.uint64)
    allroutes,plans=fixed_configs();nrkey=demo_nr_key()
    candidates=[]
    failures=[]
    predicted_masks=[]
    start=time.monotonic()
    for seed in range(seed_start,seed_stop):
        for policy in ('fresh_fixture','previous_state_fixture'):
            masters=list(seeded_masters(ids,seed,policy,nrkey))
            # route predictions: three samplers on one identical prefix per draw
            for schedule,base in plans:
                cfgbase={'seed_index':seed,'seed_policy':policy,'schedule':schedule,
                        'operation':base.operation,'sources':'-'.join(base.names) if schedule=='fixed' else 'dynamic-31'}
                sequences=[[] for _ in SAMPLERS]
                errors=[None for _ in SAMPLERS]
                for j, master in enumerate(masters):
                    if all(error is not None for error in errors):
                        break
                    route=chosen_route(allroutes,seed,j,schedule,base)
                    stream=MemoBitStream(RoutedBits(sources_from_seed(master),route,256),[])
                    for ix,sampler in enumerate(SAMPLERS):
                        if errors[ix] is not None:
                            continue
                        stream.rewind()
                        try:
                            t=sample_ticket(stream,sampler)
                            sequences[ix].append(t)
                        except (ValueError,RuntimeError,EOFError) as e:
                            errors[ix]=str(e)
                for ix,sampler in enumerate(SAMPLERS):
                    cfg=dict(**cfgbase,sampler=sampler)
                    if errors[ix] is not None:
                        failures.append({**cfg,'error':errors[ix]})
                        continue
                    if len(sequences[ix])!=100:
                        raise AssertionError('incomplete prediction without error')
                    seq=sequences[ix]
                    masks=np.array([mask(t) for t in seq],dtype=np.uint64)
                    hits=np.bitwise_count(true & masks)
                    candidates.append({**cfg,'train_hits_80':int(hits[:80].sum()),
                                       'holdout_hits_20':int(hits[80:].sum()),
                                       'train_exact':int(np.count_nonzero(hits[:80]==5)),
                                       'holdout_exact':int(np.count_nonzero(hits[80:]==5)),
                                       'holdout_three_plus':int(np.count_nonzero(hits[80:]>=3))})
                    predicted_masks.append(masks[80:])
        if progress and ((seed-seed_start+1)%8==0 or seed==seed_stop-1):
            print(f'seed {seed} complete: {len(candidates)} valid, {len(failures)} rejected, {time.monotonic()-start:.1f}s elapsed',flush=True)

    if len(candidates)+len(failures)!=(seed_stop-seed_start)*2*len(plans)*len(SAMPLERS):
        raise AssertionError('candidate count mismatch')
    def tie_key(r):
        return r['seed_index'],r['seed_policy'],r['schedule'],r['operation'],r['sources'],r['sampler']
    selected=min(candidates,key=lambda r:(-r['train_hits_80'],tie_key(r)))
    hindsight=min(candidates,key=lambda r:(-r['holdout_hits_20'],tie_key(r)))
    exceed=0; null_maxes=[]
    if null_replicates:
        rng=np.random.default_rng(20261029)
        models=np.stack(predicted_masks).astype(np.uint64)
        # Fixed candidate predictions. Null histories generated independently, then max over ALL searched models.
        for off in range(0,null_replicates,12):
            batch=min(12,null_replicates-off)
            picks=np.argpartition(rng.random((batch,20,35)),5,axis=2)[:,:,:5]
            fair=np.bitwise_or.reduce(np.left_shift(np.uint64(1),picks.astype(np.uint64)),axis=2)
            mx=np.bitwise_count(models[None,:,:]&fair[:,None,:]).sum(axis=2).max(axis=1)
            exceed+=int(np.count_nonzero(mx>=hindsight['holdout_hits_20']))
            null_maxes.extend(map(int,mx))
    fieldnames=list(candidates[0])
    score_path=out/'extra5_seed_sweep_scores.csv'
    with score_path.open('w',newline='',encoding='utf8') as fd:
        writer=csv.DictWriter(fd,fieldnames=fieldnames);writer.writeheader();writer.writerows(candidates)
    scores_hash=hashlib.sha256(score_path.read_bytes()).hexdigest()
    result={
        'research_scope':'retrospective synthetic seed search, NOT production seed recovery',
        'data_source':'experiments/extra5_last100_data.csv',
        'draw_id_range':[14256,14355], 'train_draws':80,'pseudo_holdout_draws':20,
        'seed_domain':D.decode('ascii'),'seed_start_inclusive':seed_start,'seed_stop_exclusive':seed_stop,
        'attempts':len(candidates)+len(failures),'completed':len(candidates),'failures':len(failures),
        'failure_reasons':dict((m,sum(x['error']==m for x in failures)) for m in sorted(set(x['error'] for x in failures))),
        'sample_failures':failures[:10],
        'schedules':['fixed','round_robin','hash_switch'],'routes_fixed':31,
        'samplers':list(SAMPLERS),'seed_policies':['fresh_fixture','previous_state_fixture'],
        'best_train_selected':selected,'best_holdout_posthoc':hindsight,
        'models_with_any_exact_ticket_on_holdout':sum(x['holdout_exact']>0 for x in candidates),
        'total_exact_tickets_on_holdout':sum(x['holdout_exact'] for x in candidates),
        'expected_exact_tickets_under_iid_null':len(candidates)*20/324632,
        'null_fixed_holdout_expected_individual_matches':20*25/35,
        'train_selected_fixed_model_holdout_upper_tail_p':exact_holdout_tail(selected['holdout_hits_20']),
        'posthoc_model_uncorrected_upper_tail_p':exact_holdout_tail(hindsight['holdout_hits_20']),
        'null_calibration':{'replicates':null_replicates,'generator':'numpy PCG64 seed 20261029','max_score_exceedances':exceed,
            'familywise_plus_one_p':(exceed+1)/(null_replicates+1) if null_replicates else None,
            'mean_null_max':float(np.mean(null_maxes)) if null_maxes else None},
        'scores_csv_sha256':scores_hash,
        'execution':{'elapsed_seconds':round(time.monotonic()-start,2),'python':platform.python_version(), 'numpy':np.__version__},
        'interpretation':'Synthetic seeds do not recover secret physical entropy, coupons, keys, algorithm choices, or future draws. Best-of-thousands overlaps require search correction.'
    }
    (out/'extra5_seed_sweep_results.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    if progress:
        print(json.dumps({k:v for k,v in result.items() if k not in ('sample_failures','best_train_selected','best_holdout_posthoc')},indent=2))
        print('SELECTED:',selected,'POSTHOC:',hindsight)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--seed-start',type=int,default=0)
    ap.add_argument('--seed-stop',type=int,default=64)
    ap.add_argument('--null-replicates',type=int,default=2000)
    ap.add_argument('--out',type=Path,default=P)
    args=ap.parse_args()
    run(args.seed_start,args.seed_stop,args.null_replicates,args.out)
