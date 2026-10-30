#!/usr/bin/env python3
"""Actual deterministic PRNG/seed/sampler search, followed by year-separated testing.

Development uses only 2022-2024 actual numbers; validation 2025; test 2026.
A config selected from development is frozen BEFORE evaluation. All historical
outcomes existed at research time: these tests are temporal, not prospective.

Uses generator + sampler implementations unchanged from the prior project.
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
import numpy as np
from timestamp_prng_scan import gen,sample,seedspecs,metadata,make_seed,asmask
ROOT=Path(__file__).resolve().parent
GENS=['numerical_lcg32','ansi_lcg32_fullword','msvc_rand15','xorshift32','xorshift64star',
      'splitmix64','pcg32_fixed_stream','mt19937_python']
SAMPLERS=['rank32_rejection','combinadic24','unique_mod35','fisher_yates5_modulo','fisher_yates5_unbiased']
START_2025=2192
START_2026=2922

def rows_from_csv(path):
    rows=list(csv.DictReader(open(path,newline='')))
    assert len(rows)==3526
    assert all(int(r['draw_id'])==10832+i for i,r in enumerate(rows))
    assert rows[START_2025]['date']=='2025-01-01'
    assert rows[START_2026]['date']=='2026-01-01'
    return rows

def build_prediction_matrix(rows):
    times=[metadata(r) for r in rows]
    matrices=[];configs=[]
    for kind in GENS:
        for seedtype,offset in seedspecs():
            seeds=[make_seed(m,seedtype,offset) for m in times]
            for sampler in SAMPLERS:
                try:
                    masks=np.fromiter((asmask(sample(kind,s,sampler)) for s in seeds),dtype=np.uint64,count=len(seeds))
                except RuntimeError:
                    continue
                matrices.append(masks)
                configs.append({'generator':kind,'seed_rule':seedtype,'seed_offset':offset,'sampler':sampler})
    return configs,np.stack(matrices)

def hits_per_model(pred,actual):
    return np.bitwise_count(np.bitwise_and(pred,actual)).sum(axis=1,dtype=np.int64)

def main(replicates=500):
    path=ROOT/'extra5_2022_2026_authoritative.csv'
    with (ROOT/'train_2022_2024.csv').open(newline='') as f:
        trainrows=list(csv.DictReader(f))
    with (ROOT/'evaluation_calendar_2025_2026.csv').open(newline='') as f:
        eval_calendar=list(csv.DictReader(f))
    assert len(trainrows)==2192 and len(eval_calendar)==1334
    assert all(int(r['draw_id'])==10832+i for i,r in enumerate(trainrows+eval_calendar))
    # Precompute unlabelled ticket predictions; the 2025/2026 source file
    # supplying actual ticket outcomes is not even opened until after freeze.
    configs,preds=build_prediction_matrix(trainrows+eval_calendar)
    assert len(configs)==8*len(seedspecs())*5, len(configs)
    trainmask=np.asarray([asmask(tuple(int(r[f'n{i}']) for i in range(1,6))) for r in trainrows],dtype=np.uint64)
    select_hits=hits_per_model(preds[:,:START_2025],trainmask)
    selected_idx=int(select_hits.argmax())
    selected=dict(configs[selected_idx]);selected['selection_hits_2022_2024']=int(select_hits[selected_idx])
    # Search-corrected null: independent fair five-number tickets for each selection draw,
    # identical 1080-model candidate prediction library scanned each replicate.
    rng=np.random.default_rng(20261030)
    maxscores=[]
    for _ in range(replicates):
        chosen=np.argpartition(rng.random((START_2025,35)),4,axis=1)[:,:5].astype(np.uint64)
        fair_masks=np.bitwise_or.reduce(np.left_shift(np.uint64(1),chosen),axis=1)
        maxscores.append(int(hits_per_model(preds[:,:START_2025],fair_masks).max()))
    p_selection=(1+sum(x>=selected['selection_hits_2022_2024'] for x in maxscores))/(1+replicates)
    # Save the decision before reading any validation or test ticket labels.
    freeze={
        'source_sha256':json.loads((ROOT/'provenance.json').read_text())['csv_sha256'],
        'candidate_count':len(configs),
        'selection_years':[2022,2023,2024],
        'validation_year':2025,'final_test_year':2026,
        'selection_rule':'max 2022-2024 number overlap; deterministic lexicographic model-enumeration tie breaking',
        'selected_candidate':selected,
        'search_adjusted_selection_p_value':p_selection,
        'selection_null_replicates':replicates,
        'selection_null_seed':20261030,
        'selection_null_max_median':float(np.median(maxscores)),
        'selection_null_max_p95':float(np.percentile(maxscores,95)),
        'model_precomputed_2025_2026_2022_2024_numbers_SHA256':hashlib.sha256(preds[selected_idx].tobytes()).hexdigest(),
        'selection_phase_did_not_read_validation_or_test_numbers':True,
        'candidate_model_is_not_actual_operator_attribution':True,
        'predictor': [sorted([j+1 for j in range(35) if (int(m)>>j)&1]) for m in preds[selected_idx,START_2025:]],
    }
    frozen=ROOT/'selected_generator_PRE_EVALUATION.json'
    # Freeze on first run. On repeat verify lock instead of rewriting.
    if frozen.exists():
        prior=json.loads(frozen.read_text())
        assert prior==freeze,'LOCK VIOLATION: existing selection differs; do not overwrite'
    else:
        frozen.write_text(json.dumps(freeze,indent=2)+'\n')
    print('FROZEN candidate:',selected, 'selection null p=',p_selection,flush=True)
    # After freezing, open outcome-bearing CSV for the first time.
    allrows=rows_from_csv(path)
    valmask=np.asarray([asmask(tuple(int(r[f'n{i}']) for i in range(1,6))) for r in allrows[START_2025:START_2026]],dtype=np.uint64)
    testmask=np.asarray([asmask(tuple(int(r[f'n{i}']) for i in range(1,6))) for r in allrows[START_2026:]],dtype=np.uint64)
    val_hits=hits_per_model(preds[:,START_2025:START_2026],valmask)
    test_hits=hits_per_model(preds[:,START_2026:],testmask)
    sel_val=int(val_hits[selected_idx]);sel_test=int(test_hits[selected_idx]);sel_train=int(select_hits[selected_idx]);
    val_matches=np.bitwise_count(np.bitwise_and(preds[selected_idx,START_2025:START_2026],valmask))
    test_matches=np.bitwise_count(np.bitwise_and(preds[selected_idx,START_2026:],testmask))
    # Report available marginal cross-model retrospective values separately (NOT for selection).
    output={
        'experiment':'fixed-generator-year-split-2022-to-2026',
        'frozen_file':str(frozen.name),
        'dataset_sha256':freeze['source_sha256'],
        'candidate_family_count':len(configs),
        'selected':selected,
        'year_boundaries':{'select_2022_2024':START_2025,'validation_2025':730,'test_2026':604},
        'selected_train_hits':sel_train,'selected_train_expected':START_2025*25/35,
        'selected_validation_hits':sel_val,'selected_validation_expected':730*25/35,
        'selected_test_hits':sel_test,'selected_test_expected':604*25/35,
        'selected_validation_exact_five':int(np.sum(preds[selected_idx,START_2025:START_2026]==valmask)),
        'selected_test_exact_five':int(np.sum(preds[selected_idx,START_2026:]==testmask)),
        'validation_match_distribution':np.bincount(val_matches,minlength=6).tolist(),
        'test_match_distribution':np.bincount(test_matches,minlength=6).tolist(),
        'selection_search_adjusted_p':p_selection,
        'selection_null_max_scores_summary':{'median':float(np.median(maxscores)), 'p05':float(np.percentile(maxscores,5)), 'p95':float(np.percentile(maxscores,95)), 'max':max(maxscores)},
        'validation_models_above_uniform_expectation':int(np.sum(val_hits>730*25/35)),
        'test_models_above_uniform_expectation':int(np.sum(test_hits>604*25/35)),
        'best_posthoc_validation_hits':int(val_hits.max()),
        'best_posthoc_test_hits':int(test_hits.max()),
        'model_selected_before_test':True,
        'historical_results_known_in_research':True,
        'interpretation':'No actual RNG identified by seed schedule; performance of selection should be judged on frozen year-forward 2025 and 2026 scores, never by posthoc max.'
    }
    (ROOT/'seeded_generator_results.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--calibration',type=int,default=500);args=p.parse_args()
    main(args.calibration)
