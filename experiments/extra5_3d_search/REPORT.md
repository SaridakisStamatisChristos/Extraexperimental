# EXTRA 5 — three-dimensional search research report

**Date:** 2026-10-30  
**Status:** EXECUTED_LOCAL; no proof of deployed generator, secret state, or future prediction advantage.

## 1. Observable model and the three axes

For each draw t, let `S_t` denote the unordered five-number winning set, `Π_t` the permutation of its elements in the workbook's recorded sequence, and `T_t` the scheduled time/draw index. The observable ordered sequence is `Y_t=Π_t(sort(S_t))`. The empirical archive has 3,526 consecutively numbered tickets for 2022–October 29, 2026. Number rank belongs to `0..324631`, permutation rank to `0..119`.

Two competing generation architectures are:

A. `G(state_t) → five ordered distinct numbers`;

B. `G1(state_t) → unordered combination`, then `G2(state'_t) → permutation`.

A and B are *observationally equivalent* when both are unbiased: `P(Y=y)=[C(35,5)*5!]^-1=1/38,955,840`. For a nonuniform set mechanism `p(S)`, direct ordered generation can still reproduce any independent-uniform-shuffle distribution via `p(Y)=p(sort Y)/120`. Therefore this research tests specific couplings and cannot prove the architectural distinction from the output sequence alone.

## 2. Three-dimensional affine inversion

All 120³ combinations `(a,b,c)` were evaluated for each of six `(X,T)` pairs: X=current combination rank (conditional analysis), previous combination rank (one-step input), or previous recorded permutation rank (one-step input); T=draw index or date ordinal. `Π_hat=(aX+bT+c) mod 120`. The first 2,192 draws fit parameters, with six winning rules frozen before the later 1,334 labels were opened by `evaluate.py`. Total parameter combinations `6*120³=10,368,000` (many mathematically equivalent; NOT 10 million statistically independent algorithms).

Development winners: 43,43,45,43,44,41 exact relative-permutation matches in six families, respectively. On 2025+2026: 10,14,13,13,6,9, respectively. Chance expected for any one fixed rule is `1334/120=11.1167`; the best later-year 14/1334 yields one-sided binomial p **0.228878**. Other models do not exceed a compelling fixed-model threshold either.

The original planned 80 null replicates were interrupted at 48 due execution time. Each of the 48 *complete* null experiments permuted observed development permutation labels while preserving number/time features and replayed the entire six-family 10.368M search. In 23, the maximum exceeded or equaled 45. Plus-one p=`(23+1)/(48+1)=0.489796`. This is preliminary-resolution Monte Carlo, yet clearly inconsistent with the observed winner being a dramatic breakthrough. No invented remaining 32 runs.

## 3. Nonlinear 3-way dependence search

For 12 independently specified binary set properties, eight recorded permutation properties, eight time properties, we tested `12*8*8=768` standardized interaction correlations. Training winning feature triple: `(set_sum>=90) × (evening slot) × (smallest selected number displayed first)`. Absolute correlation `0.0702326446`; 1,000 simulated nulls each shuffled the entire permutation feature matrix together and repeated the maximum over all 768 interactions; exceedances 517; familywise p=`518/1001=0.517483`.

The same fixed feature association in 2025–2026 had correlation `−0.0375962` (opposite direction), with two-sided independent 5,000-permutation p=`0.169766`. It did not replicate. These tests assess detectable conditional dependence, not proof of direct versus separate-shuffle architecture.

## 4. Actual three-axis next-draw generator hypotheses

New candidate library: 8 distinct PRNG recurrence variants; 14 seed derivations (including prior set, prior permutation, second-previous set, publicly scheduled minute and combinations); nine offsets; five number samplers; four permutation policies, shared stream versus independent stream versus canonical sorted control. Total **20,160** fully specified tuples; 2,191 one-step development targets (first row omitted because it lacks prior data). Each tuple emits a *five-number set and its relative permutation*.

Train selects separately: max 4/5+ count; max total matching numbers; max joint 4/5+ with matching permutation rank. Results are saved in `FROZEN_JOINT3D_models.csv`; the second stage writes `FROZEN_JOINT3D_future.csv` using only prior revealed outcomes/schedule, not current result. Third-stage evaluator then opens `sealed/future_labels.csv`.

| Selected objective | 2022–24 4/5+ | 2022–24 total hits | 2025 4/5+ | 2026 4/5+ | 2025–26 exact 5/5 | 2025–26 4/5+ AND permutation pattern |
|---|---:|---:|---:|---:|---:|---:|
| Rare ≥4 | 7 | 1,631 | 0 | 2 | 0 | 0 |
| Total number hits | 1 | 1,689 | 2 | 0 | 0 | 0 |
| Joint ≥4 and correct permutation | 2 | 1,523 | 0 | 1 | 0 | 0 |

The leading rare-event hypothesis is `xoroshiro128plus, minute_control, offset=0, rank32_rejection, same_stream_rank`. Its two 2026 4/5 successes were draws **#14137** (predicted 8,19,20,23,34 vs actual 8,16,19,20,34) and **#14293** (22,23,24,27,29 vs actual 11,23,24,27,29), both with mismatching relative-permutation ranks.

The chance probability of at least two four-number-or-better overlaps for a **single fixed predictor** on 1,334 independent fair draws is `0.128667`. `E[overlap totals]=1334*(25/35)=952.857`; leading rare candidate observed 977, while the number-hit selection observed 970. These modest excesses do not establish RNG reconstruction, especially given earlier searches and the retrospective nature of the evaluation.

For 2,191 independent fair draws, a fixed unbiased predictor has probability `P(at least 7 4/5+)≈0.00009284`. When evaluating 20,160 predetermined configurations, **the expected number of configs achieving at least seven is ≈1.87 by linearity of expectation** (not a familywise p-value). The near-miss search maximum is therefore not implausible. No full joint-library max-statistic null p-value was computed in this run; avoid claiming one.

## 5. Exact independent verification and correction

The independent `oracle_joint.py` reimplements PRNG recurrences, seed transformations, bounded combinatorial sampling, repeated-ball selection, Fischer–Yates selection and relative-order sampling in Python, separate from `joint_generator3d.cpp`. It independently reproduced **4,002/4,002** pre-evaluation frozen later-year predictions (zero mismatches), and **40,320/40,320** smoke fixtures across *all* 20,160 configurations on two reference records, including each of the eight generator families, 14 seed rules, nine offsets, five set samplers and four permutation modes (zero mismatches). Fifteen regression tests pass.

The first joint run had a genuine CRLF parsing bug: the last `prev2_set_rank` feature failed to parse in C++, producing an erroneous lag-two seed and an incorrect secondary training winner. Independent oracle caught 1,334 mismatches in that model. The offending run and wrong labels are saved under `invalidated_parser_run/`, explicitly excluded from scientific findings. The corrected C++ parser strips `\r` from CSV fields. All selected models, predictions, scoring and independent differential fixtures were regenerated and passed with zero mismatches. The corrected secondary winner is `xoshiro256starstar,prevsum_xor_minute,+3600,rank32_rejection,same_stream_rank`.

## 6. Validity and limitations

- Recorded workbook order is not confirmed to be the underlying machine's extraction order; an extra shuffle, direct extraction, or format conversion may all be consistent with the observations.
- The chronological 2025+2026 split is execution-isolated for this new experiment, **but those years have been used extensively in the earlier EXTRA 5 campaign**. Not genuinely blind, not prospective, no honest claim of validated forecasting edge.
- Previous outcomes from within later years are allowed as *previous-draw* seed inputs, meaning the joint experiment scores **one-step-ahead** rules, not an unconditionally frozen 1,334-ticket forecast made before 2025. `future_features_only.csv` contains previously revealed outcomes and also current sorted sets for the separate conditional shuffle arm. The joint generator's seed uses only prior data.
- Configurations share mathematical operations and some generate duplicate streams. Counts are parameter tuples, not independent algorithms, and the user should not view them as 10M+ entirely unrelated approaches.
- Exhaustive searches here cover only affine modulo-120 permutation relationships and specifically listed PRNG/seed/sampler policies; they do not search every possible generator or recover the actual production RNG/state.
- No full-search calibrated null p was generated for the 20,160-config one-step library, only analytic individual-model chance calculations and exact out-of-development evaluation.
- The fixed 5/35 chance of a 4/5+ event is `151/324632 ≈ 0.000465142`; one draw's full five-number exact chance is `1/324632`. Relative order matching on a given ticket is `1/120` under independent uniform order.

## 7. Verdict

**Three-dimensional search completed and falsified a broad class of simple set/order/time couplings.** Strong development maxima are explained by extensive model selection, and neither algebraic rules, nonlinear interaction features, nor joint shared-stream PRNG hypotheses produced reproducible complete tickets or stable 4/5+ behavior. The shuffle hypothesis remains possible but not identified from tickets alone. Further evaluation must use newly observed future locked predictions and reliable raw order/extraction evidence; more retrospective model variations alone cannot establish the deployed mechanism.
