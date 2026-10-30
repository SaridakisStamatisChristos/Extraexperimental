#!/usr/bin/env python3
"""EXTRA 5 599/5 quarantined retrospective holdout.

Fit from train_599.csv ONLY. Never opens the complete archive or holdout.
This is an empirical statistical baseline search, NOT recovered lottery RNG.
Usage: python forecast.py --train train_599.csv --lock predictions_LOCK.json
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, math, random
from dataclasses import dataclass
from pathlib import Path
import numpy as np

N=math.comb(35,5)
MODELS=(
    ('uniform',0,0),
    ('hot',0,.15), ('hot',0,.35), ('cold',0,.15), ('cold',0,.35),
    ('recency',20,.15), ('recency',20,.35),
    ('recency',60,.15), ('recency',60,.35),
    ('recency',120,.15), ('recency',120,.35),
    ('repeat',0,-.20), ('repeat',0,.20),
    ('hour',0,.25), ('weekday',0,.25),
    ('lag2',0,-.20), ('lag2',0,.20),
    ('seasonal7',0,.20),
)
FOLDS=((200,399),(399,599))

@dataclass(frozen=True)
class Draw:
    id:int
    date:dt.date
    time:str
    numbers:tuple[int,...]


def load_train(filename:Path)->list[Draw]:
    with filename.open(newline='') as f:
        rdr=csv.DictReader(f)
        needed={'draw_id','date','time','n1','n2','n3','n4','n5'}
        if not needed.issubset(rdr.fieldnames or []):raise ValueError('missing columns')
        out=[]
        for r in rdr:
            vals=tuple(int(r[f'n{k}']) for k in range(1,6))
            if len(set(vals))!=5 or any(not 1<=v<=35 for v in vals):raise ValueError('bad ticket')
            out.append(Draw(int(r['draw_id']),dt.date.fromisoformat(r['date']),r['time'],vals))
    if len(out)!=599 or [d.id for d in out]!=list(range(13754,14353)):
        raise ValueError('train-only contract violated: expected 599 consecutive IDs #13754-14352')
    for a,b in zip(out,out[1:]):
        if (a.time,b.time) not in (('15:00','19:00'),('19:00','15:00')):
            raise ValueError('unexpected draw clock order')
        if (b.date-a.date).days != (1 if a.time=='19:00' else 0):
            raise ValueError('unexpected draw date order')
    return out


def next_schedule(last:Draw,count=5)->list[tuple[int,str,str]]:
    day=last.date;hour=last.time;targets=[]
    for k in range(count):
        if hour=='15:00':hour='19:00'
        else:hour='15:00';day+=dt.timedelta(days=1)
        targets.append((last.id+k+1,day.isoformat(),hour))
    return targets


def prior_weights(draws:list[Draw], end:int, target_date:dt.date,
                  target_time:str, model:tuple)->np.ndarray:
    """end exclusive; all number observations strictly before end."""
    mode, parameter, alpha=model
    w=np.ones(35,dtype=float)
    if mode=='uniform':return w
    if end<1:raise ValueError('empty prefix for conditioned model')
    if mode in ('repeat','lag2'):
        reference=end-(1 if mode=='repeat' else 2)
        if reference<0:return w
        w[np.asarray(draws[reference].numbers)-1]=math.exp(alpha)
        return w
    if mode=='seasonal7':
        reference=end-7
        if reference<0:return w
        w[np.asarray(draws[reference].numbers)-1]=math.exp(alpha)
        return w
    if mode=='hour': ids=[i for i in range(end) if draws[i].time==target_time]
    elif mode=='weekday':ids=[i for i in range(end) if draws[i].date.weekday()==target_date.weekday()]
    else:ids=list(range(end))
    if not ids:return w
    factors=np.ones(len(ids))
    if mode=='recency':factors=np.exp2(-((end-1)-np.asarray(ids))/parameter)
    counts=np.zeros(35,dtype=float)
    for i,k in zip(ids,factors):counts[np.asarray(draws[i].numbers)-1]+=k
    scaled=counts/(factors.sum()*5/35)  # fair expected marginal appearances per number
    if mode=='cold':scaled=np.maximum(.05,2-scaled)
    w=(1-alpha)+alpha*scaled
    assert bool(np.all(np.isfinite(w)) and np.all(w>0))
    return w


def symmetric5(weights:np.ndarray)->float:
    """Exact combinatorial partition function, O(35*5), no 324632 tickets loop."""
    e=[1.,0.,0.,0.,0.,0.]
    for x in weights:
        for k in range(5,0,-1):e[k]+=x*e[k-1]
    return e[5]


def log_probability(weights:np.ndarray,ticket:tuple[int,...])->float:
    return float(np.log(weights[np.asarray(ticket)-1]).sum()-math.log(symmetric5(weights)))


def odds_marginals(weights:np.ndarray)->np.ndarray:
    """P(number included) for exactly five weighted-without-replacement subset law."""
    # derivative of e_5(w) * w_i / e_5(w)
    partition=symmetric5(weights)
    marg=np.zeros(35)
    for i,wi in enumerate(weights):
        rest=np.delete(weights,i)
        e=[1.,0.,0.,0.,0.]
        for x in rest:
            for k in range(4,0,-1):e[k]+=x*e[k-1]
        marg[i]=wi*e[4]/partition
    assert abs(float(marg.sum())-5)<1e-8
    return marg


def deterministic_top5(weights:np.ndarray, train_sha:str, target_id:int)->tuple[int,...]:
    """Top five marginal inclusion odds; keyed SHA-256 breaks EXACT ties only."""
    hashes=[int.from_bytes(hashlib.sha256((train_sha+f'|{target_id}|{i+1}|tie').encode()).digest()[:8],'big') for i in range(35)]
    chosen=sorted(range(35),key=lambda i:(-float(weights[i]),hashes[i]))[:5]
    return tuple(sorted(i+1 for i in chosen))


def product_weight_sample(weights:np.ndarray, seed:int)->tuple[int,...]:
    """Exact subset sampler: P(S) proportional to product_i∈S(weights_i)."""
    rnd=random.Random(seed)
    # DP Z[i][k] = k-th symmetric polynomial of weights[i:]
    Z=np.zeros((36,6),dtype=float);Z[35,0]=1.
    for i in range(34,-1,-1):
        Z[i,0]=1.
        for k in range(1,6):Z[i,k]=Z[i+1,k]+weights[i]*Z[i+1,k-1]
    remaining=5;chosen=[]
    for i in range(35):
        if remaining==0:break
        conditional=weights[i]*Z[i+1,remaining-1]/Z[i,remaining]
        if rnd.random()<conditional:
            chosen.append(i+1);remaining-=1
    assert remaining==0 and len(chosen)==5
    return tuple(chosen)


def trial_scores(draws:list[Draw],model:tuple,start:int,stop:int)->dict:
    logs=[];hits=[]
    for t in range(start,stop):
        d=draws[t]
        w=prior_weights(draws,t,d.date,d.time,model)
        logs.append(log_probability(w,d.numbers))
        # use fixed non-evaluated tie-break control by target_id alone
        p=deterministic_top5(w,'evaluation_seed_never_tuned',d.id)
        hits.append(len(set(p)&set(d.numbers)))
    return {'log_likelihood':float(math.fsum(logs)),
            'vs_uniform':float(math.fsum(logs)+(stop-start)*math.log(N)),
            'hits':int(sum(hits)), 'count':int(len(logs))}


def name(model):
    return ':'.join(str(k) for k in model)


def choose_model(draws:list[Draw])->tuple[tuple,dict]:
    ledger={}
    for model in MODELS:
        fold=[trial_scores(draws,model,start,stop) for start,stop in FOLDS]
        ledger[name(model)]={'folds':fold,'combined_gain_nats':sum(x['vs_uniform'] for x in fold),
                            'combined_hits':sum(x['hits'] for x in fold)}
    # Strong stability gate: BOTH prespecified validation folds must individually
    # exceed uniform in log-probability by >= log(3). If no improvement this
    # robust, choose uniform rather than force a potentially overfit model.
    qualified=[m for m in MODELS[1:] if all(x['vs_uniform']>=math.log(3.) for x in ledger[name(m)]['folds'])]
    selected=max(qualified,key=lambda m:(ledger[name(m)]['combined_gain_nats'],name(m))) if qualified else MODELS[0]
    return selected, {'scores':ledger,'qualification':'both folds each >= log(3) nats improvement over uniform; else uniform',
                      'qualifying_models':[name(m) for m in qualified]}


def fit(train_path:Path)->dict:
    draws=load_train(train_path)
    sha=hashlib.sha256(train_path.read_bytes()).hexdigest()
    model,selection=choose_model(draws)
    predictions=[]
    for draw_id,date,time in next_schedule(draws[-1],5):
        w=prior_weights(draws,len(draws),dt.date.fromisoformat(date),time,model)
        top=deterministic_top5(w,sha,draw_id)
        prob=math.exp(log_probability(w,top))
        random_seed=int.from_bytes(hashlib.sha256((sha+f'|{draw_id}|draw').encode()).digest(),'big')
        random_ticket=product_weight_sample(w,random_seed)
        predictions.append({'draw_id':draw_id,'date':date,'time':time,
                 'primary_ticket':list(top),'primary_ticket_probability':prob,
                 'independent_weighted_sample':list(random_ticket),
                 'inclusion_probabilities':[float(x) for x in odds_marginals(w)],
                 'weights':[float(x) for x in w],
                 'model_log_likelihood_normalizer':math.log(symmetric5(w))})
    return {
       'protocol':'EXTRA5-599-TRAIN-5-SEALED-RETROSPECTIVE-2026-10-30-v1',
       'train_sha256':sha, 'train_count':len(draws),'train_ids':[draws[0].id,draws[-1].id],
       'target_ids':[x['draw_id'] for x in predictions],
       'baseline':'uniform 1/C(35,5) exactly; iid conditional reference',
       'selected_model':list(model),'selected_model_name':name(model),
       'selection':selection,
       'primary_metric':'summed log probability of actual tickets (proper scoring rule)',
       'prediction_policy':'top five inclusion odds; ties SHA256 of train-only data and target ID',
       'secondary_ticket_policy':'exact product-weighted combinatorial subset sampling, deterministic seed from train SHA256 and target ID',
       'future_draws_used_for_selection':0,'future_draws_used_for_predictions':0,
       'heldout_results_read_by_this_program':False,
       'predictions':predictions,
       'caveat':'Retrospective quarantine only: outcomes already public in larger project; not truly fresh or prospective, and candidate family was informed by previous archive analysis.'
    }


def main()->None:
    p=argparse.ArgumentParser();p.add_argument('--train',type=Path,required=True)
    p.add_argument('--lock',type=Path,required=True)
    args=p.parse_args()
    if args.lock.exists():raise SystemExit('REFUSE to overwrite existing lock')
    report=fit(args.train)
    canonical=json.dumps(report,sort_keys=True,indent=2)+'\n'
    args.lock.write_text(canonical)
    print(json.dumps({'selection':report['selected_model_name'],
        'qualified':report['selection']['qualifying_models'],
        'predictions':[{k:v for k,v in x.items() if k in ('draw_id','primary_ticket','independent_weighted_sample')} for x in report['predictions']],
        'sha256_lock':hashlib.sha256(canonical.encode()).hexdigest()},indent=2))

if __name__=='__main__':main()
