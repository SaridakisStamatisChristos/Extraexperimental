# EXTRA 5 — Exact Inverse-State Engineering Laboratory

**Date:** 2026-10-30. **Status:** actual source code and executed numerical experiments; production RNG not identified.

This is a **generator-reconstruction algorithm suite**, not a frequency/pattern search. It attempts to determine the internal state of a hypothesized PRNG from the lottery's 5-of-35 output constraints. Each algorithm has a positive control with deliberately hidden parameters or internal state. Synthetic successes do not imply the real installed generator shares these mechanisms.

## Inputs and invariants

- Authoritative 3,526 draws, IDs 10832–14357, 2022-01-01 through 2026-10-29.
- Original CSV SHA256 `61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307`.
- One 5-number **set** corresponds to one of `C(35,5) = 324,632` lexicographic ranks, in `[0,324631]`.
- Recorded `n1,...,n5` order is **not established** to be original machine extraction order; direct-rank solvers are invariant to permutation, whereas the five-output solver has an explicit order assumption.

## Four mathematical inversion engines

### A. Exact parity projection from whole-ticket modulo reduction

When `rank = u % 324632` and accepted generator output `u` is a 32-/64-bit integer, `324632` is divisible by eight, giving three exact low output bits. For PRNGs with GF(2)-linear transitions, represent each output bit as the linear functional of the unknown initial state by propagating every basis vector. Solve via incremental Gaussian elimination over GF(2), and stop at the earliest contradictory draw. For nonlinear output addition (`xoroshiro128+`, `xoshiro256+`), only bit zero is used, which is exactly the XOR of operand bits.

`inverse_linear.py` tested 96 combinations: Marsaglia xorshift128 (2 shift families, 4 word locations, 8 strides), two xorshift64 variants (8 strides each), xoroshiro128+ (8), xoshiro256+ (8). **96/96 contradicted by draw 260**, max low-bit consistent prefix 259 (mostly the 256-bit models). This assumes one output word per ticket, fixed step gap, direct modulo mapping and no unmodeled rejected/skipped output in the analyzed prefix.

### B. Exact multiply-high interval inversion (64-bit and 128-bit state)

When `rank = floor(u * 324632 / 2^w)`, for `w=32` or `64`, the inverse preimage of an observed rank is exactly

```
lo = ceil(rank * 2^w / 324632)
hi = ceil((rank+1) * 2^w / 324632) - 1
```

Every binary **leading bit shared by lo and hi** is fixed throughout the interval. These bits become GF(2) equations for xorshift generator output words. Unlike a naive 32-/64-bit brute-force seed search, this recovers a state using only a few ranks if the generator structure is correct.

`inverse_interval.py` tested 160 configs: two Marsaglia128 parameter sets × four selected words × 16 fixed spacings, and two xorshift64 variants × 16 spacings. **160/160 contradicted by draw 9**. Planted 64- and 128-bit generators: recovered the **exact initial state** from the first 8 and 12 draws, respectively, then independently verified all 100 synthetic ranks.

The attack does not apply directly to nonlinear additive output scramblers (e.g., xoroshiro128+ output high bits) without a nonlinear solver; those were deliberately excluded.

### C. Five-output state inversion from a 5-of-35 sampler

If five successive PRNG outputs are used to choose numbers **in the recorded sequence** without replacement, then the *fourth* selected number is indexed among exactly 32 remaining numbers. Under modulo sampling it reveals **five low output bits**. A fixed stride of five outputs plus 0–8 possible unused outputs per draw produces linear equations for the state. For `+` output scramblers, use only bit zero.

`inverse_selection_fast.cpp`: **108/108 tested configurations contradicted by draw 260**. Positive controls recovered exact initial states and reproduced all 100 (Marsaglia128), 50 (xorshift64), 170 (xoroshiro128+) and 290 (xoshiro256+) complete synthetic ordered tickets. The slower `inverse_selection.py` is a second implementation.

**Critical limitation:** if the recorded order is a *secondary shuffle* unrelated to the selection order, the equations in this section are not justified. These negatives do not rule out that separate-shuffle architecture. If the sampler uses rejection with variable state advances, the fixed-spacing assumption can also be violated.

### D. Exhaustive unknown-parameter xorshift32 inversion under multiply-high

For a 32-bit xorshift whose emitted state `u` maps to rank `floor(u*N/2^32)`, the **first rank** confines `u` to an interval of 13,230 states (for the observed first draw). Enumerate that interval, both XOR shift-direction patterns, **all 31³=29,791** shift triples (1..31 each), and eight fixed spacings. This searches every state in the modeled first-output preimage without assuming an initial seed.

`invert_xorshift32_high.cpp` executed **6,306,158,880** second-rank candidate transitions, retaining **12,788** two-draw states and **zero three-draw states**. Independent Python `multiplyhigh_oracle.py` reproduced all **12,788** retained witnesses. The planted generator with unknown `(a,b,c)=(3,7,11)`, reverse shift direction, 7-word gap, and `0x6a5f1234` first output state was identified and reproduced **45 consecutive complete synthetic ticket ranks**.

## Results summary

| Model class | Candidate parameterizations | Genuine EXTRA 5 exact sequence | Planted controls |
| --- | ---: | --- | --- |
| GF(2) low-bit parity | 96 | all inconsistent by draw 260 | exact state recovered |
| High-bit interval inversion | 160 | all inconsistent by draw 9 | exact 64- and 128-bit states, 100 ranks each |
| Fourth-without-replacement output | 108 | all inconsistent by draw 260 | exact 64-, 128-, 256-bit states; up to 290 full tickets |
| Unknown-shift xorshift32, multiply-high | 476,656 shift-direction-gap parameterizations, each with 13,230 output states | 12,788 two-draw matches, **zero three-draw** | exact seed + shifts + gap, 45 ranks |

**Negative results are conditional on the source/output/sampler assumptions listed above; they do not prove the lottery cryptographically secure or disclose its actual generator.** The complete historical dataset has been reused in several earlier experiments, so no 2025/26 segment is a wholly untouched independent validation dataset for the overall research campaign.

## Reproduction

Requires Python 3.10+ and `g++`/`clang++` with C++17; no network, third-party libraries, GPU, GitHub Actions or cryptographic secrets needed.

```bash
bash reproduce.sh
```

`reproduce.sh` compiles and runs all inverse engines, checks frozen result equality and then executes 17 tests. On the tested container, full 32-bit parameter enumeration takes ~32 s, lowbit GF(2) ~23 s, highbit ~6 s, five-output C++ ~0.15 s. The individual test suite takes ~2 s. No CI configuration changes are required.

## Next algorithmic research

1. Develop an SMT/CSP state inversion backend for nonlinear scramblers and **multiply-high outputs** of xoroshiro/xoshiro (`+`, `**`) rather than incorrectly treating higher bits as GF(2)-linear.
2. Model **variable rejection counts and unknown per-ticket output consumption** using bounded, explicitly verified transition branches. Do not confuse a fixed-gap contradiction with general-family impossibility.
3. Build a set-valued finite-state sampler solver, supporting **unknown extraction order** and optional independent post-selection shuffle, so the output ordering ambiguity is represented rather than assumed away.
4. Use prior-year-only reconstruction followed by forward prediction on genuinely future draws, not post hoc fit. If a candidate actually recovers state, verify complete tickets and continue across many draws without resetting its seed.

All reported model counts are real executed configurations. The research identifies a functioning state-recovery technique and falsifies specific output mechanisms; **it has not generated trustworthy EXTRA 5 future winning numbers**.