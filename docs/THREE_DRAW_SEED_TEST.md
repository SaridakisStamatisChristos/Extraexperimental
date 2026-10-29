# Step 18 — Strict seeds for THREE consecutive known EXTRA 5 draws

## Three-draw input
- #14249: **2,4,30,32,35**
- #14250: **2,5,9,30,33**
- #14251: **10,18,21,25,29**

All user-reported; no operator publication verified in this step. The requirement is an **exact match on all three consecutive five-number tickets**, preserving one continuous generator state with the same seed; an exact first ticket or partial overlap is not a success.

## Seed-only experiments actually executed

1. **Historical generator-family reconstructions:** earlier exhaustive-in-range search attempted 1,640,000 public synthetic seeds across eight profiles (AES-192-CFB, DES-CFB, CAST-CFB, toy BBS/RSA, XOR and M/B mixers). Only **five** produced #14249; all five were replayed from their public initialization and their first **three** outputs decoded. **Five first-ticket exact / zero two-ticket exact / zero three-ticket exact.** No additional 1.64M full enumeration was executed in this step; the earlier complete candidate list was reused.
2. **New seed-only arithmetic controls:** 1,000,000 public integer seeds each for SplitMix64, xorshift64*, and a 64-bit LCG; outputs decoded with the same hypothetical continuous 24-bit rejection/combinatorial ticket sampler. **SplitMix64: 3 first matches, zero second/third; xorshift64*: 2 first, zero second/third; LCG64: 6 first, zero second/third.** These are *not* documented EXTRA 5 generator families.

**Total searched or replayed seed hypotheses: 4,640,000, with 16 exact first tickets, zero exact consecutive pairs, zero exact triplets.** The chance-based ideal-uniform expected exact triplets in that candidate count is only **1.36×10⁻¹⁰**; failure is the expected outcome.

## Algebraic seed-and-parameter fitting: two exact 3/3 examples

Map the three five-number sets to lexicographic ranks **55,817; 57,278; 268,706** modulo \(N=\binom{35}{5}=324632\).

- **Affine recurrence:** \(r_{t+1}=(194124r_t+204866)\bmod324632\), initialized with \(r_0=55817\), reproduces all three tickets. Its next *unseen* #14252 candidate is **13,16,21,26,32**. Because gcd(194124,324632)=28, this is not a full-period LCG.
- **Quadratic recurrence:** \(r_{t+1}=(r_t^2+81029r_t+315056)\bmod324632\) initialized with the same rank reproduces the same three known tickets. It proposes **3,12,17,18,33** for #14252.

These two are **post-hoc coefficient fits**: they solve for the transformation using the observed draws. They do **not** recover the deployed operator's cryptographic seed. Their incompatible fourth outputs demonstrate that even three perfect training matches do not uniquely identify an algorithm.

## Reproduce and evidence

Run from repository root:
```bash
python experiments/extra5_three_draw_seed_test.py --control-seeds 1000000
python -m unittest discover -s tests -p 'test_three_draw_seed_test.py' -v
```

Local original experiment: 3,000,000 arithmetic seed attempts completed, 8 regression tests passed, and archived five generator candidates were replayed; reproducibility source above is a compact equivalent. No CI. The local original executable and complete machine-readable output can also be downloaded from the conversation.

**Next:** Keep #14252 unknown. If testing the two newly fitted recurrences, do not adapt their coefficients after the reveal. For genuine cryptographic RNG attribution, obtain source-confirmed seeding, generator-selection and final 5/35 mapping rather than enlarging an arbitrary public seed search.
