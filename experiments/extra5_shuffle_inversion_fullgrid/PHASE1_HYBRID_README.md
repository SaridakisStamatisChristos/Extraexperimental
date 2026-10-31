# EXTRA 5 — Phase 1: exact 64-bit unordered state inversion

## Verified status

- Baseline `main`: `9934579a6f02fdb3557e0a5990e129825753a36b`.
- Research branch: `research/inverse-64-hybrid`.
- **10/10** independently planted 64-bit states recovered from unordered training ticket sets with exact state values; **1,000/1,000** held-back synthetic complete tickets independently regenerated.
- **40/40** tightly specified 64-bit xorshift/sampler/gap hypotheses returned fully enumerated UNSAT against a 132-ticket authentic historical subset. There are **36 rank-64** cases and **four rank-63** cases, with all residual state bits enumerated. The individual counts vary; read `PHASE1_HYBRID_RESULTS.json`.
- Production generator, secret state and future predictions **not recovered**.

## Algorithm and proof boundary

For a fixed-state 64-bit xorshift with either left/right/left or right/left/right transition, exactly five sequential selections without replacement from sorted values 1..35, no reseeding, and a constant optional inter-ticket output gap, the fourth selection is from **32 remaining values**. For modulo sampler its index is the lowest five state bits; for multiply-high sampler it is the highest five. An unordered published ticket admits a finite set of possible fourth indices, independently of its printed order. These indices become disjunctive linear GF(2) equations for the unknown state.

The engine chooses thirteen informative ticket indices, derives the rank and dependency syndromes, enumerates all allowed assignments, recovers GF(2) particular state solutions plus all free-bit variants, filters with sixty additional necessary domain constraints, then independently checks whole unordered tickets using the defined sampler. Complete finite enumeration justifies UNSAT only under the pinned hypotheses. Budget limit or inadequate rank yields UNKNOWN. Not covered: nonlinear generator output scramblers, collision/retry samplers, variable skips, cryptographic generators, per-draw reseeding, or modern deployment assumptions.

## Reproduction

Execute from `experiments/extra5_shuffle_inversion_fullgrid/`:

```bash
g++ -O3 -std=c++20 -Wall -Wextra -Werror inverse64_branch.cpp -o inverse64_branch
python -W error -m unittest -v test_inverse64_branch.py
python prepare_real_subset.py --output /tmp/extra5_real_sparse.csv
python run_phase1_grid.py --binary ./inverse64_branch --input /tmp/extra5_real_sparse.csv --output /tmp/extra5_grid_replay.json
```

`prepare_real_subset.py` reads the unchanged adjacent `extra5_five_year/extra5_2022_2026_authoritative.csv`, requires SHA-256 `61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307`, and writes 3,526 chronological positions, with only 132 observed tickets. Missing observations are zero-valued but do not reset or skip generator time. The subset was retrospectively selected for exact model falsification, **not** a forecasting holdout.

Generalized engine CLI: `DATA.csv TRAIN_LIMIT GAP [BRANCH_LIMIT] [EXTRA_CHECKS] [MAX_SELECTION_POOL] [A B C DIR HIGH]`. `DIR=0` for left/right/left; `DIR=1` for right/left/right; `HIGH=0` modulo; `HIGH=1` 64-bit multiply-high. The defaults are shift triple `13,7,17`, direction zero, modulo sampler.

For the older 83-file baseline when ZIP parts are available locally, separately run `bash assemble_archive.sh`, then `python -W error -m unittest -v test_lab.py` and `python audit_results.py`. **The old archive could not be downloaded into the network-isolated container this session**: original archive reconstruction and the old 12 regression tests were not rerun, and no existing CI ran. The **new six** regression methods passed locally, and a second 40-case grid run reproduced all complete-search classifications and exact count fields. The historical source datasets, existing prediction locks, old results and `main` were left unchanged. Logs and correction notes are in `PHASE1_HYBRID_RESULTS.json` and `docs/CONTINUATION.md`.
