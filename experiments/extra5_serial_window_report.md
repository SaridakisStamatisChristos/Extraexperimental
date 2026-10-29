# EXTRA 5: Serial independence and frequency-dispersion audit

**Executed 29 October 2026 · research snapshot · 100 historical draws (#14256–14355) · experimental, not operational.**

## Scope and motivation

A prior analysis reported an 80-draw interval (#14268–14347) with unusually *even* number counts. This experiment checked whether the original interval reproduces from the archived draw-level data, compared all 21 possible contiguous 80-draw windows in the 100-draw archive, and tested temporal overlap across lags 1–5. We also assessed overall frequency dispersion. All diagnostics were selected after the research had already inspected these historical data; **this is not preregistered or predictive**.

## Data validity

- CSV: `extra5_last100_data.csv`. Exactly 100 consecutively numbered records, five different integers within 1–35 in each row; IDs #14256–14355.
- The source CSV is **sorted five-number combinations**, not authentic RNG emission order.
- External spot checks: #14256, #14259, #14351 and #14355 match third-party listings; #14351 and #14355 also match an Allwyn Cyprus draw-results page. This is **not** an authoritative line-by-line cross-check of all 100 records.
- Current published reference: https://allwyn.cy/en/games/extra-5/draws-and-results/ , https://numerics.gr/extra-5/kliroseis-apotelesmata , https://www.foufos.gr/extra .

## Null and statistics

Each draw is independently sampled uniformly without replacement from 1–35, yielding five numbers. A number's per-draw inclusion probability is `1/7`. The global Pearson statistic for all 35 marginal counts is adjusted by `34/30` for within-draw hypergeometric negative dependence; using a chi-square(34) reference distribution is an approximation. A *lower*-tail p-value tests for unusually **small** deviations from equal marginal counts (the upper-tail test is not the relevant direction here).

For adjacent (or lagged) draw overlaps `K`, the fair-null distribution is `Hypergeom(N=35, K=5, n=5)` with expectation `5/7` and variance `5*(5/35)*(30/35)*(30/34)`. The lag-family test uses the maximum absolute standardized total overlap across lags 1–5.

The window statistic is the population SD of the 35 occurrence counts in an 80-draw interval. We separately estimated: (a) lower tail for the previously noticed fixed window #14268–14347; and (b) lower tail for the **minimum** count SD among all 21 contiguous 80-draw windows in this 100-draw archive, applying a within-sample look-elsewhere correction.

Monte Carlo: 50,000 independent 100-draw histories generated with NumPy PCG64 seed `20261029`, selecting each ticket by the five smallest of 35 independent continuous uniform values. This gives an *unbiased* without-replacement subset. All MC p-values use `(extreme_count + 1)/(50000+1)`.

## Executed results

| Test | Observation | p-value |
|---|---|---:|
| 100-draw overall frequencies | adjusted Pearson χ²(34) = **17.068**, number-count range 10–21, unusually even | lower-tail MC **0.00672**, asymptotic **0.00686** |
| Previously identified 80-draw window #14268–14347 | population count SD **2.12852** | fixed-window lower-tail MC **0.00234** |
| Most even 80-draw window in this 100-draw archive | #14264–14343, population count SD **2.01828** | **21-window-scan MC 0.00588** |
| Adjacent draws | overlap counts: 0×43, 1×40, 2×15, 3×1, 4×0, 5×0; overlap sum **73** for 99 transitions | no standout |
| Lags 1–5 | totals **73,84,73,66,58**, maximum absolute z = **1.924** at lag 2 | search-adjusted MC **0.2514** |

All numerical values and simulation metadata appear in `extra5_serial_window_results.json`; the code is `extra5_serial_window_audit.py`.

## Scientific interpretation

**The underdispersion reproduces on draw-level records and survives correction for the 21 overlapping 80-draw windows within this local 100-draw dataset.** This is a valid descriptive anomaly for this chosen archive, not proof of a nonrandom mechanism. Researchers chose this time period after examining historical snapshots; searching many other time periods, tests and sources could produce an equally extreme result by coincidence. The report does not adjust for that larger selection process. The 100-draw sample is small and third-party sourced.

**No detected serial-overlap anomaly at lags 1–5**, and the outputs cannot distinguish correct unbiased RNG/sampling methods or reconstruct an internal state/seed.

## Next falsification steps

1. Obtain an *independent, non-overlapping* 100-draw historical control interval from verified operator data, and run exactly this frozen set of tests without retuning.
2. Obtain a much larger authoritative date-ordered archive, with reliable draw identifiers and provenance; evaluate dispersion across fixed, disjoint blocks (not only the currently selected 21 windows), using familywise calibration over the complete archive.
3. Independently check all 100 current draw records against official source data before strengthening claims.
4. If any stable departure persists, test explicitly defined mechanisms (e.g. marginal balancing between draws), with independent prospective data; avoid claims about actual source code without documentary evidence.

No CI and no operational forecasts.