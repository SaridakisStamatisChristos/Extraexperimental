# Greek EXTRA 5 (5/35): independent statistical audit — 29 October 2026

## Executive finding

The **available aggregate historical data do not establish systematic number-frequency bias**. For 14,346 draws up to 24 October 2026, the correctly calibrated global frequency test yields **χ²(34)=37.9914, p=0.29237**. Neither the lowest-frequency number nor the most common published pair remains significant under familywise correction.

One exploratory finding deserves independent replication: **the 80 draws between snapshots dated 14 September and 24 October 2026 have unusually evenly distributed individual-number counts**. Their corrected chi-squared dispersion statistic is **15.725** on 34 asymptotic degrees of freedom; exact-model Monte Carlo simulations yield a **lower-tail probability of approximately 0.003**. It is not evidence of predictability, algorithm identification, or deliberate intervention. The interval was assembled after data discovery, and the full event-level history has not been independently validated.

This is an **aggregate-statistics audit**, not a complete event-level cryptographic or randomness audit. Full serial-independence, arbitrary lag, source-integrity, and historical change-point testing need primary draw-by-draw records.

## Data and provenance

- Primary aggregate data source (third party): [Foufos EXTRA 5 statistics](https://www.foufos.gr/en/stats/extra), publication snapshots dated 14 September 2026, 17 October 2026, 24 October 2026.
- Cumulative draw counts: **14,266**, **14,331**, **14,346** respectively; all sets of 35 published cumulative frequencies independently sum to **5 × number of draws**.
- Source for architecture: [OPAP Integrated Report 2023, p. 104](https://media.opap.gr/OPAPIntegratedReport202327082024.pdf). OPAP reports independent cryptographically secure random-number systems for EXTRA 5, KINO, and SUPER 3, certified randomness, and cryptographic controls.
- Source cross-reference: [Lottevo EXTRA 5 statistics](https://lottevo.com/lotteries/greece-extra-5/statistics), with closely matching top and bottom number counts for 28 October 2026.
- The latest source listings indicate 14,354 draws by 28 October 2026, but a full readable 35-number table from that date was not retrieved in this execution environment. This audit's main snapshot therefore ends on 24 October 2026.

## Null model

Each draw is a uniformly sampled five-element subset of {1,...,35}, independent of every other draw. Within-draw number appearances are negatively correlated, because the five numbers are distinct.

- Expected individual count in N draws: N × 5/35 = N/7.
- Marginal individual-number probability under the null: Binomial(N,1/7).
- For the 35-way Pearson frequency statistic, the sampling-without-replacement correction is 34/30. The resulting statistic has approximately a χ² distribution with 34 degrees of freedom.
- For a fixed pair, the joint draw probability is C(5,2)/C(35,2) = 10/595 = 0.0168067.
- Probability of k overlaps between consecutive draws is C(5,k) C(30,5−k) / C(35,5).

The theoretical reference probabilities are derived from combinatorics, not trained on the past data.

## Executed test results

| Hypothesis / diagnostic | Result | Interpretation |
|---|---:|---|
| All 35 number frequencies, N=14,346 | χ²(34)=37.9914, p=0.29237 | Does not reject uniformity |
| Number 9, historical count | 1,955 vs expected 2,049.43 | Lowest observed number |
| Number 9, exact two-sided p | 0.02415 | Nominal only; Bonferroni ×35 = 0.845 |
| Number 32, historical count | 2,126 vs expected 2,049.43 | Most frequent |
| Pair 3–31 | 298 vs expected 241.11 | Most frequent published pair |
| Pair 3–31, two-sided p | 0.000349 | Bonferroni ×595 = 0.20769; not significant |
| Average number sum | 90.064 vs expected 90 | p ≈ 0.718 |
| Odd-number appearance total | 37,010 vs expected 36,889.7 | p ≈ 0.339 |
| Group frequencies 1–10, 11–20, 21–30, 31–35 | corrected χ²≈7.020 | p ≈ 0.071; does not reject |
| Last digit frequencies | corrected χ²≈10.046 | p ≈ 0.347; does not reject |
| Consecutive-draw overlap summary | approximately 43.4%, 42.9%, 12.3%, 1.3%, 0%, 0% for 0–5 overlaps | Only rounded aggregates available; not subjected to an exact multinomial test |
| September 14–October 24, N=80 | corrected χ²=15.725, lower-tail MC p ≈ 0.003 | Exploratory unusually *low* dispersion; requires reproduction |

### Recent-window finding

The September 14 count vector was subtracted from the October 24 count vector. All 35 changes are nonnegative and sum to 400 = 80 draws × five numbers. The 35 numbers each occurred **8–18 times**, versus 11.429 expected. The observed standard deviation across number counts is **2.160**; the single-number null standard deviation is **3.130**. A Monte Carlo experiment simulating independently selected five-of-35 draws provides the lower-tail probability reported above.

This interval is *not* proof of tampering. There may be many unobserved/comparable 80-draw windows in the complete historical archive; looking for extraordinary windows produces extraordinary results by chance. A thorough analysis requires preselected time windows or a familywise correction across all windows, independently reconciling the two snapshots to actual draw IDs, and a future holdout period.

### What this cannot establish

1. A frequency test cannot demonstrate cryptographic security, reveal the actual CSPRNG construction, or distinguish between good pseudorandomness and ideal randomness.
2. Passing a test is not proof of randomness. Rejecting a statistical null is not proof of manipulation.
3. Frequency summaries discard chronological order. Thus, without raw draws, serial correlation, adjacent draw overlap, longer lags, calendar changes, and exact pair interaction tests are not fully evaluated.
4. The source's draw-ID range extends one number beyond its reported count (e.g., #1–#14347 versus 14,346 draws), requiring explanation/verification from operator data before a claim of perfect archive completeness.
5. Statistical results are descriptive, **not predictive**. Under a fair 5/35 draw, every five-number ticket retains the same 1-in-324,632 probability.

## Reproduction

Included files:

- `extra5_reproducible_audit.py`: complete executable source. Default run tests three published cumulative snapshots and performs 100,000 Monte Carlo simulations per snapshot window. With `--draws history.csv`, also audits raw draw records, including pair frequencies, serial overlap, number sums and fixed 80-draw windows with multiplicity correction.
- `extra5_audit_results.json`: executed numerical results, including historical frequency vectors, exact nominal pair test, and simulation parameters.
- `extra5_frequency_deviations.png`: plot of the 35 observed-minus-expected appearance counts for the 24 October 2026 historical snapshot.

Run: `python extra5_reproducible_audit.py --output extra5_audit_results.json`

Full raw-data CSV expected columns: `n1,n2,n3,n4,n5` and optionally `draw_id,date` (ISO YYYY-MM-DD). To enable full-history audit: `python extra5_reproducible_audit.py --draws history.csv`

The code was also run on a 100-row synthetic dataset to verify draw ingestion, count reconciliation, and serial-overlap bin totals. This validates the analysis pipeline, **not** the third-party historical archive.