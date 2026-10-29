# EXTRA 5 — Walk-forward fitting and forward draw checkpoint

**Experiment executed 29 October 2026, Europe/Athens.** The input archive ends on draw **#14355 (28 Oct, 19:00)**. The 29 Oct 15:00 draw #14356 is **not included**; the sealed forecast below is for **#14357 (29 Oct, 19:00)** and is deliberately **two-draw-ahead**.

## Goal and protocol

Fit an explicit family of mathematical sequence models to known unordered five-of-35 results and evaluate whether they generalize. This is not identified as the actual physical/cryptographic generator.

- Twelve prespecified models: uniform, smoothed frequency, three exponential-decay models, mean reversion (cold), two lag-2 conditional models, two neighbor-following models, and two ridge autoregressions.
- Models select 5 numbers by ranking marginal inclusion probabilities with deterministic tie breaking.
- Target IDs **14286–14315** (30 chronological one-by-one predictions) determine **which model to choose** by lowest mean multi-label Brier loss. Historical future outputs are never supplied to each model at prediction time.
- Evaluate that fixed selected model at targets **14316–14355** (40 further chronological predictions), refitting from the available prefix each time but keeping its hyperparameters fixed. In the two-ahead mode, data end two draw IDs before the evaluated target.
- The same procedure is also reported for one-step-ahead as a secondary exploratory check; no model was selected on the final 40 draws.

## Selected model and historical results

**Two-draw-ahead model selected by the tuning phase: `cold`**. It gives lower ranking priority to frequently occurring numbers, shrinking the probability estimate toward 5/35.

| Model | Early 30 hits | Later 40 hits (out of 200) | Later-40 mean Brier |
|---|---:|---:|---:|
| **cold** | 24 | 39 | 4.26607 |
| exp_20 | 13 | 26 | 4.33351 |
| exp_5 | 18 | 32 | 4.31296 |
| exp_60 | 15 | 25 | 4.34267 |
| frequency | 19 | 25 | 4.33517 |
| markov_10 | 16 | 28 | 4.38066 |
| markov_30 | 17 | 30 | 4.35366 |
| neighbor_15 | 19 | 29 | 4.47932 |
| neighbor_5 | 22 | 28 | 4.53365 |
| ridge_20 | 18 | 26 | 4.40526 |
| ridge_80 | 18 | 28 | 4.36371 |
| uniform | 22 | 33 | 4.28571 |

- The selected two-draw-ahead model achieved **39/200 individual overlaps**, against **28.571** expected for an independent uniform 5-of-35 draw.
- Conditional one-sided null tail for **this fixed 40-forecast series**: **p = 0.01885911** (hypergeometric convolution). This does **not** account for the researcher’s prior choice of the archive, horizon, model candidates, project history or noticing the unusual balanced period; treat it as exploratory.
- The selected one-step-ahead cold model had **37/200** overlaps, conditional one-sided p ≈ 0.047. The horizons are correlated and not independent confirmation.
- Multi-label Brier improvement is small: **4.2661 vs 4.2857** for the uniform model on the two-step 40-draw period.

## Immutable future-draw checkpoint

**Target #14357, scheduled 29 October 2026 at 19:00 Europe/Athens:**

```text
2 11 13 14 35
```

**Training stops at draw #14355.** #14356 is not used or predicted as if unknown at the time the draw happened. The prediction remains unchanged after its GitHub commit, irrespective of #14356.

Prediction record: [`extra5_draw14357_precommit.json`](../experiments/extra5_draw14357_precommit.json). The commit timestamp and SHA can be checked independently. No claim of winning is made.

## Why perfect historical fit is not algorithm identification

The accompanying script constructs a degree-≤99 polynomial over the prime field 524,287 that encodes all 100 archived five-number combinations **exactly**. Adding `c × ∏(x−draw_id)` does not change any of those 100 outputs but can force **any** desired next five-number combination by choosing `c`. Two constructed models fit all 100 observations and give mutually contradictory next draws `[1,2,3,4,5]` and `[31,32,33,34,35]`. This demonstrates that fitting alone does not recover a deployed generator.

## Reproduce

```bash
python -m pip install -r requirements.txt
cd experiments
python extra5_walkforward_fit.py --out .
python extra5_exact_fit_counterexample.py
cd ..
python -m unittest discover -s tests -p test_fit_prediction.py -v
```

## Next action

After #14357 has actually been published by the operator, read the public result, compare its five numbers with this GitHub-committed ticket, and append that outcome. Preserve the original prediction unchanged. Assess multiple genuine future draws before inferring an advantage. No CI.
