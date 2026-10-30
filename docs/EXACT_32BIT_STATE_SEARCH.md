# Step 22: Exact inverse-state search for four consecutive EXTRA 5 draws

Research date 2026-10-30. The four user-provided tickets for draws 14249–14252 have lexicographic 5/35 ranks 55817, 57278, 268706 and 23073. They were not independently verified against operator records in this checkpoint.

Five invertible toy 32-bit word-output PRNG families were tested: two xorshift32 variants, two LCG32 variants, and an additive-counter SplitMix32-style fmix permutation. Three rank samplers were tested: top 24 bits, low 24 bits, or full 32 bits, using rejection modulo C(35,5)=324632 and lexicographic unranking.

Rather than searching arbitrary seed IDs, enumerate every first-accepted 32-bit output word compatible with ticket 14249, invert its 32-bit state and advance the same state without reseeding. Each 24-bit mapping admits 13056 first words; the 32-bit mapping admits 13230. Thus all 15 hypotheses jointly tested 196710 first-ticket-compatible words. There were no unresolved rejection runs within 1024 emitted words.

RESULT: exactly one state matched the first TWO tickets, none matched the first THREE or FOUR. The two-draw witness belongs to SplitMix32-style fmix with full-word sampling; first emitted word 414935513, preceding counter state 291627021. Its ranks are 55817 -> 57278 -> 216364 -> 59123, giving tickets 2,4,30,32,35 -> 2,5,9,30,33 -> 7,12,16,17,25 -> 2,5,18,22,26. It contradicts actual draw 14251, and is not a forecasting result.

Verification: locally executed a full Python research script (8 passing regression tests including all 324632 rank/unrank inversions), a separately implemented C++17 checker, and the compact Python reproducer. All gave 196710 first-compatible states, 1 exact pair, 0 exact triples, 0 exact quadruples. The committed compact script has four reproducibility tests. No CI was run.

Scope: exhaustive only for precisely the five defined 32-bit generator functions and three output-to-ticket transforms, not the real Allwyn cryptographic or physically reseeded system, other samplers or multistate generators. No production seed recovered and no predictive edge identified.


## Source archival correction (30 October 2026)

The prior checkpoint's complete reference scripts were absent from GitHub. A locally executed, standalone compact Python enumerator and two regression tests have now been added to the repository: [source](../experiments/extra5_exact_32bit_compact.py), [tests](../tests/test_exact_32bit_compact.py), [structured counts](../experiments/extra5_exact_32bit_compact_results.json). The independent C++ verifier and comprehensive test suite ran locally (C++ `SUMMARY|196710|1|0|0|0`, 8 Python tests); C++ and comprehensive test source files are also available as locally generated artifacts but are not claimed as committed in this checkpoint. No full-clone CI run. Also distinguish the [separate successful 96-bit xorshift 4/4 reconstruction](FOUR_DRAW_INVERSE_STATE.md): the present negative finding is confined to the specified 32-bit classes.
