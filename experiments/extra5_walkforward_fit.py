#!/usr/bin/env python3
"""Fit historical EXTRA 5 sequences without look-ahead; preregister 2-step forecast.

Historical data end at draw 14355 (2026-10-28 19:00). Forecast draw 14357
(2026-10-29 19:00) without looking at draw 14356, which is not in our file.

Assumptions: independent lottery null, outputs are unordered five-subsets of 35.
Models are exploratory inference baselines, not Allwyn RNG reverse engineering.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import platform
import numpy as np
from scipy.stats import hypergeom
from sklearn.linear_model import Ridge

HERE = Path(__file__).resolve().parent
DATA_DEFAULT = HERE / 'extra5_last100_data.csv'
P0 = 5/35
DOMAIN = b'EXTRA5-PRECOMMIT-2026-10-29-TWO-AHEAD-V1'


def load_data(path: Path):
    with path.open(newline='', encoding='utf-8-sig') as handle:
        records = list(csv.DictReader(handle))
    ids = [int(r['draw_id']) for r in records]
    if len(ids) != 100 or ids != list(range(14256,14356)):
        raise ValueError('Expected exactly consecutive IDs 14256..14355')
    X = np.zeros((len(records),35), dtype=float)
    for i, r in enumerate(records):
        nums = [int(r[f'n{j}']) for j in range(1,6)]
        if len(set(nums)) != 5 or not all(1 <= x <= 35 for x in nums):
            raise ValueError(f'Bad ticket {ids[i]}')
        X[i, np.array(nums)-1] = 1
    return ids, X


def normalized_inclusions(p):
    p = np.maximum(np.asarray(p, dtype=float), 0.00001)
    # Bounded logit-independent correction to make marginals sum to exactly 5.
    lo, hi = 0.0, 2_000_000.0
    for _ in range(48):
        mid = (lo + hi)/2
        if np.minimum(1.,p*mid).sum() >= 5: hi = mid
        else: lo = mid
    out = np.minimum(1.,p*hi)
    assert abs(out.sum() - 5) < 1e-7, out.sum()
    return out


def predict(X, name, horizon=2):
    n = len(X)
    assert n > horizon + 10
    p_base = (X.sum(axis=0) + 35*P0)/(n+35)
    if name == 'uniform':
        return np.full(35, P0)
    if name == 'frequency':
        return normalized_inclusions(p_base)
    if name.startswith('exp_'):
        half = float(name.split('_')[1])
        w = 0.5**(np.arange(n-1,-1,-1)/half)
        # Sample strength 10 prior draws, shrink to uniform rather than recent fit.
        return normalized_inclusions((w@X + 10*P0)/(w.sum()+10))
    if name == 'cold':
        return normalized_inclusions(np.maximum(0.02,2*P0-p_base))
    if name.startswith('markov_'):
        shrink = float(name.split('_')[1])
        last = X[-1]
        sources = X[:-horizon]
        targets = X[horizon:]
        a = sources.T@targets
        counts = sources.sum(axis=0)
        conditional = (a + shrink*p_base) / (counts[:,None] + shrink)
        return normalized_inclusions(np.mean(conditional[last>0],axis=0))
    if name.startswith('neighbor_'):
        k = int(name.split('_')[1])
        source=X[:-horizon]
        successors=X[horizon:]
        # Top k historical analogs in the same lag-h prediction task.
        scores = source@X[-1]
        inds = np.argsort(-scores,kind='stable')[:min(k,len(scores))]
        w = np.maximum(0.2,scores[inds])
        return normalized_inclusions((w@successors[inds] + 12*p_base)/(w.sum()+12))
    if name.startswith('ridge_'):
        alpha = float(name.split('_')[1])
        source=X[:-horizon]
        targets=X[horizon:]
        model=Ridge(alpha=alpha, fit_intercept=True)
        model.fit(source,targets)
        raw=model.predict(X[-1].reshape(1,-1))[0]
        return normalized_inclusions(0.45*np.clip(raw,0.005,0.95)+0.55*p_base)
    raise ValueError(name)

MODELS=('uniform','frequency','exp_5','exp_20','exp_60','cold','markov_10','markov_30','neighbor_5','neighbor_15','ridge_20','ridge_80')


def top_ticket(p):
    return tuple(sorted((np.argsort(-p,kind='stable')[:5]+1).tolist()))


def holdout_rows(X, horizon, first=60):
    # Each target t is forecast from X[0:n] with n=t-horizon+1.
    # For horizon 2, t=60 uses data up to 58, but not 59 or 60.
    bymodel={n:[] for n in MODELS}
    for t in range(30,len(X)):
        n=t-horizon+1
        if n < 20: continue
        for model in MODELS:
            p=predict(X[:n],model,horizon)
            hits=int(X[t,np.array(top_ticket(p))-1].sum())
            brier=float(np.sum((p-X[t])**2))
            row={'target_index':t,'prefix_count':n,'hits':hits,'brier':brier,
                 'ticket':top_ticket(p)}
            bymodel[model].append(row)
    tune={}
    test={}
    for model, rs in bymodel.items():
        early=[r for r in rs if r['target_index'] < first]
        late=[r for r in rs if r['target_index'] >= first]
        tune[model]={'draws':len(early),'hits':sum(r['hits'] for r in early),
                     'brier_mean':float(np.mean([r['brier'] for r in early]))}
        test[model]={'draws':len(late),'hits':sum(r['hits'] for r in late),
                     'brier_mean':float(np.mean([r['brier'] for r in late]))}
    # The actual model is selected ONLY using the early validation period.
    # Uniform excluded from tuning; maintained as an invariant baseline.
    chosen=min([m for m in MODELS if m!='uniform'],
               key=lambda m:(tune[m]['brier_mean'],MODELS.index(m)))
    return tune,test,chosen,bymodel


def overlap_p(total_hits, draw_count):
    prob=hypergeom.pmf(np.arange(6),35,5,5)
    dist=np.array([1.])
    for _ in range(draw_count):dist=np.convolve(dist,prob)
    return float(dist[total_hits:].sum())


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--data',type=Path,default=DATA_DEFAULT)
    ap.add_argument('--out',type=Path,default=HERE)
    args=ap.parse_args()
    args.out.mkdir(parents=True,exist_ok=True)
    ids,X=load_data(args.data)
    result={
       'timestamp_purpose':'2026-10-29 afternoon Europe/Athens; predict target #14357 at 19:00 before result publication',
       'source_range':[ids[0],ids[-1]],
       'dataset_sha256':hashlib.sha256(args.data.read_bytes()).hexdigest(),
       'target_draw_id':14357,
       'missing_14356':'15:00 draw #14356 occurred, but outcome NOT used or available in this dataset',
       'forecast_horizon':2,
       'training_selection':'early targets indices 30..59 (prior 30), selected solely by mean Brier',
       'evaluation':'40 targets indices 60..99; for each, train on data ending 2 draws prior',
       'model_grid':MODELS,
       'null':'independent uniform five-of-35 subsets',
       'random_overlap_expected_40':40*25/35,
       'software':{'python':platform.python_version(),'numpy':np.__version__}
    }
    outcomes={}
    for h in (1,2):
        tune, test, chosen, per_target=holdout_rows(X,h)
        def extra(d):
            for m,rs in d.items():
                if rs['draws']==40:
                    rs['p_one_sided_hits_fixed_ticket']=overlap_p(rs['hits'],40)
            return d
        pred=predict(X,chosen,h)
        outcomes[str(h)]={
            'selected_model':chosen,'selection_30':tune,'test_40':extra(test),
            'selected_test_score':test[chosen],
            'uniform_baseline_test':test['uniform'],
            'selected_full_data_ticket':top_ticket(pred),
            'selected_full_data_marginals':{str(i+1):round(float(v),8) for i,v in enumerate(pred)},
            'holdout_ticket_rows':[{'draw_id':ids[r['target_index']],**r} for r in per_target[chosen] if r['target_index']>=60],
        }
    result['horizons']=outcomes
    # Commit the two-draw-ahead forecast only. 14357 is in the future as-of creation.
    result['precommit_prediction']={
        'draw_id':14357,'last_known_draw_id':14355,
        'numbers':list(outcomes['2']['selected_full_data_ticket']),
        'model':outcomes['2']['selected_model'],
        'scope':'two-step forecast without knowledge of draw #14356',
        'data_leakage':False,
        'selection':'target 14357 numbers frozen independently of #14356 and #14357'
    }
    out=args.out/'extra5_walkforward_fit_results.json'
    out.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
    print('DATA',ids[0],ids[-1], 'sha256',result['dataset_sha256'])
    for h in (1,2):
        rr=outcomes[str(h)]
        print('HORIZON',h,'SELECT',rr['selected_model'],'30-draw fit score',rr['selection_30'][rr['selected_model']], '40 draw held-out',rr['selected_test_score'])
        print('  UNIFORM',rr['uniform_baseline_test'])
        print('  NEW TICKET',rr['selected_full_data_ticket'])
    print('PRECOMMIT:',result['precommit_prediction'])
    print('OUTPUT',out)

if __name__=='__main__':main()
