# EXTRA 5 — 599/5 strict-input holdout study (2026-10-30)

## Objective and data-provenance contract

**Question:** fit a forecasting algorithm to all user-authoritative 2026 draws except the last five and assess it on precisely those five. The authoritative workbook is `extra5_2026.xlsx`, whose independently normalized CSV is already preserved in the project. No claim is made that spreadsheet columns D–H are actual extraction order. This study uses **unordered** tickets.

- **Training**: 599 consecutive draws #13754–#14352, 2026-01-01 15:00 through 2026-10-27 15:00.
- **Quarantined retrospective holdout**: five draws #14353–#14357, 2026-10-27 19:00 through 2026-10-29 19:00.
- **Primary metric**: log probability assigned to each true 5-of-35 combination, summed across the test.
- **Secondary metric**: number of matches between each fixed five-number ticket and its corresponding draw; and inclusion-probability Brier score.
- **Baseline**: exact independent uniform 5-of-35 ticket law, each ticket probability 1/C(35,5)=1/324632.
- **Fitting restrictions**: `forecast.py` and `challengers.py` have no access to `holdout_5_PRIVATE.csv`; they accept only `train_599.csv`. Predictions were written to two immutable-by-program local JSON lock files and their SHA-256 hashes fixed in `evaluate.py` prior to execution of that evaluator.
- **Crucial scope limitation**: The wider research project had previously accessed outcomes through #14357. This is a *retrospectively quarantined* exercise, NOT a genuinely prospective or untouched holdout and it is not independent of earlier candidate-family design choices. The filenames `LOCK` document the local execution order, not pre-reveal timestamp proof.

## Model and algorithm

Each candidate assigns 35 positive number weights `w_i` from earlier draw frequencies, smoothed recency counts, mean reversion, previous-ticket repetition/avoidance or date/clock-matched history. The probability of an unordered ticket `S` is

\[
P_w(S)=\frac{\prod_{i\in S}w_i}{e_5(w_1,\ldots,w_{35})},\qquad
 e_5(w)=\sum_{|T|=5}\prod_{i\in T}w_i.
\]

`e_5` is evaluated by dynamic programming in O(35×5) operations, not by approximating normalization. The primary ticket is the top five marginal inclusion odds, with SHA-256 deterministic tie-breaking; additionally, an *independent product-weighted sample* is frozen for each future draw using an exact DP subset sampler.

For cumulative cold-number models, the model estimates

\[
f_i=\frac{\#\{t\in\text{training prefix}:i\in S_t\}}{5n/35},\qquad
w_i=(1-\alpha)+\alpha\max(0.05,2-f_i).
\]

Two fixed *walk-forward validation folds*, indices `[200,399)` and `[399,599)`, are scored using only the prefix available before each validation target. The 18 candidate model definitions are fixed in `forecast.MODELS`. The evidence-gated primary selection rule accepts a nonuniform model only if **both folds individually improve on uniform by at least `log(3)` nats**; otherwise it selects uniform. This is a conservative heuristic, **not** a formally calibrated multiple-testing threshold. Two challengers are also frozen: best nonuniform by total training-fold log score; and best model with strictly positive gain in both folds, if distinct.

The five future tickets are produced **without any updating from the five holdout draws**, as the user requested. For a fixed cold-number weight vector this correctly results in the same five-number primary ticket at all five horizons; changing it after seeing holdout draws would be leakage.

## Training-only model selection

| Model | First validation fold log advantage | Second validation fold | Combined |
|---|---:|---:|---:|
| Uniform | 0 | 0 | 0 |
| Cold, α=0.35 | −0.07055 | +0.89839 | +0.82784 |
| Cold, α=0.15 | +0.23181 | +0.51203 | +0.74384 |
| Recency half-life 120, α=0.15 | −0.60348 | −0.65131 | −1.25479 |
| Hot, α=0.15 | −0.61830 | −0.70182 | −1.32013 |

None of 17 nonuniform candidates qualified under the primary two-fold strength gate. **Primary selected model: uniform.** Best nonuniform: **cold α=0.35**; positive-both-folds challenger: **cold α=0.15**. These nonuniform gains are small and not independently calibrated for the many model choices historically explored.

## Five frozen forecasts versus five actual results

| Draw | Actual | Primary uniform-control ticket | Primary hits | Cold α=.35 and α=.15 ticket | Cold hits |
|---|---|---|---:|---|---:|
| #14353 | 3 5 22 24 29 | 7 10 17 22 26 | 1 | 2 5 6 26 28 | 1 |
| #14354 | 10 15 26 27 29 | 22 23 29 32 35 | 1 | 2 5 6 26 28 | 1 |
| #14355 | 4 14 15 19 27 | 16 21 22 25 31 | 0 | 2 5 6 26 28 | 0 |
| #14356 | 5 7 11 18 29 | 3 10 12 29 31 | 1 | 2 5 6 26 28 | 1 |
| #14357 | 3 4 6 10 22 | 1 7 13 15 21 | 0 | 2 5 6 26 28 | 1 |
| **Total** | | | **3** | | **4** |

## Quantitative score and falsification

| Measure | Uniform-control | Cold α=0.35 | Cold α=0.15 |
|---|---:|---:|---:|
| Matches across five tickets | 3 | 4 | 4 |
| Joint likelihood ratio against uniform | 1.0000 | 1.16455 | 1.06857 |
| Mean 35-number marginal Brier loss | 4.285714 | 4.278189 | 4.282399 |
| Tail P(≥observed matches), fixed tickets under iid fair draws | 0.731399 | 0.494688 | 0.494688 |
| Full winning tickets | 0 | 0 | 0 |

Under iid uniform 5-of-35 draws, fixed predictions yield `25/35=0.7142857` expected number matches per draw, hence `25/7≈3.5714` matches across the five forecasts. The exact single-ticket overlap law is hypergeometric `P(K=k)=C(5,k)C(30,5-k)/C(35,5)`; the five-draw tail is computed by exact convolution. Since the two cold challenger tickets are identical on all five draws, **they are not independent confirmation**. A 1.16455× likelihood ratio across just five draws is extremely weak evidence.

## Independent checks and executed tests

`python -m unittest -v test_holdout.py` reported **15 passing tests**, including: independent brute-force equality for the elementary symmetric-polynomial normalizer on bounded instances; independently enumerated ticket-probability normalization; exact marginal-probability sum of five and ordering; training data hash and chronological schedule; modification of future training records not altering earlier model weights; 1200 seeded uniform-subset sampler runs; full replay of the challenger-selection artifact; exact retrospective result reproduction; refusal to overwrite an existing prediction lock; and correct hypergeometric null probabilities.

**Predictions lock SHA-256**: `82f4208666c56b56fd7cdd27f56a4b937ac3cbdfcd072f6b83a438de22521561`.

**Challengers lock SHA-256**: `a3d75cb35324e6150d5425fa534d0aa68009b5f5e818134951926f189bdc414c`.

**Training CSV SHA-256**: `cc2e3da23f5edab6f310f68a1204c00aa0113dcd38660b2e732346ce5cf9b8e4`.

## Reproduce (Python 3 plus numpy; no CI)

```bash
cd experiments/extra5_599_5
python -m unittest -v test_holdout.py
python forecast.py --train train_599.csv --lock /tmp/extra5_primary_replay.json
python challengers.py --train train_599.csv --lock /tmp/extra5_challengers_replay.json
python evaluate.py --test holdout_5_PRIVATE.csv --primary predictions_LOCK.json --challengers challengers_LOCK.json --out /tmp/extra5_599_holdout_replay.json
```

The fit programs refuse to overwrite an existing lock. Compare the replayed JSON payloads against committed records (their hashes are stable given identical input bytes and Python/numpy behavior); `evaluate.py` explicitly checks the original locked-file SHA-256 before evaluating.

## Scientific disposition

**Algorithm produced and tested; deployed generator remains unknown.** In five retrospective draws the cold-number candidate achieved one more number match than checksum-controlled uniform selection, but neither the hit count nor the likelihood score supports predictive superiority. The current Allwyn RNG's secret state and sampler remain unidentified; this model is a statistical ticket law only. Better-looking retrospective tickets cannot establish a forecasting edge without genuinely future-locked prospective observations. Existing locked predictions are preserved; this experiment does not add CI.
