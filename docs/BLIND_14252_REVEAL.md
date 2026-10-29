# Step 19 — Draw #14252: result versus locked three-draw recurrence models

User-revealed result for historical EXTRA 5 **#14252**: **1, 7, 9, 14, 18**. Source is the user's report; this evaluation did not independently check an operator-published draw record.

The original pre-reveal [prediction lock](../experiments/extra5_draw14252_THREE_DRAW_FIT_LOCK.json) is preserved **unchanged**. It contained two explicit models fitted to #14249, #14250 and #14251.

| Pre-reveal model | Frozen five-number output | Matching numbers | Score |
|---|---|---|---:|
| **Primary** affine rank recurrence | 13, 16, 21, 26, 32 | none | **0/5** |
| Secondary quadratic rank recurrence | 3, 12, 17, 18, 33 | 18 | **1/5** |

The primary had been selected by the fixed *lowest polynomial degree* rule before the result; the secondary is a comparison only and must not be retroactively promoted to primary.

Both recurrences reproduced the preceding three known draws *by construction*, because adjustable coefficients were solved using all three. The next-draw mismatch shows that this historical fit is not evidence of a correct reconstruction of the real EXTRA 5 generator.

## Implications and next checkpoint

- **Seed-only historical-family search:** the earlier 1.64 million synthetic hypotheses contained no seed matching even two consecutive tickets; an additional 3 million arithmetic-PRNG toy seed hypotheses contained no exact two- or three-ticket state matches. This is a finite search over **artificial seed/key mappings**, not a disproof of any real production cryptographic RNG.
- **Free-parameter recurrence fitting:** a perfect 3/3 training fit is not a successful forecast. Primary blind 0/5; quadratic secondary 1/5.
- **No evidence of live Allwyn keys, physical-entropy seed, true sampler, deployed generator version, or forecasting advantage.**

For further work, prioritize an independently documented seed/initial-state transformation and the real five-number sampler, and test a *fixed model* across independent concealed historical sequences without revising it after misses. Never overwrite pre-reveal locks.

[Machine-readable evaluation](../experiments/extra5_draw14252_blind_evaluation.json). No CI added.
