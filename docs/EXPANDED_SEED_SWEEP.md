# Step 9 — 128-seed historical replay (29 October 2026)

**Result:** 128 PUBLIC SYNTHETIC SEEDS, 25,344 generator/seed/sampler configurations attempted; no identification of real Allwyn entropy or seed.

## Executed protocol

- Recorded draws: **#14256–14355**, 100 draws from the repository, with first 80 used for model choice and later 20 used as **retrospective pseudo-holdout**.
- Seed indices **0–127** in the existing domain `EXTRA5-INDEPENDENT-SEED-SEARCH-v1|NOT-OPERATOR-SEEDS|`; not a search through a disclosed operator seed space.
- 31 fixed BBS/RSA/DES/AES research routes plus two experimental switching schedules; 2 seed-state policies; 3 candidate bit-to-five samplers.
- **25,344 attempted; 23,343 completed; 2,001 rejected** after the explicitly bounded **1,024-bit sampler budget**. Failures remain counted, not quietly discarded.
- New locally executed cached implementation reused per-draw derived seeds and bitstream prefixes across sampler variants; its first eight seed indices produced **byte-identical score CSV** against the previously committed original replay (all 1,479 completed configurations; SHA256 `86d9a47e992923e689308a2242083e14fb070c96dbd728e5a22f20a5304cc174`).
- Full local Python test suite: **64 passing**, no CI.

## Historical comparison

| Candidate | Training (first 80, out of 400 individual overlaps) | Later 20 (out of 100) |
|---|---:|---:|
| **Train-selected:** index 86, previous-state fixture, BBS/RSA/DES XOR, sequential sampler | 85 | **12** |
| **Post-hoc later-20 maximum:** index 17, previous-state fixture, BBS/DES XOR, combination-rank sampler | 47 | **29** |
| Independent uniform-draw expectation | 57.14 | **14.29** |

- The training-selected configuration **underperformed** the fair baseline on the later 20; fixed-model one-sided upper-tail p≈**0.7996**.
- A later-20 maximum of 29 looks rare *for a prespecified single model* (uncorrected p≈0.0000324), but that is **invalid as a claim of a discovered model** after searching 23,343 completed configurations.
- In **1,200 simulated fair 20-draw histories**, taking the maximum across the **same fixed 23,343 candidate predictions**, **648** attained 29 or more. Familywise plus-one p≈**0.5404**.
- No completed candidate matched all five numbers on any later-20 draw (0 exact tickets across the candidate library). Under independent fair ticket assumptions the expected count is ~**1.44**, but the models are correlated.

**Scores file:** 23,343-row CSV generated locally, SHA256 `aa6957f68853af23e4cadeb48cf86decc2d98c437910df58e26143aa80510c81`. This hash verifies the optimized implementation output; source code and results were generated locally. The full CSV is **not included in this archival commit**; regenerate it from the benchmark.

## Reproduction with code already in this repository

```bash
cd experiments
python extra5_seeded_replay.py --seeds 128 --null-replicates 1200 --out .
```

This original replay implementation is slower than the optimized locally run cache/rewind variant; results are expected to agree numerically, and the previous eight-seed sweep was verified byte-for-byte. **A full 128-seed rerun with this slower archived implementation has not been executed**, so the archived CSV checksum is not independently confirmed for all 128 indices.

## Inference

Brute-force searching arbitrary synthetic seed indexes produces chance historical overlaps. Without operator entropy, coupon input bytes, secret CSPRNG parameters, and actual switching/sampling configuration, this exercise **does not** recover the operator seed or forecast future numbers. Expanding the search again without additional technical evidence has diminishing scientific value.

Next: seek original implementation documentation that identifies concrete seed/IV derivation, cipher parameters, route schedule, and 5/35 number mapping, then test pinned source-grounded variants. No CI.
