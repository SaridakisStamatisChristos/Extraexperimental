# Technical Report — EXTRA 5 Exact Shuffle-Invariant Inversion

**Run date:** 2026-10-30  
**Status:** Locally executed and independently replayed; **production generator not identified**.

## Result

| Measure | Modulo sampler | Multiply-high sampler | Combined |
|---|---:|---:|---:|
| Xorshift32 transition/parameter/gap configurations examined | 297,910 | 297,910 | 595,820 |
| Fully enumerated by seven informative observations | 124,990 | 124,990 | 249,980 |
| Additionally fully enumerated by eight observations | 19,450 | 19,450 | 38,900 |
| **Fully enumerated (union)** | **144,440** | **144,440** | **288,880** |
| Underconstrained/unresolved | 153,470 | 153,470 | 306,940 |
| Maximal-period settings (all fully evaluated) | 1,620 | 1,620 | 3,240 |
| States matching first full draw **and selected necessary constraints from the first 100 draws** | 3 | 0 | 3 |
| Those also matching the second full draw | **0** | **0** | **0** |

The 595,820 models are not 595,820 statistically independent searches. These are **parameter/sampler specifications**, not production RNG candidates confirmed by evidence. The rows for 306,940 unresolved specifications are **not falsification results**.

All 3,240 maximal-period xorshift32 configurations (`324` transitions × `5` output gaps × `2` samplers) met the exhaustive-coverage condition and failed. Maximal period was verified algebraically by establishing that seed 1 has a cycle of exactly `2^32-1`, using the complete prime factorization `3·5·17·257·65537` and repeated squaring. This is a **conditional exclusion** of the specified state transition and sampling architecture, not an exclusion of all good-quality PRNGs.

### Count details

The two seven-observation searches enumerated `4,046,874,704` possible index-assignment branches each. The two eight-observation stages enumerated `3,383,950,560` branches each. This totals about `14.86 billion` **candidate fourth-index assignment branches** across both samplers/stages, **not** that many distinct PRNG seeds or draws. Linear dependency checks, four additional index constraints, and exact forward ticket replay prune these branches.

Three modulo-model states survived the chosen index constraints and matched the first unordered historical draw. Their specification/initial-state pairs are stored in `RESEARCH_RESULTS.json`; all three failed the second draw. The multiply-high model found no such survivors. Each is only a **historical-consistency** result, because several observations beyond the first two were already imposed as necessary constraints. No predictive power is claimed.

## Independent controls

Six planted xorshift32 configurations were generated with different hidden seeds, shift triplets and output gaps under the **modulo** sampler. The exact same six combinations were independently generated under the **multiply-high** sampler. All 12 inverse runs recovered the **precise original 32-bit state**, and Python independently regenerated **all 60 of 60 complete five-number sets** for each run. A rank-31 planted case is included to guard against incorrectly rejecting an underdetermined linear system.

The original five-year CSV was verified against its preserved SHA256 `61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307`. For every one of **3,526** actual draws, the unordered set bitmask matches the five numbers in the canonical CSV. Python independently recomputes the exact possible fourth-selection mask for the real and synthetic data. Every C++ source compiles with `-Wall -Wextra -Werror`; `12/12` Python regression tests pass with resource warnings treated as errors.

## Completeness theorem (conditional)

**Claim.** Let `T` be a particular xorshift32 transition, `g` the fixed number of additional output steps between tickets, and `S` either one of the specified five-output selection samplers. If a seven- or eight-observation model is marked `enumerated=1`, then every initial state consistent with the selected historical sets is represented by at least one compatible fourth-index assignment and corresponding recovered candidate state; every such state is subsequently filtered using four additional **necessary** constraints and fully replayed. Therefore no skipped state could explain the entire observed history when the exhaustive forward checks reject all candidates.

**Proof.** For draw index `d`, the fourth emitted generator word is `T^(d(5+g)+4)(s)`. Because `T` is linear over `GF(2)` and `S` uses either the bottom or top five bits of the fourth word for its size-32 choice, the observed fourth index is an exactly known 5-row linear transformation of the 32-bit initial state `s`. The published unordered set constrains that index to a finite set `A_d`, obtained by choosing each possible fourth number and every preceding three-number subset. Any state that produces the observed five-number set must therefore satisfy **one of** these enumerated assignments. The implementation enumerates the Cartesian product of allowed assignments for selected observations. For `enumerated=1`, their binary observation matrix has rank at least 31. Gaussian elimination and dependency syndromes reconstruct every compatible particular solution; its nullspace has dimension at most 1 and both values are enumerated. Four further fourth-index observations are necessary conditions, so filtering on them cannot discard a truly matching state. Remaining candidates are simulated with `T` and `S`; an exact mismatch conclusively rules out that state. QED **within the stated model**.

The proof does not apply when `enumerated=0`, to a varying output gap, to a changed mapping, or to an unknown per-draw state input. The observed sequence can be explained by many distinct machines; an actual production mechanism cannot be identified from these exclusions alone.

## Experimental 64-bit attempt

`smt_inverse64.py` uses `libz3.so.4` directly through `ctypes`, expresses the fourth-selection observations as exact 64-bit XOR parity constraints, and supports synthetic known-seed controls. The bit-level linear forms were independently checked against 64-bit xorshift iterations. With 35 chosen observations, Z3 returned **UNKNOWN (timeout)** after 10 seconds both for a planted synthetic generator and the actual 2022 prefix. No 64-bit state was recovered, **and no 64-bit configuration was falsified** in that experiment. This is preserved so later work can improve the solver instead of mistaking timeouts for proof.

## Open research questions

1. Recover states of 64/128/256-bit word generators from unordered-set constraints with scalable nonlinear/SMT or meet-in-the-middle techniques. The baseline currently times out even on planted 64-bit instances.
2. Model variable output consumption from rejection sampling, retries, and number-collision elimination, rather than assuming exactly five words plus constant `g` per ticket.
3. Validate whether candidate generator architecture and sampler could persist between draw events; model reseeding separately and avoid assuming it away.
4. Obtain a truly untouched later sequence for forecasting after a candidate mechanism/state has been fixed. Historical interpolation, later-year retrospective parameter fitting, and constraints selected with knowledge of the answer cannot be presented as future prediction.

**Bottom line:** An exact, shuffle-invariant 32-bit state-inversion engine has now been implemented and verified across two samplers, with strong conditional exclusions. We have **not solved or predicted EXTRA 5**.
