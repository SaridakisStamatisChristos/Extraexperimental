# EXTRA 5: forensic audit of bitstream-to-number mappings

**Analysis date:** 29 October 2026  
**Evidence:** published cumulative frequency totals for **14,353** draws, with 71,765 number appearances.  
**Source:** https://numerics.gr/extra-5/statistika-arithmoi ; https://numbers.gr/extra-5 .  
**Reproduction:** `python extra5_sampler_forensics.py` (Python standard library only).

## Research question

Can the publicly recorded five-element subsets identify how the internal pseudorandom bits are converted into five integers from 1 through 35?

**Partially:** a specific incorrectly biased conversion can be excluded. It is not possible, from uniformly distributed five-element subsets alone, to distinguish between multiple correctly implemented samplers with the same output law, nor to identify the cryptographic primitive or secret seed.

## Candidate mapping

Given b random bits, form `x % 35 + 1`. Ignore duplicate numbers and keep drawing until five distinct values have been selected. Let `q=floor(2**b/35)`, `r=(2**b) mod 35`. Numbers 1..r have weight q+1; numbers r+1..35 have weight q. Conditional on no duplicate, the probability of choosing a remaining number is proportional to its weight.

A small exact dynamic program computes the distribution of the number of selected labels in 1..r for each draw. For `N` independent draws, the sum has mean N times per-draw mean and variance N times per-draw variance. The z-tests below use a normal approximation (N=14,353).

| Source bit width | Heavier labels | Observed appearances | Candidate expectation | z versus candidate | Approx. two-sided p |
|--:|--|--:|--:|--:|--:|
| 8 | 1–11 | 22,721 | 24,530.98 | −15.21 | 2.94e−52 |
| 10 | 1–9 | 18,506 | 18,892.67 | −3.49 | 4.78e−4 |
| 16 | 1–16 | 32,827 | 32,815.77 | +0.09 | 0.929 |
| 32 | 1–11 | 22,721 | 22,554.71 | +1.42 | 0.155 |

**Interpretation:** The specific naive 8-bit modulo mapping with duplicate rejection is dramatically inconsistent with observed data. An exploratory 10-bit variant also disagrees. The published aggregate data do not distinguish the 16- and 32-bit modulo candidates from uniform sampling (and cannot establish that either is in use).

The core 8-bit test predates any claim that this is an actual OPAP method. It is a falsifiable hypothesis about an implementation error; **it does not demonstrate a security flaw in the deployed system**.

## Why matching frequencies is not enough

An unbiased rejection sampler, a correct partial Fisher–Yates shuffle, and exact combinatorial unranking all assign each unordered five-element subset probability exactly `1 / C(35,5) = 1 / 324632`. If individual draws are independent, **all possible recorded draw histories have the same probability under all three methods**. No amount of final-number data can uniquely identify which was used.

Moreover, the historical hybrid eLottery architecture described by Bikos et al. (2023) derives generator inputs in part from physical randomness and the hash of the closed bet file and supports dynamically changing among BBS, RSA/Rabin, DES and AES-based sources. This is a description of the historical design, not verification of the current production version.

Peer-reviewed paper: https://doi.org/10.3390/cryptography7040054 .

## Next observations that would add information

1. **Full ordered draw history**: Compare draw order (if available, not the sorted published set) and positional ranks for deviations from uniform order. Ranked-position tests reveal biased ordering, not which of multiple unbiased algorithms was used.
2. **Chronological independence**: Compare overlap of successive five-element subsets with the exact hypergeometric distribution, including autocorrelation, runs and change-point tests. Use a preregistered test battery and correct for multiple testing and window selection.
3. **Source implementation evidence**: Retrieve archived generator specifications or certification reports giving the bit-to-range mapping, draw-order publication format, reseeding/entropy schedule and exact implementation revision.

## Scope and limitations

- This run used 35 published frequency totals, **not** a full chronological draw-by-draw archive.
- Tests assume independent draws and uniformly distributed input b-bit values for the candidate mapping. These assumptions are specific to the tested hypothesis.
- Candidate comparisons were devised during exploration, so marginal p-values for exploratory variants should not be treated as preregistered discovery thresholds.
- No exploitation, seed reconstruction, future prediction, RNG compromise or evidence of rigging has been demonstrated.