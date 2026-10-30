# EXTRA 5 — Shuffle-Invariant Exact PRNG State Reconstruction

**Research date:** 2026-10-30. **Status:** executable verified inverse-state algorithm; deployed EXTRA 5 RNG remains unidentified.

## Key advance

For an unordered five-number draw from 1..35, a sequential without-replacement sampler makes selections from 35, 34, 33, **32**, 31 available numbers. If the fourth selection is obtained as `PRNG_word % 32`, the fourth output word's low five bits disclose the selection index. We **do not know the extraction order**. Rather than assume the spreadsheet's order is raw, enumerate all 120 possible selection orders and retain every admissible fourth-selection index, typically 5–8 of 32 indices.

If the PRNG state transition is GF(2)-linear (e.g. a 32-bit xorshift recurrence), each of those five emitted bits is a linear function of the unknown initial state. We solve the resulting **set-valued disjunction of linear systems** via exact depth-first Gaussian elimination over GF(2). At full rank, reconstruct every compatible 32-bit state and forward-verify **all five selected numbers** and all subsequent draws. At the prefix limit, enumerate all residual free-state assignments (subject to a documented work cap), and declare the model eliminated **only if the exhaustive flag is true**.

This is an **exact solver** for the stated family: every seed that could have generated the modeled draw sequence must satisfy its fourth-selection constraints, and every final candidate is checked against the full observed tickets. It does not assume any relationship between the extraction order and published display order.

## Scrambled outputs

For `word = state * m mod 2^32`, with **odd known multiplier** `m`, the fourth index is `word mod 32`. Since `m` is invertible modulo 32, translate every allowed fourth-index `j` into an allowed raw-state index `j*m^{-1} mod 32`, recover the initial state using linear equations, and verify using the actual complete 32-bit scrambled output. This makes the solver useful for a specifically defined multiplicatively scrambled xorshift family without incorrectly treating multiplication as GF(2)-linear.

## Executed evidence

- Authoritative sequence: **3,526** consecutive draws, #10832–#14357; dataset SHA256 `61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307`.
- Systematic xorshift32 `(a,b,c)∈{1,…,12}³` and fixed outputs-per-ticket `stride∈{5,6,7,8}`: **6,912/6,912 exhaustive configurations**, **zero initial states reproducing the observed full sequence**. Every model was tested on the first twelve draws to constrain state, with forward verification against all available tickets. Exactly 5 selections are made from 35,34,33,32,31; any extra stride outputs are discarded between draws.
- Three distinct known odd scramblers, 50 predetermined shift triples, strides 5..10: **900/900 exhaustive configurations**, **zero states reproducing the observed full sequence**.
- **Nine synthetic positive controls:** three different shift triples, different fixed spacings, scrambled and unscrambled outputs; recovered the exact planted initial 32-bit state and reproduced **60/60 complete synthetic tickets** in every control.
- **10 independent regression tests passed**, including all 6,912+900 frozen search entries and independent Python reference sequences.

**Scope limits:** The sweep does not cover all 31³ shift triples for every stride, or the actual deployed RNG, unknown generator changes, per-draw reseeding, nonlinear state transitions, variable rejection skips, or alternative samplers. The original draw order is not assumed to be raw selection order. The historical data are not an untouched prospective test across the wider research campaign.

**Interpretation:** No trustworthy real next-draw predictor or production state recovered. Elimination of a specified model is not evidence that the lottery is unbreakable in principle.

## Reproduce

Requires Python 3.10+, C++17 compiler, and no third-party Python dependencies for the core solver/tests.

```bash
bash reproduce.sh          # compile, prepare inputs, run 10 tests; quick
bash reproduce.sh --full   # additionally rerun the 6,912-grid and 900-scrambler sweeps
```

Main artifacts:

- `unordered_attack.cpp`: exact GF(2) disjunctive state enumeration, plus full-ticket verification; explicit output budget and `exhaustive` flag.
- `inverse_unordered_sampler.py`: independent Python generator / fourth-index reference.
- `prepare_unordered.py`: canonical dataset transformation and synthetic positive controls.
- `sweep_grid.py`, `sweep.py`, `sweep_star.py`: deterministic parameter sweep and reproducibility.
- `test_reconstruction.py`: rigorous cross-language regression tests.
- `grid_results_{1_2,...,11_12}.json` and `star_sweep_results.json`: complete frozen evidence.
- `smt_inverse.py`: exploratory nonlinear 128-bit SMT prototype using `libz3.so.4` directly. **Not a successful 128-bit inversion**—solving realistic 128-bit instances timed out; the exact 32-bit solver does not depend on this prototype.

No model parameter was fitted to 2025–2026 for the main search. Since every tested real-data model is eliminated by the prefix, there are no production-generator holdout predictions to evaluate.
