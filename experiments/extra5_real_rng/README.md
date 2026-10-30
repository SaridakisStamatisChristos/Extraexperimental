# EXTRA 5 — Real-PRNG family reconstruction (599 training draws / five excluded)

**Research-only, 30 October 2026. This repository does not contain the operator's RNG.** This campaign tests **actual recurrence algorithms and actual sampler implementations**, not hot/cold/recency heuristics.

## Input and reproducibility

- `train_599.csv`: user-authoritative spreadsheet rows #13754–#14352, SHA-256 `cc2e3da23f5edab6f310f68a1204c00aa0113dcd38660b2e732346ce5cf9b8e4`.
- `holdout_5_PRIVATE.csv`: isolated #14353–#14357, read **only** by `score_holdout.py` after `lock.py` freezes forecasts. All five draw results were already public before the investigation; the holdout is reproducibly *retrospective*, not prospectively blind.
- First 400 rows used to select the timestamp/ID-seeded candidate; following 199 used exclusively to validate that selection. Every candidate is a fully specified `(generator, seed rule, sampler)`; there is no fitted hot/cold-number parameter.
- Run from this folder using Python 3.12+ with NumPy and SciPy; `recover_exact.py` requires system `libz3.so.4` (native Z3 SMT solver), a missing library must be reported as unverified, not assumed available.

```bash
python recover_exact.py --train train_599.csv --out exact_state_results.json --timeout-ms 12000
python exhaustive_six_training.py
python timestamp_prng_scan.py --train train_599.csv --out timestamp_scan_results.json --calibration 1000
python lock.py                  # create-once, refuses to replace a changed lock
python score_holdout.py         # ONLY NOW opens the five test outcomes
python -m unittest test_real_generator -v
```

## 1. Exact continuous-state recovery (native Z3 QF_BV)

The bit-vector equations implement concrete 32-bit LCG constants (Numerical Recipes, ANSI-style, Microsoft-style), Marsaglia xorshift32, xorshift96 and xorshift128. Output consists of consecutive **32-bit big-endian words**; each accepted 24-bit chunk represents a `0..324631` lexicographic rank with `raw % 324632`, rejection for `raw >= 16556232`. Each known ticket has precisely **51** permitted raw24 aliases. For the probed prefix, **no rejected chunks** are assumed.

These constraints are **exact for this specific model**, not for unspecified other byte order, word order, seed reset, physical entropy, rejection timings, or sampler. Status `unsat` means mathematically inconsistent within that model; `unknown` means solver timed out and **cannot** be treated as a disproof. All `sat` initial states are independently forward-generated and checked against the training prefix.

Observed first-window results from `exact_state_results.json`:

| Family | First 4 draws | First 6 draws | First 8 draws |
|---|---|---|---|
| LCG32 `(1664525, 1013904223)` | UNSAT | — | — |
| LCG32 `(1103515245, 12345)` | UNSAT | — | — |
| LCG32 `(214013, 2531011)` | UNSAT | — | — |
| xorshift32 `(13, 17, 5)` | UNSAT | — | — |
| xorshift96 `(16, 5, 1)` | SAT | UNKNOWN (12 s) | — |
| xorshift128 `(11, 19, 8)` | SAT | SAT | UNKNOWN (12 s) |

The first `4` training draws come from January 1–2, 2026; this is a **second non-overlapping window** relative to the October 2026 xorshift96 tests. `exhaustive_six_training.py` is an exhaustive, independent GF(2)-based xorshift96 inverse search for this January six-draw block, including arbitrary rejection of the fifth raw chunk. Exactly `51^4 = 6,765,201` no-initial-rejection four-draw states were enumerated, 26 fitted the fifth, **zero fitted the sixth**. Thus this particular continuously evolving sampler/state hypothesis cannot explain even six January draws, and automatically cannot explain the full 599-draw sequence. It does not disprove alternative rejection histories *among the first four draws* or model re-seeding.

A further attempt to extend the xorshift128 eight-draw SMT search to 45 seconds exceeded the host execution ceiling **without a result**. This remains **UNKNOWN**; do not report an UNSAT result.

## 2. Real PRNGs with reseeding at every scheduled draw

We implemented **eight concrete PRNGs**: Numerical Recipes LCG32, ANSI-style LCG32, 15-bit MSVC `rand` output, xorshift32, xorshift64*, SplitMix64, PCG-XSH-RR with fixed stream, and Python's seeded MT19937 implementation. The output is mapped through five explicit samplers: `rank32_rejection`, continuous `combinadic24`, `unique_mod35`, 5-step Fisher–Yates modulo, and 5-step Fisher–Yates with correct bounded rejection. We tested draw-ID, date, Unix time, XOR/addition combinations, and a small predeclared grid of clock offsets. **1,080** valid configuration combinations were evaluated on the 599-draw chronology. These are *timestamp/ID-derived seed guesses*, not recovered actual entropy or secret keys.

**Selection rule pre-fixed:** maximize the first 400 draws' *number-overlap total*. Stable enumeration breaks ties. Test the winner unchanged on the following 199 draws; do not select again on validation outcomes. Compare the maximum first-400 fit to 1,000 independent fair-lottery simulations, each including the same 1,080-model search. Main results:

- Selected concrete algorithm: `xorshift64star + epoch_second_xor_draw_id + fisher_yates5_modulo`.
- First 400: **325 total overlapping numbers**; null familywise maximum-search p ≈ **0.974** (no selection-stage evidence).
- Next 199: **140 overlapping numbers**, vs **142.14** uniform expectation; **0 exact five-number tickets**.
- No candidate generated two or more exact tickets among its 599 predictions. The maximum exact five-number fit from any of the 1,080 configurations was **one**, which is expected from a search this large.
- Fully prespecified forecast block #14353–#14357 saved in `algorithm_forecasts_LOCK.json`; SHA-256 `676feb8d46917bdf6ca6eb9fe7c3332cb6e4c7fc2847d9beec2862276a9d6180`.

## 3. Completely separate last-five scoring

The five predictions were made from the first 599 only, and then independently decoded by `score_holdout.py`:

| Draw ID | Predicted combination | Actual combination | Shared numbers |
|---|---|---|---:|
| 14353 | 6,13,20,26,35 | 3,5,22,24,29 | 0 |
| 14354 | 1,12,19,29,32 | 10,15,26,27,29 | 1 |
| 14355 | 2,5,10,32,35 | 4,14,15,19,27 | 0 |
| 14356 | 13,22,32,33,35 | 5,7,11,18,29 | 0 |
| 14357 | 4,15,17,20,21 | 3,4,6,10,22 | 1 |

Total **2/25** number-overlap hits; **0 exact five-number winning tickets**. Fair-lottery expectation: **3.5714** total hits, fixed-ticket one-sided `P(overlap >= 2)` ≈ **0.9053**. This is a **negative out-of-sample validation**, not evidence of predicting the operator.

## 4. Why even 599 chronological tickets cannot identify an unspecified secure RNG

Each *unordered* 5-of-35 ticket contains at most `log2(C(35,5)) = 18.3084456923` bits of information; 599 tickets supply at most **10,966.759 bits** about *any* fixed hidden state. Even if five numbers are genuinely recorded in original extraction order (not independently verified for this spreadsheet), the order-sensitive ceiling is `log2(35*34*33*32*31)=25.2153363` bits per draw, or **15,103.986 bits** total.

For illustration: under a uniformly distributed **19,937-bit** hidden state and a deterministic observation process, the *average* posterior state entropy is at least `19937 - 10966.759 ≈ 8,970 bits` given unordered tickets (chain rule and data processing inequality). This is **not** a proof about the actual EXTRA 5 RNG or the uniqueness of a particular observed transcript. Actual cryptographic RNGs may also incorporate fresh secret physical entropy, in which case there need not be any predictively useful relationship between future draws and old outputs.

The operator's published [2023 integrated report (p.104)](https://media.opap.gr/OPAPIntegratedReport202327082024.pdf) describes certified independent cryptographic systems for EXTRA 5, with independent secure generation and protection of number files. Its [current game description](https://allwyn.cy/en/games/extra-5/more-about/) confirms electronic RNG draws but gives no implementation, secret keys, seed or bitstream-to-ticket sampler. These sources **do not** authorize attributing any of the tested toy/simple PRNGs to production.

## Scientific verdict and scope

**EXACT STATE/SEED RECOVERY OF THE PRODUCTION GENERATOR: NOT ESTABLISHED. PREDICTIVE EDGE: NOT ESTABLISHED.** Four 32-bit continuous-generator branches are provably UNSAT for their first four January 2026 outputs under the assumed sampler; xorshift96's January branch is exhaustively falsified by sixth draw; xorshift128 eight-draw viability is not resolved. The independent timestamp-seeded PRNG search found no meaningful explanatory or predictive rule.

A true production reconstruction needs authenticated implementation/sampler/entropy evidence or repeated pre-reveal successes. Do not overinterpret retrospective holdouts, change historical locks, add CI, or claim an UNSAT timeout.
