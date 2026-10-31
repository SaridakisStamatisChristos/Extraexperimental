# Phase 3A — one-word combinatorial-rank inversion for GF(2)-observable generators

Date: 2026-10-31. Parent branch `research/inverse-64-hybrid`, parent commit at start `affd7d3579512bc18d7d15276ca23c1b5a40858b`.

## Exactly specified hypothesis

A persistent PRNG emits **one word per ticket**. That word is mapped to a zero-based lexicographic rank `r = word % 324632` and unranked to one unordered five-number combination. Optionally `gap=0,1,2` additional PRNG output transitions are consumed *after each ticket*. No rejection, overflow discard, reseed, collision retries, independent sampler, independent display state, or other variable consumption is assumed by the inverse solver. **The real installed EXTRA 5 mapping is not known to use this procedure**. The project tests mathematical hypotheses, not predictions.

The inverse applies to three **pinned models**:

- `marsaglia128`: 4 × 32-bit Marsaglia xorshift128 with shifts 11, 19, 8; emits new fourth word (32-bit). Bottom **3** bits are GF(2)-linear.
- `xoroshiro128plus`: two 64-bit words with rotation parameters 24, 16, 37, emits **pre-transition** `(s0+s1) mod 2^64`, including real nonlinear addition. Its lowest **1** bit is linear (XOR), not the higher bits.
- `xoshiro256plus`: four 64-bit words with xoshiro256 transition and emits **pre-transition** `(s0+s3) mod 2^64`, including real nonlinear addition. Lowest **1** bit is linear.

The `+` models are noncryptographic PRNGs; no secure-generator attack is claimed.

## Exact derivation

`N = binom(35,5) = 324632 = 8 × 40579` is divisible by 8, but not 16. Since `r ≡ word (mod N)`, the lowest three bits of `r` equal the lowest three bits of `word`, **as long as a word directly maps via modulo rank**. For a 64-bit addition output, bit 0 of `s0+s1` equals bit 0 of `s0 XOR s1`, regardless of carries. The PRNG state transition is GF(2)-linear. Hence the recorded unordered combination rank yields 3 or 1 *exact* GF(2) parity equations per ticket in the initial unknown state. We compute these forms on all unit-state vectors and solve them by full Gaussian elimination. Only a full-rank, full-ticket reverified state is labelled SAT. A dependent contradictory equation is model-specific UNSAT; remaining nullity is UNKNOWN.

This analysis does **not** apply to multiply-high rank mapping, continuous combinatorial bitstream mapping, non-power-of-two rejection when a word is discarded, or arbitrary hidden draw-dependent skips. The code implements a reference rejection-forward sampler but deliberately raises `NotImplementedError` in inverse mode when consumption paths are unknown rather than falsely marking them UNSAT.

For ideal uniformly distributed independent words, 32-bit rejection against the largest multiple of `N` discards `85936/2^32 ≈ 2.00e-5` words; 64-bit rejection discards `267360/2^64 ≈ 1.45e-14`. These are sampler probabilities, not experimentally established properties of EXTRA 5 and not guarantees against hidden skips or reseeding.

## Executed checks

`python -W error -m unittest -v test_rank_inverse.py` passes **7/7** tests:

- complete rank/unrank bijection for all **324,632** possible tickets, including the GitHub canonical first recorded rank;
- separate forward reference implementations for all three PRNGs, including genuine nonlinear addition;
- state-bit projection checks for deterministic and random seeds;
- **18/18** full **unrestricted** planted initial-state recoveries (3 generators × 2 gaps × 3 states); **1,800/1,800** continuation tickets replayed, including independent generator-output replay; 200 training tickets per 128-bit model and 335 for 256 bits;
- rank-deficient UNKNOWN, mutated ticket UNSAT, wrong-gap UNSAT, explicit variable-rejection inversion rejection.

`python benchmark_rank.py` reproduces `RANK_RESULTS.json`; individual end-to-end inverse times measured on the local Linux/Python 3.13 environment appear in JSON. Data generation occurs separately and is not included in the inverse timing; no claim of overall benchmark superiority is made.

## Authentic 2022 prefix (model-specific exclusions)

The GitHub connector supplied the authoritative file `experiments/extra5_five_year/extra5_2022_2026_authoritative.csv` (Git blob `eff4bdcb94a67bad95dd1a8e8da0e61354746d15`), and a *separate JS implementation* recomputed and verified all **3,526 lexicographic ranks** against the recorded five numbers. The independent Python parity solver was executed on an explicitly preserved transcription of the first **300 ranks**, enough for the earliest contradictions. See `REAL_LOCAL_AUDIT.json` for full XOR-dependency `0=1` certificates with listed row IDs.

The **nine** tested combinations (3 PRNG models × gaps 0,1,2) returned **UNSAT** by draw #10874–#11091 under the precise one-word modulo rank / continuous state / no rejection specification. This excludes only those pinned models, not entire PRNG families or other samplers. Original source CSV is not duplicated in this new folder.

The local container lacked a copy of the original 3526-row CSV, so the full-canonical local SHA256 path below was **implemented but not executed**. A GitHub repo checkout contains it and can run:

```
cd experiments/extra5_shuffle_inversion_fullgrid/phase3_rank
python -W error -m unittest -v test_rank_inverse.py
python benchmark_rank.py
python real_audit_rank.py --canonical ../../extra5_five_year/extra5_2022_2026_authoritative.csv --output REAL_FULL_AUDIT.json
```

**Evidence:** 18/18 recovered planted states, 1,800/1,800 held-out synthetic tickets, 9/9 exact model-specific contradictions with independent Python and JS agreement on earliest failing draw, no production state or predictive advantage. Real-world hypothesis status remains **UNKNOWN** overall.
