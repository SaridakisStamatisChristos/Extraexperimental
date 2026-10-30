# EXTRA 5 — R7 evidence-closed 604-draw reconstruction, 2026-10-30

## Contract and immutable constraints

**Goal:** independently identify or falsify plausible generator and sampler implementations and test whether any models genuinely predict future lottery results. **Hard constraints:** source authority of the user-supplied workbook, correctly report #14249, no data leakage, preserve prior prediction locks, no CI, executable reproducible research, put the continuation note in the same commit as research changes. The deployed RNG is unknown. The 2026 data have already been inspected and are not an untouched prospective test.

## Source integrity and provenance

- User-supplied XLSX file SHA-256: `97f6b7ae5e41565d77ed8065a044c57bde539da8d5dca4e44917466c02b4738c`.
- Normalized CSV SHA-256: `5fb393513548e1c5853165eeb137c66f1a859071eaf0c4c8203f5d487289d33e`.
- 604 workbook records compared to CSV in every recorded number position, date, time, ID. All match. Workbook has a misleading worksheet dimension and is parsed by its actual XML rows; a separate `artifact_tool` import also read header and sample/end rows correctly.
- Corrected #14249 workbook order: `35,2,4,30,33`; unordered sorted: `2,4,30,33,35`. Historical manually provided `...30,32,35` superseded.
- Ordered columns D–H might be extraction order, but this **was not independently verified**; no ordered-state inference may assert that it is true.

## Exact search: xorshift96, six known draws

Assumed toy model: 3-word xorshift96 recurrence from `toy_inverse.py`, 32-bit words emitted big-endian into continuous byte stream, 24-bit chunks rejected when `raw24 >= 16,556,232`, accepted chunks mapped as `(raw24 % 324,632)` to a lexicographically ranked unordered 5/35 ticket. **Zero rejected chunks for the first four accepted tickets**. Each such ticket has 51 admissible raw24 aliases.

All `51^4=6,765,201` branch states were **exhaustively enumerated**, not sampled. Because the first 3 output words form an invertible 96x96 GF(2) mapping, each 96-bit alias transcript corresponds to exactly one state. Exhaustive histogram over fifth tickets produced **324,632 distinct** possibilities, multiplicities from **4 to 44**, first-fifth rejection counts `{0:6676127, 1:87901, 2:1161, 3:12}`. Exactly **25** states matched #14253 `(17,23,30,34,35)`; **zero** of these matched sixth draw #14254 `(1,6,23,26,34)`.

All 25 surviving fifth-match states were fully forward-decoded to draw #14254. Additional 600 deterministic random states were decoded forward from the beginning to validate the training prefix. A distinct 11-test unit suite independently checks the exact lexicographic ranking, generator forward outputs, all 25 witness states, full-rank xorshift128 transform, data integrity and forecast normalization.

**Disposition:** **REFUTED**, but *only* for the fully declared six-draw, zero-initial-rejection toy branch and continuous state. This **is not** proof against all xorshift96 implementations, nor any actual certified electronic RNG. No seed recovered.

## Full 604-draw statistical audit

One broad diagnostic battery compares observed records to independent uniform 5/35 draws. Use 700 **separate** null-calibration sequences for each statistic's mean and variance; 3,000 new null sequences to calibrate the maximum standardized statistic across 15 measurements; 4,000 permutations conditionally shuffling numbers within each observed ticket for a separate positional diagnostic.

Metrics: 35-way inclusion chi-square, greatest standardized marginal deviation, maximum pair count, number of within-ticket adjacent values, ticket-rank Kolmogorov–Smirnov deviation, exact duplicate ticket pairs, time-of-day and weekend contingency differences, ticket sum, adjacent and long-lag overlaps at 1,2,3,7,14,30 draws. Full observed/null means/null SD/per-metric and familywise p-values are in `statistical_audit_results.json`.

- Familywise maxT p-value: `0.8643785404865045`.
- Conditional positional-permutation p-value: `0.775556110972257`.
- Maximum observed pair count: `19`; adjacent consecutive values across draws: `363`; exact duplicate pairs: `1`.
- The most extreme standardized statistic is mean overlap at lag 1, which still produces no evidence after correction.

**Disposition:** **NO DETECTED ANOMALY IN THIS BATTERY**, not proof of truly random or cryptographically secure output. Exploratory because the historical data are public and the project previously searched many possible metrics.

## Explicit historical walk-forward model comparison

For every historical target from draw `#13954` through `#14357` (404 draws), estimate weights only from draws with **strictly smaller IDs**, normalize the induced probability over all `C(35,5)=324,632` subsets by the exact elementary-symmetric-polynomial DP, and score the actual outcome. Fixed 15 model specifications: uniform; 0.2/0.6-smoothed cumulative; 0.2/0.6-smoothed mean-reversion (*cold*); exponential half-lives 10/30/100 with 0.2/0.6 smoothing; last-draw repetition and avoidance; time-matched and weekday-matched frequencies.

- Uniform mean log probability: `-12.690447512074...`.
- Best historical nonuniform (`cold:None:0.2`) mean log probability ≈ `-12.688111...`, aggregate improvement `+0.9438738100234332` nats, likelihood ratio `exp(0.94387)≈2.57`.
- Equal-weight mixture over 14 nonuniform likelihood-ratio processes ≈ `0.25964055347544973`.
- None of this is fresh-blind evidence; the *cold* hypothesis was discussed earlier in the project's historical 40-draw experiment. A process chosen based on past-exposed records cannot honestly claim a preregistered 2026 e-test.
- Selecting *any* model by top-5 historical hit count instead of proper log score is discouraged: with 604 draws and many choices, selective agreement is inevitable.

**Disposition:** **NO VALIDATED PREDICTIVE ADVANTAGE**. The slight post-hoc cold likelihood improvement is a research observation, not a reliably exploitable feature.

## A rigorous identification limit

**Proposition (observational equivalence of ideal samplers):** Let `Ω` be the `C(35,5)=324632` unordered tickets. If two sampler mechanisms each output every ticket with probability `1/|Ω|`, independently each draw, then for any finite observed sequence `(S_1,...,S_m)` both assign exactly probability `|Ω|^{-m}`. Their induced data distributions are identical; their likelihood ratio is always 1; no decision rule using only that observed ticket history can identify which of these two mechanisms produced it better than random guessing with equal priors.

**Proof:** Independence gives `Pr(S_1,...,S_m)=∏_{t=1}^m Pr(S_t)=|Ω|^{-m}` under each mechanism. The two probability laws coincide at every outcome, giving total-variation distance zero. QED.

The same reasoning applies to **ordered** draws if their complete ordered five-number laws coincide and the recorded order is genuine. This says nothing about insecure samplers that introduce detectable biases or temporal correlations; it only says faithful uniform algorithms cannot be distinguished by their identical outputs.

## Operator evidence and limits

Allwyn's [EXTRA 5 information](https://allwyn.cy/en/games/extra-5/more-about/) currently states that the game has **two electronic draws daily (15:00/19:00)** and that a certified electronic RNG generates the five numbers. This is direct public-source evidence of the **class of device**, not of source code, seed mechanism, entropy, rekeying policy or 2026 RNG algorithm. The existing repository documents historical BBS/RSA, cipher-mode, mixer and entropy protocols; **do not conflate that historical system with the current certified installation**.

## Verification and falsification gates

| Gate | State | Evidence |
|---|---|---|
| Exact XLSX↔CSV equivalence, 604 records | VERIFIED LOCALLY | `source_integrity.py` output and `source_integrity_results.json` |
| 604 chronological IDs, 5 unique numbers | VERIFIED LOCALLY | `test_research.py`, `source_integrity.py` |
| Toy xorshift96 first-4 no-rejection branch exhaustive | VERIFIED LOCALLY | `exhaustive_six.py`, output witness states and histogram |
| Independent forward check of 25 fifth-match states | VERIFIED LOCALLY | `test_research.py` |
| 11 adversarial/reconstruction unit tests | VERIFIED LOCALLY | `python -m unittest -v test_research.py` |
| Calibrated 604-draw fingerprint suite | VERIFIED LOCALLY | `statistical_audit.py` and JSON |
| Chronological 15-model replay | VERIFIED LOCALLY | `walkforward_models.py` and JSON |
| True unexposed future predictive edge | **UNVERIFIED** | Historic data already public; pending prospective scoring |
| Current operator RNG and seed recovered | **UNVERIFIED** | No production implementation evidence |
| Recorded numeric column order equals extraction order | **UNVERIFIED** | XLSX alone does not prove semantic ordering |
| No CI | VERIFIED | No `.github/workflows` file added or modified |

### Forward-only null control

`prospective_null_control_14360_LOCK.json` records a deterministic SHA-256-derived ticket **2, 7, 13, 26, 32** for draw #14360, scheduled Oct 31 at 15:00 Greece time if the normal twice-daily schedule continues. The source is locked through #14357; it does not use #14358 or #14359. This control has **the ordinary 1-in-324,632 chance for a full match under uniform draws**, not additional predictive power. An immutable previously saved JSON lock is never overwritten with different content.

## Next scientifically justified research

1. Obtain authenticated current operator/certification evidence identifying RNG version, seeding and five-number sampling transformation; historical cryptographic descriptions are not enough.
2. Independently verify whether spreadsheet D–H ordering is the actual draw extraction order. If yes, model ordered output (approximately 6.9 extra bits per draw) and test candidate sampler-specific position signatures.
3. Distinguish continuous-state hypotheses from per-draw entropy and reseeding. One public 5-of-35 ticket per draw cannot prove the device retains state between draws.
4. Preserve all pre-reveal predictions and score genuine future results against exact uniform expectations. Never revise old locks after outcome disclosure.
5. Replicate promising findings on a separate historical year that was *not* used in model selection; correct across the project's full model-search history.
