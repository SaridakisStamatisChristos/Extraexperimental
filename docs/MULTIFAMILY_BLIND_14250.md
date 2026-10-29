# Step 14 — Multi-family blinded historical seed-fit test, EXTRA 5 #14249 → #14250

**Date of analysis:** 29 October 2026. **Blind target:** #14250; **DO NOT LOOK UP OR INCLUDE ITS ACTUAL NUMBERS UNTIL AFTER THE PRE-REVEAL LOCK**.

The first single-ticket experiment used only AES-192-CFB. This expansion tests eight historical-family/reference-mixer profiles on one *new* known ticket. The user provided draw #14249 (Saturday, 5 September 2026): **2, 4, 30, 32, 35**. We did **not** consult #14250. This target is outside the archived 100-draw file (#14256–14355).

## Model contract and experimental status

- Source-supported family names (not operator configuration): AES-192-CFB, DES-CFB, CAST-128, BBS, RSA/Rabin parity, modified Algorithm M, Algorithm B, XOR mixing. CAST-128 appears in the original designer's 2001–02 account; the 2023 paper discusses AES as well. These are *different historical references*, not confirmed to be simultaneous or in the 2026 installation.
- **Explicit experimental assumptions:** full-block CFB128 for AES and CFB64 for DES/CAST; synthetic public SHA512 indexed seed→key/IV; toy number-theoretic parameters (BBS 383×503; RSA 397×401, exponent 17); unverified M/B 256-bit block boundaries; zero-plaintext cipher source; unsigned 24-bit rejection with lexicographic combination unranking; uninterrupted generator state across both consecutive tickets, **without** fresh entropy between draws.
- Each model is initialized afresh for each candidate seed index. A first five-number ticket is compared for exact equality, then an identical stream is reinitialized and advanced to generate the following ticket *only for exact fits*.
- Families and attempted public seed-index counts: AES-192-CFB 400,000; DES-CFB 400,000; CAST-128-CFB 400,000; BBS-toy 80,000; RSA-toy 80,000; AES⊕DES 100,000; M(AES,BBS) 100,000; B(BBS) 80,000.

## Executed result

**1,640,000 attempted; 5 exact first-draw fits; 505 first-ticket decoding failures** due to exhausted finite 6-byte preview; all 5 matching models were replayed using 64 bytes without changes. For a fully uniform independent ticket model, 1,640,000/324,632 ≈ **5.05** first-draw fits expected. The toy parity/mixer models are not guaranteed uniform, so this is a rough reference only, not an exact null for every configuration.

| Family | Fitting public synthetic seed index | Pre-reveal candidate for #14250 |
|---|---:|---|
| `aes192-cfb128` | `43315` | 1, 10, 22, 25, 27 |
| `aes192-cfb128` | `236403` | 4, 6, 19, 27, 31 |
| `cast128-cfb64` | `78501` | 1, 14, 24, 30, 31 |
| `cast128-cfb64` | `251682` | 11, 23, 27, 30, 31 |
| `xor-aes192-des` | `29267` | 9, 16, 19, 26, 32 |

**Frozen primary tie-breaking rule:** among all exact first-ticket fits, choose the smallest SHA256 of `DOMAIN + b'FIXED-SELECTION|' + ASCII(family + '|' + seed_index)`. This rule references no hidden outcome. It selected **AES-192-CFB, seed index 236403**, yielding **4, 6, 19, 27, 31** for hidden draw #14250.

**Pre-reveal immutable GitHub lock:** [extra5_draw14250_LOCKED_before_reveal.json](../experiments/extra5_draw14250_LOCKED_before_reveal.json), first lock commit [`8b0c8b447f86ebfe6c069fde5a52496ed674067c`](https://github.com/SaridakisStamatisChristos/Extraexperimental/commit/8b0c8b447f86ebfe6c069fde5a52496ed674067c). Do not amend this file after revelation. The **five alternative candidate outputs** were also locked; selecting one post hoc is invalid.

## Validation

- A regression test caught a bug in the first M/B short-preview implementation: wraparound operations at the end of a 256-bit block must not change earlier output bits when a shorter prefix is requested. Fixed by explicitly implementing the first `n` bits of the main loop for prefixes under 256 bits, and full-block mixing for longer streams.
- Re-executed the entire sweep with the fixed code; reported fits and primary ticket were unchanged. A second, independently written compact implementation reproduced all 1,640,000 cases and every recorded matching seed and preview failure.
- **18 local unittest cases passed** (13 original plus 5 compact-version regression checks): AES/DES/CAST CFB references, prefix consistency across all eight profiles, M/B reference comparison, XOR reference, seed-domain separation, draw IDs and training values, combinadic rank/unrank, and all 5 first/second ticket replays.
- GitHub machine-readable summary: [`extra5_multifamily_blind_14250.json`](../experiments/extra5_multifamily_blind_14250.json). The more detailed local execution JSON has SHA256 `afd15e32a7b991ba6e8c11ee43eb5ea618d8c2824652f3a3a4c489451d4cd88b`; the committed compact summary is semantically equivalent but not byte-identical. Generated on Python 3.13.5, cryptography dependency in repository requirements. Rerun the independently verified compact implementation with `python experiments/extra5_multifamily_compact.py --cipher-seeds 400000 --math-seeds 80000 --mixed-seeds 100000` from repository root; tests with `python -m unittest discover -s tests -p 'test_multifamily_compact.py'`.

## Scientific outcome and next checkpoint

Five exact fits to one historical ticket are consistent with chance after a large seed search; different fitted models predict different next outcomes. No hidden draw has been checked, no manufacturer RNG state or actual seed material recovered, and the per-draw entropy may make continuous-stream assumptions wrong. Do not claim that these are actual Allwyn keys, algorithm identification, or betting forecasts.

**NEXT:** Ask user for #14250 only now that the candidate and primary predictions are locked. Compare the **primary** candidate to the revealed actual five numbers and record the result in a NEW file. Score other candidate outputs only as exploratory diagnostics; never change the frozen selection rule. Later, conduct further unseen adjacent-pair tests with the identical protocol.