# Phase 3C — Exact online GF(2) rejection-path pruning

**Evidence status:** executable algorithmic result, with restrictions. No production RNG, sampler or seed identified. Prior Phase 3A/3B results are preserved. Date: 2026-10-31.

## Problem statement

Target precisely a one-word-to-lexicographic-combination-rank 5-of-35 sampler: each accepted PRNG word `w` maps to rank `w % 324632`, with rejection of `w >= floor(2^wordbits / 324632)*324632`. Allow a bounded total of `K` discarded words *within an early prefix* of `n` tickets. The number of discarded words **after that prefix is unrestricted** and follows exactly from forward replay. The hidden persistent initial state and rejection path are both unknown; the generator and fixed gap are explicitly pinned. Inputs are unordered combinations.

`online_path_solver.py` combines the exact linear projection of output low bits from Phase 3A with a depth-first search over the skip count before each accepted ticket. The DFS keeps a reversible GF(2) pivot basis. Every added ticket yields `proved_linear_low_bits` equations. A contradiction rejects **all** possible continuations of that partial skip path, not just one leaf. When all state bits become determined, exact rank/rejection replay immediately checks that unique state and stops at the **first** wrong rank. A witness is accepted only on full-ticket match with the exact sampler and a prefix rejection count within the declared bound.

## Completeness and soundness invariant

For a prefix of length `n`, skip count vector `(r_0,...,r_(n-1))` with nonnegative entries and total at most `K` corresponds to one of precisely `C(n+K,K)` possible paths. Every branch enumerates all remaining possible counts. If a necessary linear equation is inconsistent with the GF(2) basis, no state for **any** future suffix choices can match that branch. For full rank, only one initial state is possible; deterministic exact replay either certifies it or excludes the entire remaining subtree. A rank-deficient leaf, execution budget termination, or indeterminate replay is `UNKNOWN`, never `UNSAT`. The code maintains `pruned_leaf_path_multiplicity` equal to the number of ruled-out bounded paths; `UNSAT` additionally asserts that this equals `total_prefix_paths`. A SAT witness may be trajectory-equivalent to another pre-rejection state; it is not necessarily the original seed.

A candidate's early full replay uses integer combination ranks instead of reconstructing five numbers, which is **semantically equivalent** for an ordered lexicographic rank. This independent replay tracks exact rejected-word counts, checks accepted output modulo 324632, and consumes the fixed gap after acceptance. It does not assume the output is linear beyond the already proved low bits. Extreme replay-cycle safety cap yields `UNKNOWN` instead of a false exclusion.

## Executed results

- **29/29 local test methods**: 9 new online-solver tests, 13 retained Phase 3B tests, 7 Phase 3A tests. Covers exact synthetic recovery, out-of-sample replay, the first-rejection seed alias, forced later rejection, incomplete-rank `UNKNOWN`, imposed node-budget `UNKNOWN`, mutation falsification, and consistency with prior enumeration.
- Same-environment controlled comparison, Marsaglia xorshift128, first 60 authentic ranks, fixed gap=0, `K=3`: original Phase 3B solver **15.781266 sec** versus new online solver **3.007641 sec**, speedup **5.25x**. Both exhaust the same 39,711 paths and return bounded `UNSAT`. All runtimes local exploratory; no hosted CI.
- Expanded real-data test under **Marsaglia xorshift128**, fixed gap 0/1/2, first 60 authentic ranks with at most **4** rejected outputs in those 60 tickets: **635,376 / 635,376** paths each excluded by linear contradiction or unique-state exact replay; zero rank-deficient leaves. Individual measured runtimes **27.65, 28.71, 29.76 seconds**. This is **three additional conditional bounded exclusions** for the specified generator and sampler, NOT exclusion of the production RNG.
- The full canonical CSV was not copied to the isolated runtime: the frozen first300 fixture, previously transcribed from repository Git blob `eff4bdcb94a67bad95dd1a8e8da0e61354746d15`, was cross-checked directly against a fresh GitHub connector fetch of 3,526 records. The first300 ranks match a 64-bit FNV-1a digest `0x38c420afceb1967b`. This is independent prefix reconciliation, not independent re-verification of the canonical full-file SHA-256.

## Reproduce

From `experiments/extra5_shuffle_inversion_fullgrid/phase3_variable/`:

```bash
python -W error -m unittest -v test_online_solver.py
python -W error -m unittest -v test_variable_rejection.py
python -W error -m unittest -v ../phase3_rank/test_rank_inverse.py
python benchmark_online.py --prefix 60 --max-skips 4 --gaps 0 1 2 --output PHASE3C_REPLAY.json
```

The K=4 experiment is intentionally **not** part of the small unit-test suite. `PHASE3C_RESULTS.json` contains exact coverage counts, conditional assumptions, local timings, independent prior-solver comparison and fixture details. No historical full sweep was restarted.

## Open boundaries

Rejection rules consuming five distinct-number sampler words, collision retries, arbitrary skip rates, unknown per-draw reseeding, published xoshiro `++` / `**` nonlinear output functions and the actual operator's RNG remain `UNKNOWN`. `UNSAT` for K=4 says nothing about skip count >4 inside the first 60 records. The conventional 32-bit rejection probability is about 2e-5 per word, but this probability does not justify silently replacing a formal unbounded test with a bounded one. No future prediction has been claimed.
