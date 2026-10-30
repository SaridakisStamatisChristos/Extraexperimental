#!/usr/bin/env python3
"""Strictly post-lock independent evaluator for five quarantined public draws.

Does not import forecast.py or challengers.py. Receives locked JSON and
holdout CSV as separate inputs; refuses changed locks via pinned SHA256.
"""
from __future__ import annotations
import argparse,csv,hashlib,itertools,json,math
from pathlib import Path
from typing import Any

N=math.comb(35,5)
PINNED={
 'predictions_LOCK.json':'82f4208666c56b56fd7cdd27f56a4b937ac3cbdfcd072f6b83a438de22521561',
 'challengers_LOCK.json':'a3d75cb35324e6150d5425fa534d0aa68009b5f5e818134951926f189bdc414c',
}

def e5(weights:list[float])->float:
    e=[1.,0.,0.,0.,0.,0.]
    for w in weights:
        for j in range(5,0,-1):e[j]+=w*e[j-1]
    return e[-1]

def outcome(h:list[int], ticket:list[int], sample:list[int]|None,weights:list[float],marginals:list[float])->dict:
    overlap=sorted(set(ticket)&set(h))
    logp=sum(math.log(weights[v-1]) for v in h)-math.log(e5(weights))
    assert abs(sum(marginals)-5)<1e-8
    brier=sum(((1 if i+1 in h else 0)-marginals[i])**2 for i in range(35))
    return {'actual':h,'ticket':ticket,'matching_numbers':overlap,'hits':len(overlap),
            'independent_sample':sample,'independent_sample_hits':len(set(sample or [])&set(h)),
            'observed_ticket_log_probability':logp,
            'log_likelihood_ratio_vs_uniform':logp+math.log(N),
            'marginal_brier':brier}

def hit_distribution()->list[float]:
    return [math.comb(5,k)*math.comb(30,5-k)/N for k in range(6)]

def tail_n5_at_least(obs:int)->float:
    pmf=hit_distribution()
    dist=[1.]
    for _ in range(5):
        new=[0.]*(len(dist)+5)
        for i,p in enumerate(dist):
            for j,q in enumerate(pmf):new[i+j]+=p*q
        dist=new
    return sum(dist[obs:])

def load_test(file:Path)->list[dict]:
    with file.open(newline='') as f:r=list(csv.DictReader(f))
    ids=list(map(lambda x:int(x['draw_id']),r))
    if ids!=list(range(14353,14358)):raise ValueError('expected exactly five test IDs 14353..14357')
    for row in r:
        n=[int(row['n'+str(i)]) for i in range(1,6)]
        if len(set(n))!=5 or any(not 1<=v<=35 for v in n):raise ValueError('invalid heldout ticket')
    return r

def evaluate(test_path:Path,main_lock_path:Path,challengers_path:Path)->dict:
    for p in (main_lock_path,challengers_path):
        digest=hashlib.sha256(p.read_bytes()).hexdigest()
        if digest!=PINNED[p.name]:raise ValueError(f'lock SHA mismatch: {p} {digest}')
    main=json.loads(main_lock_path.read_text());ch=json.loads(challengers_path.read_text())
    if main['train_sha256']!=ch['train_sha256']:raise ValueError('trainer mismatch')
    rows=load_test(test_path)
    truth={int(r['draw_id']):r for r in rows}
    specs=[('evidence_gated_primary',main['selected_model_name'],main['predictions'])]
    for candidate in ch['challengers']:specs.append((candidate['policy'],candidate['model_name'],candidate['forecasts']))
    report={}
    for label,model,preds in specs:
        if [p['draw_id'] for p in preds]!=list(range(14353,14358)):raise ValueError('prediction ID mismatch')
        details=[]
        for p in preds:
            r=truth[p['draw_id']]
            if (r['date'],r['time']) != (p['date'],p['time']):raise ValueError('target date/time discrepancy')
            numbers=sorted(int(r['n'+str(i)]) for i in range(1,6))
            checked=outcome(numbers,p['primary_ticket'],p['independent_weighted_sample'],
                            p['weights'],p['inclusion_probabilities'])
            details.append({'draw_id':p['draw_id'],'date':r['date'],'time':r['time'],**checked})
        hits=sum(x['hits'] for x in details)
        llr=sum(x['log_likelihood_ratio_vs_uniform'] for x in details)
        report[label]={'model':model,'primary_total_hits':hits,
                       'independent_sample_total_hits':sum(x['independent_sample_hits'] for x in details),
                       'primary_mean_hits':hits/5,
                       'total_log_likelihood_ratio_vs_uniform':llr,
                       'joint_likelihood_ratio_vs_uniform':math.exp(llr),
                       'mean_multilabel_brier':sum(x['marginal_brier'] for x in details)/5,
                       'uniform_5_draw_expected_hits':5*25/35,
                       'one_sided_uniform_hit_tail_conditional_on_preselected_tickets':tail_n5_at_least(hits),
                       'predictions':details}
    return {'experiment':'EXTRA5-2026-LAST-5-SEPARATE-RETROSPECTIVE-v1',
            'train_count':599,'test_count':5,'last_test_id':14357,
            'test_ids':list(range(14353,14358)),
            'train_sha256':main['train_sha256'],
            'locked_file_sha256':PINNED,
            'truth_sha256':hashlib.sha256(test_path.read_bytes()).hexdigest(),
            'uniform_prob_one_ticket':1/N,
            'uniform_single_draw_hit_distribution':hit_distribution(),
            'comparison':report,
            'interpretation':'Retrospectively quarantined (published archive). Five trials insufficient to claim genuine forecasting edge; score is conditioned on fixed predictions and an iid uniform lottery reference.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--test',type=Path,required=True)
    p.add_argument('--primary',type=Path,required=True);p.add_argument('--challengers',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    result=evaluate(args.test,args.primary,args.challengers)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:{'model':v['model'],'hits':v['primary_total_hits'],
                          'sample_hits':v['independent_sample_total_hits'],
                          'log_LR':v['total_log_likelihood_ratio_vs_uniform'],
                          'LR':v['joint_likelihood_ratio_vs_uniform'],
                          'brier':v['mean_multilabel_brier'],
                          'p_ge_hits':v['one_sided_uniform_hit_tail_conditional_on_preselected_tickets'],
                          'per_draw':[(x['draw_id'],x['ticket'],x['actual'],x['hits']) for x in v['predictions']]}
                      for k,v in result['comparison'].items()},indent=2))
if __name__=='__main__':main()
