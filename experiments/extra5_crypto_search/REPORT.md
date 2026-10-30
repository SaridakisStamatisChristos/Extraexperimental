# EXTRA 5 — Independent 24,480-configuration cryptographic public-seed search
Date: 2026-10-30. This report describes **executed local tests**. Complete C++/Python source and raw artifacts were distributed as `extra5_crypto_24480_research.zip` in the originating ChatGPT conversation, but are NOT yet part of this GitHub commit.

## Input contract and candidate family
- Authoritative five-year CSV: `experiments/extra5_five_year/extra5_2022_2026_authoritative.csv`, SHA256 `61fc2a3a57656a8188f7defc422ea5efbb1a33756455a41b97891cf0004c8307`.
- 3,526 consecutive drawings. 2022–2024 (2,192) train/selection; 2025 (730) validation; 2026 (604) retrospective evaluation. Prediction selection binary had **calendar metadata only** for later years.
- 6 digest primitives: SHA256, SHA512, SHA3-256, SHA3-512, BLAKE2b-512, SHA1 (weak comparison control).
- 12 public seed derivations from schedule/draw ID; 17 signed offsets; four byte alignments; five distinct number-selection samplers including rank32 rejection, continuous rank24 rejection, Fisher–Yates modulo/multiply-high and duplicate rejection. `6*12*17*4*5 = 24480` configurations, complementary to 28,560 prior public-seeded PRNG configurations (53,040 across both research runs).
- OpenSSL EVP digest counter stream. 64-bit unsigned public seed, 64-bit block counter and domain constant (little-endian), digest bytes read as big-endian 24/32-bit chunks for sampling. Not a secret-key or production-CSPRNG reconstruction.
- Train primary optimization: maximum number of >=4 overlaps, tie-break total overlaps. Train secondary: maximum total overlaps, tie-break >=4. Search-adjusted full-library fair-null maximum calibration with 180 simulated independent train histories. Frozen 2025–2026 predictions have SHA256 `a5aef8d2ae1c564fb0f94a247d1e7180b1bc1f9f3d613d4df0049e3e23a73cd6`. These years had already appeared in prior project analyses, so this is *not a globally clean/prospective holdout*.

## Training selection and 2025–2026 evaluation
| Selection | Config | Train >=4 | Train overlaps | Full-search null p | 2025 >=4 / overlaps | 2026 >=4 / overlaps | Combined >=4 / overlaps |
|---|---|---:|---:|---:|---:|---:|---:|
| Rare-event objective | `sha512,date_hour,-2,3,rank24_continuous` | 8 | 1,578 | 44/181=0.24309 | 1 / 520 | 0 / 419 | 1 / 939 |
| Overlap objective | `sha1,minute,-600,3,fy_multiplyhigh` | 1 | 1,718 | 22/181=0.12155 | 1 / 497 | 0 / 416 | 1 / 913 |

No complete 5/5 match in evaluation. For a fixed five-number ticket, `P(>=4)=(5*30+1)/C(35,5)=151/324632≈0.000465142`. Over 1,334 later-year draws the chance mean is 0.6205 >=4 events and 952.857 total overlaps. One or more >=4 events has null probability ~0.4624. Selected models did not replicate a 4/5 effect in 2026.

## Post-hoc whole-library red team — never a selected prediction
An entirely separate retrospective scan of all 24,480 configurations on the 2025 and 2026 outcomes found 48 with >=2 near-misses in each year; null expected count 36.9586 (linearity of expectation, no assumption of model independence). The post-hoc best configuration `blake2b512,minute,120,1,fy_modulo` scored 3 near-misses in 2025 and 2 in 2026, 969 total number matches. All 300 full-library fair-null re-searches found an equally or more extreme balanced-plus-total maximum; plus-one calibrated p=301/301=1.0. This does NOT demonstrate predictive consistency.

## Independent verification
- OpenSSL C++ search, separate Python hashlib forward oracle: all 2,668 frozen later-year tickets reproduced, plus 4,384 training tickets and scores.
- Further independent oracle: 2,880 unique C++ digest/sampler cases covering six digest families, six seed types, four byte alignments, five samplers, and four draw records matched Python exactly.
- 13 local Python tests passed, including strict split and lock checks; no CI added, no old prediction locks changed.
- GCC 14.2, C++20 -O3 -march=native, OpenSSL 3.5.7. Hashing stage 31.3 s on local system. Posthoc executable 23.7 s, peak RSS ~260 MB. Machine-specific timings; no speed claim.

## Implementation evidence versus toy hypotheses
The 2004 Electronic National Lotteries paper describes historical use of physical entropy, coupon-file hash, Naor–Reingold seed postprocessing, cryptographic BBS/RSA and symmetric-cipher generators and mixing. The 2023 Bikos et al. paper documents related historical architecture and protected entropy. OPAP's 2023 report describes certified independent cryptographic RNG systems. None confirms the exact 2026 secret seed/sampler. Public timestamp/ID hash searches cannot reproduce unobserved physical entropy or secret keys.

Sources: https://doi.org/10.1007/978-3-540-27809-2_18 ; https://doi.org/10.3390/cryptography7040054 ; https://media.opap.gr/OPAPIntegratedReport202327082024.pdf

**Verdict:** Additional 24,480 completely specified public-seeded hash/sampler configurations executed; no consistent 4/5 predictive edge established. Competing actual-production architectures, secret seeds and sampler remain unidentified. The next scientifically decisive step requires current implementation evidence or truly prospective results. 