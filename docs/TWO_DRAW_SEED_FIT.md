# Step 15 — Consecutive two-draw seed fit and frozen third-draw challenge

User-provided consecutive EXTRA 5 results from **5 September 2026**:

| Draw | Ticket |
|---|---|
| #14249 | 2, 4, 30, 32, 35 |
| #14250 | 2, 5, 9, 30, 33 |

Actual #14250 was revealed **after** the previous multi-family blind prediction was committed; that primary AES prediction **4,6,19,27,31** scored **0/5**. Of the other four precomputed alternatives, two scored 0 and three scored 1? **Correct complete histogram across all five:** two scored **0**, three scored **1**. Never reselect retrospectively.

## A. Uninterrupted state, no reseeding: archived historical-family test

The previous independently reproduced **1,640,000** synthetic-seed trial evaluated AES-192-CFB128, DES-CFB64, CAST-CFB64, toy BBS and RSA parity, XOR(AES,DES), M(AES,BBS), and B(BBS). It identified **five** seed configurations that reproduced the first draw exactly. This checkpoint **independently replays those five** and compares their second uninterrupted ticket with #14250:

| Generator | Synthetic seed | Second ticket | Hits |
|---|---:|---|---:|
| AES-192-CFB128 | 43315 | 1, 10, 22, 25, 27 | 0 |
| AES-192-CFB128 (preselected) | 236403 | 4, 6, 19, 27, 31 | 0 |
| CAST-128-CFB64 | 78501 | 1, 14, 24, 30, 31 | 1 |
| CAST-128-CFB64 | 251682 | 11, 23, 27, 30, 31 | 1 |
| XOR(AES,DES) | 29267 | 9, 16, 19, 26, 32 | 1 |

**Zero seeds match both tickets exactly within that previously enumerated 1.64M-index search space.** This checkpoint did NOT perform another complete 1.64M-index sweep. The prior enumeration and its recorded candidate completeness are the input evidence; the five candidates were recomputed from initialization.

Under an ideal independent uniform 5-of-35 toy model there are **324,632** tickets, so an ordered pair has **105,385,935,424** possibilities and 1.64M random seed hypotheses yield an expected **0.00001556** exact pair matches. Zero is the overwhelmingly expected outcome; it does not refute real historic cryptographic generator families.

## B. A single state-transition formula that fits both observed draws exactly

For a deliberately simple **new surrogate algorithm**, map each sorted five-number combination to its lexicographic rank 0..324631. The two ranks are:

- #14249: **55,817**
- #14250: **57,278**

Fit a modular affine state transition:

\[
r_{t+1}=(a r_t + c)\bmod 324632.
\]

Fix **a=1** by the rule "smallest positive multiplier". The two training ranks then give **c=1,461**, so both known draws are fitted **exactly**, without per-draw manual adjustment. Projecting one further step gives rank **58,739**, ticket **2, 5, 15, 30, 34** for previously unrevealed #14251.

This is an **interpolator**, not a historically documented lottery PRNG. Alternative multipliers **a=3** and **a=5** likewise fit both draws perfectly but predict respectively **2,6,12,20,28** and **2,7,11,14,32**. Even a two-draw exact fit therefore does not identify the true process.

**Important pre-reveal GitHub lock:** [extra5_draw14251_LOCKED_before_reveal.json](../experiments/extra5_draw14251_LOCKED_before_reveal.json), original independent commit **53784da5327baa669b3c5c7889c0059dcd2c1c3e**. Do not alter this lock after result release.

## Reproducibility, limitations and next checkpoint

- [Reproducer](../experiments/extra5_two_draw_replay.py) and [recorded results](../experiments/extra5_two_draw_replay_results.json), with [tests](../tests/test_two_draw_replay.py).
- Executed locally: **nine** tests for the expanded two-draw implementation (including all 324,632 ranks), **five** tests for the compact GitHub reproducer. The compact script independently replays every archived matching seed; no CI run.
- All cryptographic keys, physical seeds, production code, reseeding schedule, CFB segment lengths, 5/35 sampler, and actual operator generator state remain **unknown**.
- **Next:** Ask the user for #14251 only after this frozen commitment; score the fixed a=1 prediction first, then the a=3/5 alternatives as retrospective diagnostics. Do not select whichever succeeds post-hoc. Repeat across independent concealed triplets before any predictive claim.
