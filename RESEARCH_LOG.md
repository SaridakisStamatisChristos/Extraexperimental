# Research log — Greek EXTRA 5 RNG investigation

**Archive cut-off: 29 October 2026.** This is a chronological preservation of the preceding research conversation. Reconstructed from retained technical reports and scripts, not a verbatim conversation transcript. Claims are labeled by evidence strength.

## Phase 1 — Game and historical cryptography

- Defined the public result as five distinct integers between 1 and 35, i.e. 324,632 unordered combinations.
- Investigated OPAP/Allwyn public statements describing independent cryptographically secure RNG systems for EXTRA 5, KINO and SUPER 3, with certification and integrity/auditing mechanisms. See OPAP 2023 integrated report, p. 104.
- Followed the historical original-system research trail through the 2004 *Electronic National Lotteries* paper and a 2023 *Cryptography* overview by researchers associated with the original project.
- **Historically documented components**: BBS, RSA/Rabin-style number-theoretic PRNGs, DES-CFB and AES-CFB ciphers, physical noise (including Zener and thermal sources), Naor–Reingold seed processing, XOR/Knuth-inspired mixing and dynamic selection/switching. The architecture is **not** evidence that these primitives, software or entropy sources operate unchanged in 2026.
- The exact 2026 seed/entropy, generator configuration, version and final five-of-35 mapping were not obtained.

## Phase 2 — Aggregate historical statistical audit

- Used third-party cumulative frequency snapshots including **14,346 draws through 24 October 2026**; examined uniformity using without-replacement covariance adjustment: `χ²(34)=37.9914, p=0.29237`.
- Compared the most frequent historical pair (3,31) with the null and familywise adjustment across 595 pairs. Published count 298, expectation ~241, adjusted p ~0.208; no statistically established excess under that correction.
- Exploratory analysis of **80 draws between 14 Sept and 24 Oct snapshots** found unusually *low* count dispersion, Monte Carlo lower-tail p ~0.003. This was selected after inspecting the historical snapshots; interpretation requires scan/window-selection correction and source reconciliation.
- No overall departure from uniformity was established; frequency tests cannot identify or compromise cryptographic RNGs.
- Original artifacts: `experiments/extra5_reproducible_audit.py`, `experiments/extra5_audit_results.json`, `experiments/extra5_audit_report.md`.

## Phase 3 — Test mathematical bit-to-ticket mapping

- Modeled an **explicitly hypothetical flawed sampler**: take a uniform `b`-bit value; choose `x % 35 + 1`; reject repeated labels until five distinct integers exist.
- Against a 14,353-draw snapshot, tested different source widths. The 8-bit version was ~15.21 SD away from its own prediction and is decisively inconsistent; a 10-bit version was ~3.49 SD away (exploratory), while 16-bit and 32-bit versions remained compatible.
- These results reject specific probability distributions, **not** the actual operator algorithm. Multiple unbiased samplers (partial shuffle, duplicate rejection with unbiased integers, combinatorial unranking) yield exactly the same 5-subset distribution.
- Original artifacts: `experiments/extra5_sampler_forensics.py`, `experiments/extra5_sampler_forensics_results.json`, `experiments/extra5_sampler_forensics_report.md`.

## Phase 4 — Pilot comparison against 20 draws

- Collected draws **#14336–14355 (19–28 October 2026)** from a third-party historical result listing.
- Simulated seven independent illustrative RNG families (BBS toy, RSA/Rabin toy, DES-CFB, AES-192-CFB, ChaCha20, SHA-256 counter, MT19937) with two unbiased samplers.
- With prechosen artificial seeds, the best of 14 configurations matched **20 of 100 ticket numbers**, compared with null expectation **14.29**. Single-model p ~0.060; not significant after testing 14.
- No exact five-number ticket match was found. This is descriptive hindsight scoring; not prediction.
- Original artifacts: `experiments/extra5_last20_simulation.py`, `experiments/extra5_last20_model_comparisons.csv`, `experiments/extra5_last20_simulation_results.json`, `experiments/extra5_last20_research_report.md`.

## Phase 5 — 60-family × five-sampler benchmark

- Collected **100 consecutively numbered draws #14256–14355 (9 Sept–28 Oct 2026)** and separated first 80 (#14256–14335) and last 20 (#14336–14355).
- Implemented 60 generator families, five sampling methods and public deterministic synthetic initialization, yielding **9,360 configurations** (32 seed indices for most families; eight for BBS/RSA).
- Training-selected: **SHA3-224 counter, seed index 0, sequential removal**: 88/400 train matches, **17/100** later-draw matches. Exact one-sided fixed-model holdout p ~0.2455.
- Strongest *post-hoc* selection looking directly at the last 20: **SplitMix64, seed index 25, reservoir**: **30/100** later-draw matches but 56/400 on first 80.
- Calibration: 3,000 null simulated 20-draw histories searched over all 9,360 fixed candidates; **280** simulations yielded a maximum >=30, plus-one probability **281/3001 ~= 0.0936**. Thus 30/100 is not a convincing post-search anomaly.
- Mean holdout score ~14.262 across configurations; train/test score correlation ~-0.028; no exact five-of-five matches in last-20 comparisons.
- The 20 later draws were already publicly known and were used retrospectively, **not a genuine future forecast**.
- All seeds and tested generators are artificial models, not a reconstruction of the current Allwyn system. Number-theoretic implementations are toys, not production-grade replicas.
- Original artifacts: `experiments/extra5_mass_algorithm_benchmark.py`, `experiments/extra5_mass_algorithm_calibration.py`, `experiments/extra5_mass_algorithm_scores.csv`, `experiments/extra5_mass_algorithm_results.json`, `experiments/extra5_mass_algorithm_research_report.md`.

## Current state / continuation checkpoint

**Supported:** historical architecture research, four executed categories of statistical/simulation analysis, reproducible scripts and source-specific historical numbers.

**Not supported:** exact identification of the 2026 RNG/sampler, seed recovery, output predictability, tampering allegations, statistically validated exploitable bias, or a claim of a successful forecast.

**Priority next:** reconcile authoritative historical draws and true drawn-order metadata; obtain current configuration/certification documentation; preregister sequential, overlap, and rolling-window testing; then perform a live forward-only prediction test only if a predeclared model exists.

No CI/automated deployment is requested. Archive is intentionally documentation-first.
