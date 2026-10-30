# EXTRA 5 2022–2026 — Research and falsification report

**Executed:** 30 Oct 2026. **Goal:** use four additional years of user-authoritative draws to challenge real generator/seed/sampler hypotheses and to inspect full-sequence statistics. **Verdict: actual production RNG unidentified; no validated predictive advantage.**

## 1. Source integrity

- Archive contains exactly **3,526** draws covering **every draw ID from 10832 through 14357**. Dates cover 2022-01-01 15:00 to 2026-10-29 19:00.
- Counts: 2022 730, 2023 730, 2024 732, 2025 730, 2026 604. Two correctly timed rows every calendar day, including the 2024 leap day. No gaps, duplicate IDs or duplicate date/time pairs. All tickets are five distinct integers in 1..35.
- Sorted #14249 = **2,4,30,33,35**, consistent with the 2026 workbook and *not* the earlier mistyped 32.
- Source XLSX SHA-256 and normalized CSV SHA-256 recorded in `provenance.json`. Original Excel number order preserved, but actual mechanical selection/extraction order not independently verified.
- 2022 and 2023 XLSX report 1521 used rows despite only 730 real draw records each; a strict nonempty numeric-ID parser prevents treating formatted blanks as draws.

## 2. Fixed generator-family search: 2022–2024 → 2025 → 2026

We tested **1,080 explicitly enumerated deterministic (generator, calendar/ID-derived seed, sampler) combinations**. Real PRNGs include conventional 32-bit LCG variants, xorshift32, xorshift64*, SplitMix64, PCG32, and Python MT19937. Five output-to-ticket samplers include bounded rank, 24-bit combinatorial rank with rejection, unique modulo-35, and modulo/unbiased partial Fisher–Yates. Reused prior project PRNG implementations; they are not alleged to be live production components.

Model selection sees only 2,192 draws from 2022–2024 and maximizes historical number-overlap count. Its candidate is frozen before the evaluation portion reads any 2025 or 2026 **outcome**. The precomputed 2025–2026 predictions use only calendar and ID information. The implementation physically reads `train_2022_2024.csv` plus an outcomes-free `evaluation_calendar_2025_2026.csv` before locking. The full outcome-bearing CSV is first opened after the freeze.

| Partition | Observed overlaps | Uniform expected overlaps | Exact one-sided p |
|---|---:|---:|---:|
| Train 2022–2024 | 1,692 | 1,565.71 | p=0.09726 **after 1,080-model search** |
| Validation 2025 | 538 | 521.43 | 0.20872 |
| Test 2026 | 442 | 431.43 | 0.28740 |
| Evaluation 2025–2026 | 980 | 952.86 | 0.16047 |

Winner: **SplitMix64, seed = floor(Athens-scheduled-draw Unix seconds / 60) − 60, sampler = 24-bit big-endian rejection and lexicographic combinatorial rank**. It produced **0 exact tickets** in 2025 or 2026. In neither year does its score warrant rejecting a fair 5-of-35 null. The source-code recurrence is an authentic SplitMix64 implementation; its *attribution to this lottery* is conjectural and unsupported.

The development-stage p-value came from 400 Monte Carlo fair-ticket *sequences*, each scored across the identical candidate library, with deterministic RNG seed 20261030, using the maximum score from each simulated search. The correct evaluation tails were calculated by exponentiating the exact hypergeometric single-draw overlap probability polynomial, not by assuming independent Bernoulli picks within each draw.

**Do not select models using the 2026 outcome and then present those same 2026 outcomes as blind tests.** All draw data existed when this experiment was run: temporal splits are retrospective, not true prospective pre-reveal forecasts.

## 3. Full-sequence tests with multiple-comparison accounting

1,000 independent fair five-of-35 simulations calibrate seven broad null statistics plus the maximum serial-overlap deviation across lags {1,2,3,7,14,30}. Another 1,500 conditional label permutations test workbook number-column order and 1,500 paired day/evening permutations test session differences.

| Statistic | Observed | Unadjusted p (test direction) | Bonferroni p, 10 tests |
|---|---:|---:|---:|
| Global 35-number frequency χ² | 16.849 | 0.976 (upper tail) | 1.000 |
| Largest individual-number deviation | 51.29 draws | 0.400 | 1.000 |
| Maximum repeated number pair | 91 | 0.04795 | 0.480 |
| Yearwise frequency χ² | 136.927 | 0.785 | 1.000 |
| Lexicographic rank decile χ² | 4.011 | 0.907 | 1.000 |
| Repeated complete-ticket pairs | 21 | 0.750 (two-sided) | 1.000 |
| Consecutive-integer number pairs | 1,979 | 0.414 (two-sided) | 1.000 |
| Largest serial overlap deviation, six lags | 1.560 scaled | 0.180 | 1.000 |
| Workbook column position statistic | 169.338 | 0.04464 | 0.446 |
| Afternoon/evening paired statistic | 35.993 | 0.197 | 1.000 |

No test passes 5% familywise control. The aggregate χ² being **lower** than typical simulations is an exploratory *underdispersion* possibility (simulation upper p=0.976, hence lower tail around 0.024); this does not survive correcting for examined statistics, and a test for unusually high imbalance would not detect it. Do not conflate a low χ² with a demonstrably biased or manipulated draw process.

Full-archive individual counts span **475–555** vs 503.714 expected each, with number 4 appearing 555 times. The most frequent pair is (4,8), co-occurring 91 times; maximum-pair upper-tail p is about 0.048 before adjusting for all summary families.

## 4. Follow-up: pair (4,8) in 2022

The 2022 maximum observed pair was **(4,8), occurring 29 of 730 draws**. A *fixed prespecified* pair has binomial probability 20/(35×34) ≈ 0.0168067 per draw; exact upper tail for 29+ occurrences is 2.7516×10⁻⁵. But this pair was discovered by a scan of **595 possible pairs and five years**. A Monte Carlo replay of that scan over 2,500 simulated complete five-year archives produced a familywise p ≈ **0.06477**, and the signal did not replicate at that intensity in later years.

This is an *exploratory* lead, not evidence of machine-level weakness or future excess for the pair. Searching additional windows/pairs without preregistration makes overfitting more likely.

## 5. Identifiability and architecture

One unordered five-of-35 result conveys at most log₂(324632)=18.30845 bits. All 3,526 results provide at most **64,555.58 bits** of ticket-output information (not secret-key entropy). If five workbook columns are proven to record true extraction order, the alphabet ceiling is **88,909.28 bits**. Even long archives cannot guarantee recovery of an RNG that incorporates fresh private entropy per draw.

**What is ruled out?** The exact timestamp/ID-seeded candidates did not demonstrate explanatory/predictive performance. Earlier work additionally excluded a fixed no-initial-rejection continuous xorshift96 sampler by its sixth draw, and several 32-bit hypotheses by SMT. This campaign does not falsify all reseeding functions, all sampler families, or modern cryptographic PRNGs.

**Production evidence:** [Current Allwyn description](https://allwyn.cy/en/games/extra-5/more-about/) calls the draw certified electronic RNG; [OPAP 2020 report](https://investors.opap.gr/~/media/Files/O/Opap-IR/06022020/Integrated%20Report%202020%2016062021%20compressed.pdf) describes independently secured cryptographic RNG systems. These sources do not disclose live key material or the current sampler. Attribution of simple toy PRNGs remains speculative.

## 6. Reproducibility and hard limits

- Commands in `README.md`; 15 independent local tests pass.
- Original XLSX hashes and CSV digest in `provenance.json`.
- No CI added; historical pre-reveal prediction locks untouched.
- `selected_generator_PRE_EVALUATION.json` preserves the selected configuration and **1,334 year-ahead tickets** before the evaluation scorer accesses outcomes.
- Source adaptation of `timestamp_prng_scan.py` is a verbatim copy from the prior real-generator research bundle; its PRNG/sampler logic is retained rather than rewritten to fit new data.
- A 2025/2026 test does not become genuine prospective validation merely because it was withheld from executable model selection; the draws were already published when the experiment ran.
- Numerical p-values are Monte Carlo estimates except stated exact hypergeometric/binomial calculations. Familywise inference is limited to the declared hypotheses/tests, not the much larger history of all research attempts.

**Conclusion:** Better source coverage and more powerful falsification do not currently produce an actual predictive generator. Prioritize verified implementation-level evidence and prospective pre-reveal checks rather than further posthoc algorithm searching.
