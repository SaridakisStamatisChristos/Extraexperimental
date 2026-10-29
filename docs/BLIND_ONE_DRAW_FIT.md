# Step 12 — Seed one known draw, predict an undisclosed historical draw

**Training supplied by user:** #14248, Saturday 5 September 2026, ticket **13, 16, 22, 30, 31**, total columns **10,566** (context only, *not* seed material).

**Blind holdout:** consecutive draw **#14249**. No actual target result was consulted. The original result was already publicly published before this research; thus **evaluator-blind historical comparison**, not a truly prospective forecast.

## Source-supported versus hypothetical

**Documented family:** historical AES-192-CFB cryptographic generator described in Bikos et al., Cryptography 2023, DOI 10.3390/cryptography7040054. **Assumptions, not operator facts:** full-block CFB128, public SHA512 artificial index-to-key/IV mapping, zero input, continuous state from one draw to next, 24-bit rejection sampler, lexicographic combinadic unranking.

## Fixed protocol and outputs

Search seed indices 0 through 3,999,999 in increasing order. For each integer, compute SHA512 of domain-separated 8-byte big-endian seed; derive AES-192 key from bytes 0–23 and 16-byte IV from bytes 24–39. Encrypt zeros in continuous AES-CFB128. Consume successive 24-bit integers; reject values at least floor(2^24 / 324632)*324632, then unrank the residue to a five-number combination. Match the FIRST ticket exactly against #14248. Select the *lowest fitting index* without considering the second ticket.

**4,000,000 tested, 12 exact single-draw fits.** Under ideal independent uniform tickets, expectation is approximately **12.32** fits. First million produced zero; last three million produced 12.

**Chosen seed = 1,231,545**, exactly fits 13-16-22-30-31, second stream ticket **8-18-24-27-34**. This is locked for #14249 in a separate prior GitHub commit `f218295f669fd9d556328d8ec57b4c2d86399915`.

**All 12 fitting seeds produce 12 different second-draw tickets.** Therefore a single exact historical fit does not uniquely identify a secret seed or algorithm.

## Reproduction and safeguards

Run `python experiments/extra5_one_draw_seed_fit.py --seed-start 0 --seed-stop 4000000` after installing `cryptography`; eight local unit tests passed, including full combinatorial-rank enumeration. Recorded result: [extra5_blind_14249_fitting_seeds.json](../experiments/extra5_blind_14249_fitting_seeds.json). Reproduction must not look up #14249; ask user for hidden result, then append a *new* scoring record, never edit the pre-reveal commitment.

**No actual Allwyn generator configuration, keys, internal state, or prediction ability recovered. No CI added.**
