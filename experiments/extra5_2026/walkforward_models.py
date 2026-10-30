#!/usr/bin/env python3
"""True one-step-ahead-in-history EXTRA 5 model comparison.

EXPLORATORY retrospective *prequential* reconstruction on revealed 2026 draws;
not prospective blinded prediction. Constant uniform distribution is benchmark.
The likelihood-ratio mixture is an e-value for a FIXED model library under iid
uniform draws; this library was historically informed, and therefore the
retrospective number must NOT be promoted to preregistered evidence.
"""
from __future__ import annotations
import csv,hashlib,json,math
from pathlib import Path
import numpy as np
from statistical_audit import load_data

HERE=Path(__file__).resolve().parent
N=math.comb(35,5)
CONFIGS=(
 ('uniform',None,0),
 ('cumulative',None,.2),('cumulative',None,.6),
 ('cold',None,.2),('cold',None,.6),
 ('recency',10,.2),('recency',10,.6),
 ('recency',30,.2),('recency',30,.6),
 ('recency',100,.2),('recency',100,.6),
 ('repeat',None,-.35),('repeat',None,.35),
 ('same_hour',None,.3),('same_weekday',None,.3),
)

def name(c):return ':'.join(str(v) for v in c)

def weights(tickets,hours,weekdays,idx,config):
    mode,decay,alpha=config
    w=np.ones(35,dtype=np.float64)
    if mode=='uniform':return w
    if mode=='repeat':
        w[tickets[idx-1]-1]=math.exp(alpha)
        return w
    if mode=='same_hour':
        ids=np.flatnonzero(hours[:idx]==hours[idx])
    elif mode=='same_weekday':
        ids=np.flatnonzero(weekdays[:idx]==weekdays[idx])
    else:
        ids=np.arange(idx)
    if len(ids)==0:return w
    counts=np.zeros(35,dtype=np.float64)
    if mode=='recency':
        # fixed half-life, using only past draws and predeclared hyperparameters
        age=idx-1-ids
        factors=np.exp2(-age/decay)
    else:factors=np.ones(len(ids))
    for t,k in zip(ids,factors):counts[tickets[t]-1]+=k
    scaled=counts/(factors.sum()/7)
    if mode=='cold':scaled=np.maximum(.05,2-scaled)
    return (1-alpha)+alpha*scaled

def product_log_score(w,ticket):
    # exact 5th elementary symmetric polynomial normalized over ALL C(35,5) subsets
    es=np.array([1.,0.,0.,0.,0.,0.])
    for weight in w:
        for j in range(5,0,-1):es[j]+=weight*es[j-1]
    assert es[5]>0 and np.min(w)>0
    return float(np.sum(np.log(w[np.asarray(ticket)-1]))-math.log(es[5]))

def simulate(warmup=200):
    rows,_,tickets=load_data()
    hours=np.array([int(row['time'][:2]) for row in rows],dtype=np.int16)
    weekdays=np.array([__import__('datetime').date.fromisoformat(row['date']).weekday() for row in rows])
    details={name(c):{'log_scores':[],'hits':[],'selected_tickets':[]} for c in CONFIGS}
    for i in range(warmup,len(tickets)):
        for c in CONFIGS:
            w=weights(tickets,hours,weekdays,i,c)
            logp=product_log_score(w,tickets[i])
            pick=tuple(sorted(np.lexsort((np.arange(35),-w))[:5]+1))
            hits=len(set(pick)&set(map(int,tickets[i])))
            key=name(c)
            details[key]['log_scores'].append(logp)
            details[key]['hits'].append(hits)
            if i==len(tickets)-1:details[key]['selected_tickets']=list(pick)
    baseline=name(CONFIGS[0]); ll0=sum(details[baseline]['log_scores'])
    assert abs(ll0+(len(tickets)-warmup)*math.log(N))<1e-8
    result={}
    ev=[]
    for c in CONFIGS:
        nm=name(c);d=details[nm]
        diff=sum(d['log_scores'])-ll0
        if nm!=baseline:ev.append(diff)
        result[nm]={
          'forecast_count':len(d['hits']),
          'mean_log_probability':sum(d['log_scores'])/len(d['hits']),
          'log_likelihood_vs_uniform':diff,
          'likelihood_ratio_vs_uniform':math.exp(diff) if diff>-700 else 0.,
          'mean_hits_of_deterministic_top_5':sum(d['hits'])/len(d['hits']),
          'final_historical_top5':[int(v) for v in d['selected_tickets']],
        }
    # Mixture likelihood ratio: for a truly predeclared model library this
    # would be an e-value; here candidate choice follows previous research.
    m=max(ev)
    mixture_e=math.exp(m)*sum(math.exp(v-m) for v in ev)/len(ev)
    future=[name(c) for c in CONFIGS if c[0]!='uniform']
    report={
      'experiment':'EXTRA5-2026-PREQUENTIAL-EXPLORATORY-v1',
      'source_sha256':hashlib.sha256((HERE/'extra5_authoritative_2026.csv').read_bytes()).hexdigest(),
      'historical_warmup_draws':warmup,
      'first_scored_id':int(rows[warmup]['draw_id']),
      'last_scored_id':int(rows[-1]['draw_id']),
      'scored_draws':len(tickets)-warmup,
      'model_definitions':'uniform, shrunk cumulative/cold/recency half-life, last-draw repeats, same-hour, same-weekday; all product weighted, exactly normalized over C(35,5) subsets',
      'models_fixed_for_this_replay_not_prospective_preregistration':list(result),
      'results':result,
      'best_by_mean_log_likelihood':max(result,key=lambda k:result[k]['mean_log_probability']),
      'best_nonuniform_by_mean_log_likelihood':max(future,key=lambda k:result[k]['mean_log_probability']),
      'equal_weight_nonuniform_likelihood_ratio_mixture':mixture_e,
      'mixture_e_threshold_for_0_05_evidence':20.0,
      'uniform_random_expected_hits':25/35,
      'interpretation':'Entire 2026 dataset is previously exposed; these are one-step-ahead historical simulations, not a virgin holdout nor a blind prediction. A fixed independent-of-data model library would make the mixture a valid e-value under the iid uniform null. This family is informed by prior retrospective research, so this replay has no prospective preregistration claim.'
    }
    (HERE/'walkforward_results.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'scored_draws':report['scored_draws'],
       'best_model':report['best_by_mean_log_likelihood'],
       'best_nonuniform':report['best_nonuniform_by_mean_log_likelihood'],
       'equal_weight_lr_mixture':mixture_e,
       'best_ll_diff':max(result[n]['log_likelihood_vs_uniform'] for n in future),
       'table':{k:{a:round(x[a],5) for a in ('mean_log_probability','log_likelihood_vs_uniform','mean_hits_of_deterministic_top_5')} for k,x in result.items()}},indent=2))
    return report
if __name__=='__main__':simulate()
