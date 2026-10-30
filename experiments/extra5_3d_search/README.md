# EXTRA 5: Three-dimensional set × order × time reconstruction search

**Status:** Executed and independently checked. No deployed RNG reconstructed; no reproducible advantage over fair 5-of-35 predictions. October 30, 2026.

## What “three dimensions” means

- **Set:** winning five-number combination, recorded as a lexicographic rank in 0..324631; candidate output is a five-number set.
- **Permutation:** 0..119 Lehmer rank of the published sequence relative to that same ticket's sorted numbers. Candidate output is a permutation, optionally computed from a *shared* or independent PRNG stream.
- **Time:** chronological draw index, scheduled local day/15:00-versus-19:00 slot, and optionally previously revealed draw information.

This is not a 3-D spatial visualisation: it is a joint hypothesis space over three observable/conditional variables. The recorded sequence is **not confirmed** to be the machine's original extraction order.

## Research arms

1. **Full affine inversion:** All `3 × 2 × 120³ = 10,368,000` integer triples for `permutation=(a*X+b*T+c)%120`; three X definitions (current set, preceding set, preceding permutation); two T definitions (draw id and date ordinal). Fit 2022–24; freeze six rules; score 2025–26. Current-set rules are *post-draw conditional* analysis, not usable for pre-draw lottery forecasts.
2. **Nonlinear 3-way interaction:** 12 binary set features × 8 binary permutation features × 8 binary time features = 768 interactions; 1,000 whole-family permutation-null replicates; selected interaction replay on 2025–26 with 5,000-shuffle independent testing.
3. **Joint one-step PRNG hypotheses:** 8 generator recurrences × 14 seed rules × 9 offsets × 5 combination samplers × 4 permutation methods = **20,160 configurations**. Seed rules include previous set, previous relative permutation, second-previous set and next scheduled time. Candidate generates both a five-number set and a 5-of-5 permutation, using a shared stream, independent permutation stream, or canonical sorted control. Training selects three different objectives; future configurations fixed before evaluation. Forecast *of each next draw* is allowed to use the already revealed previous draw. It is **not** an unconditional thousand-draw forecast.

All 3,526 user-provided consecutive archived draws #10832–#14357 were reconciled. Train: 2,192 draws (2022–2024). Later: 730 draws (2025) and 604 (2026). Later periods were already studied in other EXTRA 5 experiments; this is only an **execution-level** chronological holdout, not a truly novel untouched independent test or prospective observation.

## Key numerical results

- Best affine training match: **45/2,192** exact permutations. 48 independent-shuffle full-search null experiments completed (the intended 80-replicate call reached its execution limit); 23/48 yielded a maximum of at least 45, plus-one estimate **24/49=0.489796**. Do not report 80 as executed.
- Best later-year affine rule: **14/1,334** permutations, chance expectation **11.1167**, one-sided fixed-model p **0.228878**.
- Best three-way train interaction: correlation **+0.070233**, full-family maxT p **0.517483**; later-year correlation **−0.037596**, two-sided p **0.169766**, no directional replication.
- Best train joint PRNG candidate: **7** historical 4/5+ occurrences; only **2** on 1,334 subsequent draws, **0** exact five-number tickets, **0** 4/5+ cases with matching permutation rank. A fixed fair-ticket predictor has p(≥2 4/5+) **0.128667** over 1,334 draws. Searching 20,160 configurations readily produces multiple development rare-event winners.
- The three frozen joint objectives yielded **2, 2, 1** later-year 4/5+ events, respectively; all three yielded **0** 5/5 and **0** 4/5+ with matching permutation rank.
- All selected C++ forecasts independently reproduced by a separate Python implementation: **4,002/4,002**.
- All 20,160 C++ generator configurations checked twice against the Python oracle: **40,320/40,320**, no mismatches.
- **15 regression tests passed**.

## Source integrity and an important corrected defect

`extra5_2022_2026_authoritative.csv` SHA-256:
`61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307`

The independent oracle detected a genuine parsing bug in the first joint-PRNG fit: an untrimmed CRLF marker prevented reading the final `prev2_set_rank` column. The original invalid run is preserved in `invalidated_parser_run/` (DO NOT cite it as final evidence). `joint_generator3d.cpp` now trims CRLF and the whole search/frozen forecasts/evaluation were regenerated. Final corrected model selection and 40,320-differential check pass.

`future_features_only.csv` deliberately excludes the current `perm_rank` and the recorded `n1..n5`. It does include the *current combination* so the conditional-shuffle research can test relationships after the set is known. The **joint generator seed function does not read the current combination**; it uses previous draws and public time fields only. Those previous-draw fields include actual previous outcomes within 2025/26, so forecasts are **one-step ahead only**.

## Reproduction

All code and original dataset are bundled. Linux/macOS with Python, NumPy/SciPy, and g++ C++17 recommended.

```bash
bash reproduce.sh
```

The reproduction script regenerates train/future partitions, executes affine and joint selection, independently replays all selected forecasts, recreates the 40,320-case fixture, and runs 15 regression tests. It also reruns the 768-feature/1,000-replicate full-family nonlinear interaction calibration. It checks existing prediction/model locks for byte-level drift. The 48-replicate *large affine* null test is preserved, but intentionally not repeated by default: it is CPU-intensive (~5 seconds/rep on the tested machine) and the planned 80-replicate run timed out. To reproduce that partial null separately use `./null3d train_labeled.csv 48 20261030 null_48_replay.csv` and compare against `null_48_partial.csv`.

## Unresolved

A direct uniform ordered-selection process and a uniform set followed by an independent uniform shuffle generate the same observable ordered outcomes, with probability `1/38,955,840` for each ordered ticket. Their architectures cannot be statistically distinguished by this archive alone. None of the tested candidate recurrences or joint models is identified as production; prediction accuracy has not exceeded chance after correcting for search and repeated prior exploration.
