# Step 16 — Diverse algorithms fitted to the same two known consecutive draws

**User concern:** The initial two-draw checkpoint made a single primary guess from an affine modulo-rank formula; all five previously fitted AES/CAST/XOR artificial cryptographic-seed candidates failed to reproduce BOTH known consecutive results.

## Data contract and blind status

Known, user-supplied #14249 = **2,4,30,32,35** and #14250 = **2,5,9,30,33**. **Do not read draw #14251's result until after the model bank is committed.** This is retrospective evaluator-blind evaluation, not live prospective prediction.

We now construct nine explicit mathematical hypotheses that exactly reproduce the known transition by their declared mechanism or initial state. All are intentionally transparent toy surrogates; none is an identified lottery RNG. The nine models represent six structurally different transition families: affine congruential rank, multiplicative rank, XOR rank, independent circular offsets, completion of a 35-symbol permutation, and a two-state recurrence, plus a degenerate constant-state falsification control. The three affine settings are variants of **one** family, not three independent physical algorithms.

## Frozen predictions for hidden draw #14251

| Model | Class | Candidate #14251 ticket |
|---|---|---|
| `affine_rank_a1` | affine LCG | 2 – 5 – 15 – 30 – 34 |
| `affine_rank_a3` | affine LCG | 2 – 6 – 12 – 20 – 28 |
| `affine_rank_a5` | affine LCG | 2 – 7 – 11 – 14 – 32 |
| `multiplicative_rank` | multiplicative congruential | 2 – 3 – 12 – 21 – 22 |
| `xor_rank_two_cycle` | XOR state | 2 – 4 – 30 – 32 – 35 |
| `positionwise_mod35` | per-number circular shifts | 2 – 6 – 23 – 28 – 31 |
| `permutation_extension` | 35-symbol bijective permutation | 2 – 4 – 9 – 10 – 34 |
| `fibonacci_rank` | two-state modular recurrence | 3 – 12 – 15 – 17 – 23 |
| `constant_rank` | constant-output control | 2 – 5 – 9 – 30 – 33 |

**Primary policy remains unchanged:** Original choice `affine_rank_a1` predicted **2,5,15,30,34**, frozen in the [earlier immutable #14251 lock](../experiments/extra5_draw14251_LOCKED_before_reveal.json) at Git commit `53784da5327baa669b3c5c7889c0059dcd2c1c3e`. No winner selection from these nine after reveal is permitted. All other models are exploratory secondary comparisons.

**Verification:** Seven local Python tests passed for the full research prototype, including exhaustive rank/unrank across the 324,632 5-of-35 combinations; the compact GitHub reproducer independently expresses each hypothesis and rejects a missing fit. No CI was run. Script: [extra5_two_draw_multimodel.py](../experiments/extra5_two_draw_multimodel.py); fixed ledger: [extra5_two_draw_multimodel_predictions.json](../experiments/extra5_two_draw_multimodel_predictions.json); tests: [test_two_draw_multimodel.py](../tests/test_two_draw_multimodel.py).

**Inference:** An exact fit to two tickets is easy with flexible models, but 9 distinct third-draw forecasts cannot all be correct. This is evidence of structural **non-identifiability**, not breakthrough prediction. The true system might also reseed independently for every draw, making uninterrupted deterministic-state fitting invalid.

**Next:** User reveals only #14251 after this commit. Grade the original primary first, then show secondary candidate outcomes without selecting a retrospective winner. For actual historical RNG reconstruction, source-confirmed seed/IV mapping and sampler details remain the key missing constraints.
