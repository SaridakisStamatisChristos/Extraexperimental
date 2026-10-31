# Phase 2B — Unordered xorshift128 inversion on a 64-dimensional state subspace

**Date:** 2026-10-31. **Scope:** precisely specified conditional experiment, not reconstruction of the EXTRA 5 production RNG.

## Model and exact limit

- Marsaglia xorshift128, 4 × 32-bit words, with state transition and output defined independently in the C++ and Python files.
- The unknown initial state is `(x,y,0,0)`, where `x` and `y` are arbitrary 32-bit words. **Only 64 of the 128 initial-state bits are unknown**. This is a restricted initialization hypothesis, **not an algorithm for recovering an unrestricted 128-bit state**.
- Exactly five outputs per ticket, independent fixed gap 0 or 2 after the fifth, and removal from a sorted 1–35 list using either `word % remaining_count` or `floor(word * remaining_count / 2^32)`.
- Tickets are treated as **unordered sets**. The C++ inversion receives NO internal extraction indices or artificial true seed.
- Observation at the fourth removal is a set-valued five-bit linear constraint on `(x,y)`. `inverse128_subspace.cpp` uses the existing Phase-1 GF(2) rank-guided index-assignment inversion and exact full-ticket replay. Branch exhaustion is required to call `UNSAT`; truncated branch enumeration remains `UNKNOWN`.
- The inference is complete **only in the restricted 64-dimensional initial-state subspace and the pinned sampler, transition, gap and search budget**.

## Executed verification

- 3 independent 64-bit subspace seeds × 2 samplers × 2 gaps = **12/12 exact planted-state recoveries**, from 500 unordered synthetic tickets each.
- Independently generated, held-out ticket continuations: **1,200/1,200 exact sets** across the 12 cases (100 each). The synthetic oracle is a separately written Python recurrence.
- Every planted search achieved rank 64, reported `SAT` after exhausting all enumerated index assignments, and returned the exact original 64-bit initial-state parameter.
- Measured search time across 12 cases (local environment, C++20 -O3): approximately **0.25–1.32 seconds per case** (excluding fixture generation / compilation).
- Negative controls: full arbitrary 128-bit state outside the defined subspace returns `UNSAT` **for the subspace model**, mutated ticket returns `UNSAT`, and a deliberately limited search returns `UNKNOWN`. They do NOT refute the unrestricted generator.
- 4/4 Phase-2B regression methods pass, along with the earlier 8/8 Phase-2 and 6/6 Phase-1 tests in this execution environment. No existing production data or prediction lock was modified.
- Authentic subset based on `prepare_real_subset.py` from Phase 1, preserving chronological indices, 132 of 3,526 observations, source dataset SHA-256 `61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307`. Six pinned subspace models (two samplers × gaps 0/1/2) all returned exhaustive `UNSAT`, with 5,038,848 assignments each. These exclusions **do not apply** to a general initial 128-bit state, reseeding, alternate samplers or different generator transitions.

## Reproduction

From this directory:

```bash
g++ -O3 -std=c++20 -Wall -Wextra -Werror inverse128_subspace.cpp -o inverse128_subspace
python -W error -m unittest -v test_subspace.py
python benchmark_subspace.py --output P2B_RESULTS.json
```

For the *optional* real-data subset, first reconstruct it with the unmodified canonical dataset and original selection script, from the parent experiment directory:

```bash
python prepare_real_subset.py --output phase2_linear/subspace128/real_sparse.csv --extra-rows 130
cd phase2_linear/subspace128
python benchmark_subspace.py --real real_sparse.csv --output P2B_RESULTS.json
```

The CSV and synthetic training data are **generated inputs** and are not checked in. The original 83-file archive remains preserved independently. Regression tests work without the original archive; the optional real check requires the canonical CSV from the existing repository.

## Methodological limitations and next gate

An unknown unrestricted 128-bit initial state remains **UNKNOWN**. The prior full-state xor-aware SMT probes returned `UNKNOWN` due to timeout. The new subspace result is a concrete bridge between 64-bit exact inversion and higher-state machines, not evidence that the lottery uses this artificial zero-padded initialization.

The next research target is genuinely unrestricted 128-bit recovery from unordered tickets. The first exploratory necessary-prefix constraints for the multiply-high sampler were algebraically formulated but did not solve planted full-state probes within the measured budget. Investigate stronger correlated constraints from all five removals, SAT parity management, and independent forward replay; never promote any timeout to a model exclusion.
