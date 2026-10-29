#!/usr/bin/env python3
"""Generate a cautious research note from executed synthetic seeded-sweep results."""
import argparse,json
from pathlib import Path
P=Path(__file__).resolve().parent

def render(data):
    best=data['best_train_selected'];post=data['best_holdout_posthoc']
    null=data['null_calibration']
    return f'''# EXTRA 5 — Expanded synthetic-seed reconstruction search

**Evidence category:** executed retrospective model comparison; not production-state recovery or a prospective forecast.

## Protocol

- Original dataset: 100 archived five-number results, draws #{data['draw_id_range'][0]}–#{data['draw_id_range'][1]}.
- Training scores: first 80 draws; **retrospective** pseudo-holdout: last 20.
- Prespecified public seed indices: **{data['seed_start_inclusive']}–{data['seed_stop_exclusive']-1}**, domain `{data['seed_domain']}`.
- Two illustrative per-draw seed policies: fresh deterministic entropy fixtures and chained-state fixtures.
- 31 historical-family generator routes and 2 **hypothetical** route switching schedules; three **hypothetical** 5-from-35 samplers.
- Every candidate is generated independently of the target lottery history, and both successful and rejected configurations are retained in a counted search ledger.
- Cryptographic primitives approximate documented **historical** source families. Keys, coupon records, physical entropy, production route switching and sampler are not known.

## Executed results

| Metric | Value |
|---|---:|
| Configurations attempted | {data['attempts']:,} |
| Completed full 100-draw replays | {data['completed']:,} |
| Failed bit-budget/other candidates | {data['failures']:,} |
| Best training-selected first 80 number overlaps | {best['train_hits_80']}/400 |
| That model's later 20 number overlaps | {best['holdout_hits_20']}/100 |
| Fixed-model later-20 upper-tail p (reference only) | {data['train_selected_fixed_model_holdout_upper_tail_p']:.5g} |
| Best post-hoc later-20 number overlaps | {post['holdout_hits_20']}/100 |
| Search-calibrated p for post-hoc best | {null['familywise_plus_one_p']:.5g} ({null['max_score_exceedances']}/{null['replicates']} null histories) |
| Exact five-number ticket matches in later 20 | {data['total_exact_tickets_on_holdout']} across all completed models |
| Expected number of exact tickets under independent uniform ticket model | {data['expected_exact_tickets_under_iid_null']:.3f} (correlation ignored) |
| Expected overlapping numbers per model in 20 fair draws | {data['null_fixed_holdout_expected_individual_matches']:.4f} |
| Seed scores CSV SHA-256 | `{data['scores_csv_sha256']}` |

Best training-selected model: `{best['operation']}({best['sources']})`, seed index `{best['seed_index']}`, policy `{best['seed_policy']}`, schedule `{best['schedule']}`, sampler `{best['sampler']}`.

Best **post-hoc**, selected directly using the later draw results: `{post['operation']}({post['sources']})`, seed index `{post['seed_index']}`, policy `{post['seed_policy']}`, schedule `{post['schedule']}`, sampler `{post['sampler']}`.

## Interpretation and limits

- A seed index is an index into a **made-up public seed derivation scheme**, not a candidate for a known operator key/seed space.
- The supposed holdout results were published before the study and are therefore not true forward validation. The stronger a search over many seeds, the easier coincidental high overlap becomes.
- Exact-match counts must also be judged against the search volume. With {data['completed']:,} configurations and 20 draw IDs per model, coincidence can produce complete matches even for perfectly random, independent lotteries.
- The calibration replays the **entire fixed candidate library** against each simulated 20-draw history and takes the maximum. Model correlation is preserved, but assumptions about independent uniform lottery draws and fixed model configurations remain.
- A properly entropy-seeded CSPRNG cannot generally be identified or cloned from the final five-number outputs without its secret state or additional implementation disclosures. The exact 2026 Allwyn generator is not identified.

## Reproduction

From the repository root after installing `requirements.txt`:

```bash
cd experiments
python extra5_seed_sweep.py --seed-start {data['seed_start_inclusive']} --seed-stop {data['seed_stop_exclusive']} --null-replicates {null['replicates']} --out .
python extra5_seed_sweep_report.py --results extra5_seed_sweep_results.json --out ../docs/EXPANDED_SEED_SWEEP.md
python -m unittest discover -s ../tests -p 'test_*.py'
```

No CI has been added. The comparison is a defensive reproducible research experiment, not a strategy for selecting winning numbers.
'''

if __name__=='__main__':
    a=argparse.ArgumentParser()
    a.add_argument('--results',type=Path,default=P/'extra5_seed_sweep_results.json')
    a.add_argument('--out',type=Path,default=P.parent/'docs'/'EXPANDED_SEED_SWEEP.md')
    args=a.parse_args()
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(render(json.loads(args.results.read_text()))+'\n',encoding='utf-8')
    print('Wrote',args.out)
