#!/usr/bin/env python3
"""Family-wise Monte Carlo calibration for searching 9360 RNG configurations over 20 EXTRA 5 draws."""
import csv,json, time
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
from extra5_mass_algorithm_benchmark import Source, draw, DRAWS, SAMPLERS, exact_tail
P=Path(__file__).parent
results=json.loads((P/'extra5_mass_algorithm_results.json').read_text())
rows=list(csv.DictReader(open(P/'extra5_mass_algorithm_scores.csv')))
masks=np.load(P/'extra5_mass_algorithm_holdout_masks.npz')['masks']
assert len(rows)==len(masks)==9360
actual=np.array([sum(1<<(n-1) for n in s) for _,s in DRAWS[-20:]],dtype=np.uint64)
obs=np.bitwise_count(np.bitwise_and(masks,actual[None,:])).sum(axis=1).astype(int)
score_saved=np.array([int(r['holdout_hits_20']) for r in rows])
# Rows were originally generated family, seed, sampler (not sorted by training).
order=[]
for family in results['families']:
    for ix in range(8 if family in ['MATH-BBS','MATH-RSA'] else 32):
        for sampler in SAMPLERS:
            order.append((family,ix,sampler))
assert len(order)==9360
# Map order array to sorted-by-training CSV.
key_to_idx={key:i for i,key in enumerate(order)}
idx=np.array([key_to_idx[(r['family'],int(r['seed_index']),r['sampler'])] for r in rows])
assert np.array_equal(score_saved,obs[idx]),'stored candidate tickets do not agree with recomputed scores'
# Permutation of actual historical draws is a second null check, but not a fair iid simulation.
t0=time.time()
rng=np.random.default_rng(123456789)
R=3000
maxima=np.empty(R,dtype=np.int16)
selected=np.empty(R,dtype=np.int16)
preselect_idx=idx[0]
for i in range(R):
    # Random uniform five-number combinations without replacement for each independent draw.
    # Use 20 independent permutations of [0..34].
    target=np.fromiter((sum(1<<int(n) for n in rng.choice(35,size=5,replace=False)) for j in range(20)),dtype=np.uint64,count=20)
    scores=np.bitwise_count(np.bitwise_and(masks,target[None,:])).sum(axis=1)
    maxima[i]=scores.max()
    selected[i]=scores[preselect_idx]
    if (i+1)%1000==0:print('null replications',i+1,'seconds',round(time.time()-t0,1),flush=True)
real_max=int(obs.max());real_preselect=int(obs[preselect_idx]);tail20=exact_tail(20)
cal={
 'replications':R,'null_seed':123456789,
 'null_simulation':'20 independent uniform 5-subsets of 1..35 per replicate; score all 9360 fixed candidate sequences and take maximum',
 'actual_search_max':real_max,
 'mc_count_at_or_above_max':int((maxima>=real_max).sum()),
 'mc_p_plus_one':float((1+(maxima>=real_max).sum())/(R+1)),
 'mc_max_median':float(np.median(maxima)),
 'mc_max_p05':float(np.quantile(maxima,.05)),
 'mc_max_p95':float(np.quantile(maxima,.95)),
 'mc_max_min':int(maxima.min()),'mc_max_max':int(maxima.max()),
 'preselected_score':real_preselect,
 'preselected_mc_p_plus_one':float((1+(selected>=real_preselect).sum())/(R+1)),
 'preselected_exact_one_sided_p':float(tail20[real_preselect]),
 'all_candidate_average_score':float(obs.mean()),
 'all_candidate_train_vs_test_corr':float(np.corrcoef([int(r['train_hits_80']) for r in rows],score_saved)[0,1]),
 'exact_5of5_among_9360_configurations':sum(int(r['holdout_exact']) for r in rows),
 'seconds':round(time.time()-t0,1)
}
results['family_wise_null_calibration']=cal
(P/'extra5_mass_algorithm_results.json').write_text(json.dumps(results,indent=2))
# Chart score frequencies with expected single-candidate mean, showing selection bias.
fig,axs=plt.subplots(1,2,figsize=(12,4.7))
axs[0].hist(score_saved,bins=np.arange(score_saved.min()-.5,score_saved.max()+1.5,1))
axs[0].axvline(20*25/35,linestyle='--',label='Chance expectation (14.29)')
axs[0].axvline(real_preselect,linestyle=':',label='Best training-selected (17)')
axs[0].axvline(real_max,linestyle='-.',label='Best after looking (30)')
axs[0].set_xlabel('Matches across latest 20 draws (out of 100 picks)')
axs[0].set_ylabel('Configurations')
axs[0].legend(fontsize=8)
axs[0].set_title('All 9,360 holdout scores')
axs[1].hist(maxima,bins=np.arange(maxima.min()-.5,maxima.max()+1.5,1))
axs[1].axvline(real_max,linestyle='--',label='Observed searched maximum: 30')
axs[1].set_xlabel('Highest score among 9,360 attempts')
axs[1].set_ylabel('Random-dataset simulations')
axs[1].legend(fontsize=8)
axs[1].set_title('Null distribution of the BEST score (3,000 trials)')
fig.tight_layout()
fig.savefig(P/'extra5_mass_algorithm_comparison.png',dpi=170)
plt.close(fig)
(P/'extra5_mass_algorithm_research_report.md').write_text(f'''# EXTRA 5: 60 RNG families × five sampling methods × fixed seeds

## Data provenance
Source: https://numerics.gr/extra-5/kliroseis-apotelesmata
100 results manually transcribed from the published results page, drawing IDs 14256–14355 (9 September – 28 October 2026). Latest 20 are cross-checked against https://www.lotteryextreme.com/greece/extra5-results and previous 20-draw source file.

## Experiment design
- **60 implemented RNG families**: conventional PRNGs (MT19937, Xorshift, Xoshiro, SplitMix64, PCG64, Philox), hash-counter (SHA-1, SHA-2, SHA-3, SHAKE, Blake), keyed HMAC/Blake, block cipher generators (AES-128/192/256 CFB, CTR, ECB counter; Camellia, DES-equivalent through equal-key 3DES, IDEA, CAST5, SEED, Blowfish), ChaCha20, and simplified number-theoretic BBS/RSA toys.
- **Five samplers**: uniform sequential removal, uniform rejection of duplicates, reservoir sampling, combinatorial unranking, random-key sort. Seed values independently chosen using deterministic SHA-512 expansion of a public constant. 32 seeds for most families, eight for BBS/RSA.
- **{results['specification']['total_configs']:,} tested configurations**, zero runtime failures.
- Training: 80 chronological historical draws, IDs 14256–14335. Holdout: latest 20 draws, IDs 14336–14355. Model selected by highest training score with tie-breaking independent of holdout.
- Score: total matching individual numbers out of five per draw. A random combination has 25/35 ≈ 0.714 matching numbers per draw; expected training score 57.14, expected validation score 14.29.

## Reproducible outcomes
- **Best selected by first 80**: {results['best_train_selected']['family']}, seed {results['best_train_selected']['seed_index']}, {results['best_train_selected']['sampler']}. Train **{results['best_train_selected']['train_hits_80']}/400**; validation **{real_preselect}/100**; one-sided held-out exact null p = {cal['preselected_exact_one_sided_p']:.4f}.
- **Best found by inspecting the latest 20** (invalid as a held-out prediction): {results['best_holdout_posthoc']['family']}, seed {results['best_holdout_posthoc']['seed_index']}, {results['best_holdout_posthoc']['sampler']}; **{real_max}/100** validation and {results['best_holdout_posthoc']['train_hits_80']}/400 training. Single-model exact p = {float(tail20[real_max]):.6g}; Bonferroni adjustment for {len(rows)} configurations = {results['baseline']['tail_holdout_best_among_all_bonferroni']:.4f}.
- **Monte Carlo family-wise calibration**: {R} independent random 20-draw datasets scored against the same {len(rows)} fixed configurations; maxima >= {real_max} in {cal['mc_count_at_or_above_max']} cases, p ≈ {cal['mc_p_plus_one']:.4f} (plus-one estimate), median searched maximum {cal['mc_max_median']:.0f}, central 90% range {cal['mc_max_p05']:.0f}–{cal['mc_max_p95']:.0f}.
- **No exact 5/5** among all 9,360 configurations over these 20 results (0 observed). Average held-out score across configurations: {cal['all_candidate_average_score']:.3f}.
- Train/holdout score correlation: {cal['all_candidate_train_vs_test_corr']:.3f}.

## Key limitations and interpretation
These are independently seeded illustrative generator variants, **NOT reproductions of Allwyn's implementation**. BBS/RSA variants are simplified mathematical toy constructions, not production cryptography. Even the AES/DES generators are not equivalent to the original closed-source mixture, seeding and switching mechanisms. The generator is modeled as a continuing byte stream without per-draw reseeding, which differs from some electronic lottery designs. Five-number outcomes lose the internal bits, output order, and seed information. Well-implemented uniform generators can be statistically indistinguishable based on outputs alone.

The 20 historical holdout draws were visible to us and are therefore a retrospective pseudo-holdout, **not a prospective live predictive claim**. The best 30-hit result is hindsight-selected, not an improvement over the random baseline. The correct takeaway is **no identified predictive model**.

## Reproduce
`python extra5_mass_algorithm_benchmark.py` followed by `python extra5_mass_algorithm_calibration.py`; requires Python 3, NumPy, SciPy, cryptography, matplotlib.

Files: `extra5_last100_data.csv`, `extra5_mass_algorithm_scores.csv`, `extra5_mass_algorithm_results.json`, `extra5_mass_algorithm_comparison.png`, and the runnable scripts.
''')
print(json.dumps(cal,indent=2))