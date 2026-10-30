#!/usr/bin/env python3
"""Freeze TWO training-only exploratory challengers; never opens holdout data.

This is part of a single model comparison: primary robust uniform fallback,
plus (a) best nonuniform by training-only cross-validated total log score,
(b) best nonuniform with positive gains on both folds. All declared before test.
"""
from pathlib import Path
import datetime as dt,hashlib,json,math
from forecast import (MODELS,load_train,choose_model,next_schedule,prior_weights,
                      deterministic_top5,product_weight_sample,odds_marginals,
                      symmetric5,log_probability,name)


def build(train_path:Path)->dict:
    draws=load_train(train_path)
    sha=hashlib.sha256(train_path.read_bytes()).hexdigest()
    _,selection=choose_model(draws)
    scores=selection['scores']
    options=list(MODELS[1:])
    best=max(options,key=lambda m:(scores[name(m)]['combined_gain_nats'],name(m)))
    stable=[m for m in options if all(x['vs_uniform']>0 for x in scores[name(m)]['folds'])]
    best_stable=max(stable,key=lambda m:(min(x['vs_uniform'] for x in scores[name(m)]['folds']), name(m))) if stable else None
    configurations=[('best_training_logscore',best)]
    if best_stable and best_stable!=best:configurations.append(('positive_both_folds',best_stable))
    out=[]
    for policy,model in configurations:
        forecasts=[]
        for draw_id,date,time in next_schedule(draws[-1],5):
            w=prior_weights(draws,len(draws),dt.date.fromisoformat(date),time,model)
            ticket=deterministic_top5(w,sha,draw_id)
            seed=int.from_bytes(hashlib.sha256((sha+f'|{draw_id}|{name(model)}|challenger').encode()).digest(),'big')
            forecasts.append({'draw_id':draw_id,'date':date,'time':time,
                              'primary_ticket':list(ticket),
                              'primary_ticket_probability':math.exp(log_probability(w,ticket)),
                              'independent_weighted_sample':list(product_weight_sample(w,seed)),
                              'weights':list(map(float,w)),
                              'inclusion_probabilities':list(map(float,odds_marginals(w))),
                              'model_log_likelihood_normalizer':math.log(symmetric5(w))})
        out.append({'policy':policy,'selected_model':list(model),'model_name':name(model),
                    'fold_scores':scores[name(model)]['folds'], 'forecasts':forecasts})
    return {'protocol':'EXTRA5-PREHELDOUT-CHALLENGERS-v1',
            'train_sha256':sha,'train_count':len(draws),'train_ids':[draws[0].id,draws[-1].id],
            'holdout_was_not_read':True,'challengers':out,
            'selection_criterion':'best training-only combined fold logscore; and best worst-fold positive-logscore candidate (if different)',
            'caution':'Both candidates selected only using 599 draws, but previously published holdout draws have already been examined by the broader project.'}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--train',type=Path,required=True);p.add_argument('--lock',type=Path,required=True)
    args=p.parse_args()
    if args.lock.exists():raise SystemExit('REFUSE to overwrite existing challenger lock')
    content=json.dumps(build(args.train),sort_keys=True,indent=2)+'\n'
    args.lock.write_text(content)
    obj=json.loads(content)
    print(json.dumps({'challengers':[{'policy':c['policy'],'model':c['model_name'],
                                       'predictions':[(x['draw_id'],x['primary_ticket']) for x in c['forecasts']]} for c in obj['challengers']],
                      'sha256_lock':hashlib.sha256(content.encode()).hexdigest()},indent=2))
