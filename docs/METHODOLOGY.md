# Methods, null models and interpretation

## Null hypothesis

Each draw is an independent uniformly random five-element subset of numbers 1..35. There are
`C(35,5)=324,632` possible unordered winning sets. For an individual number `P(present)=5/35=1/7`.

For a specific pair, `P(both present)=C(33,3)/C(35,5)=C(5,2)/C(35,2)=10/595`.

Given an independently generated candidate ticket and the historical draw, their overlap `K` follows `Hypergeometric(N=35, successes=5, sample=5)`. Thus `E[K]=5*5/35=5/7`, or `20*5/7=14.2857` matches across 20 independent draws.

### Aggregate frequency correction

Counts of the 35 labels within a draw are negatively dependent due to sampling without replacement. For the 35-category Pearson statistic, a factor of `34/30` accounts for the variance structure. See scripts for the exact statistic and p-value calls; the chi-square approximation applies across many draws.

### Bit-to-number mapping

Tested intentionally faulty `b`-bit modulo reduction and duplicate rejection against published frequencies. The mapping `x % 35` is uneven when `2^b` is not divisible by 35; observed discrepancy can reject such a concrete mapping assumption. It does **not** identify whether a real system uses modulo and rejection, a shuffle, combinatorial unranking, or any particular RNG family.

### Candidate simulations

- Artificial seeds derived deterministically from public constants **not** learned from outcomes.
- The benchmark runs 60 generator families × five samplers × 32 seeds for most / eight for slow number-theoretic toy examples = 9,360 configurations.
- A configuration emits 100 tickets aligned by draw ID, starting with draw #14256. A score is the sum of matching numbers at the same IDs, out of 400 picks in the first 80 and 100 in the last 20.
- **Selection:** choose the best configuration by *first 80* scores only, then report the *later 20* score. The later draws were already publicly known during the study, so it is a *retrospective pseudo-holdout*, not a forward forecast.
- **Post-hoc multiple testing:** report the maximum over all 9,360 on the later 20 separately and correct by the distribution of the maximum over a fixed candidate library, measured using 3,000 null simulated outcome histories.
- The 9,360 configurations are correlated; a naive best-one p-value is invalid. The Monte Carlo recalibration reuses the fixed candidate predictions.
- Validation priority: prospective (pre-committed) unseen future draws, ideally with preregistration.

### Reproducibility boundaries

Cryptographic historical components are **illustrative**. The BBS/RSA toy variants are not secure, and AES/DES variants do not recreate the full undisclosed mixing/seeding architecture. Distributions produced by correctly implemented cryptographic generators are expected to be indistinguishable from fair lottery outputs without secret internal information. More arbitrary candidate seeds mostly increase the chance of hindsight matches.

### Validation limitations

Draw data were transcribed from third-party result pages. A source-level audit needs original draw IDs, actual time zones, raw number order if meaningful, timestamps and versions. Avoid extrapolating an observed p-value from one retrospectively chosen window to evidence of corruption or predictability.

The archive intentionally distinguishes *executed historical simulation*, *analytic derivation*, and *unresolved assertion*. No algorithm recovered the deployed RNG state.
