# EXTRA 5 — Five-year authoritative-archive research (2022–2026)

**Status:** Dataset integration and fixed-configuration PRNG evaluation completed. **No deployed generator or secret state recovered.** This is independent research, not an operator-endorsed forecast.

## New evidence

Five user-provided authoritative spreadsheets are normalized into a single chronological archive of **3,526 consecutive draws**, #10832–#14357, starting at 15:00 2022-01-01 and ending at 19:00 2026-10-29 (Europe/Athens scheduled local times). Three header rows are ignored in each workbook. The 2022/2023 worksheets have large formatted but empty ranges; only actual rows with valid IDs count as draws.

| Year | Count | Draw IDs |
|---|---:|---|
| 2022 | 730 | 10832–11561 |
| 2023 | 730 | 11562–12291 |
| 2024 | 732 | 12292–13023 |
| 2025 | 730 | 13024–13753 |
| 2026 | 604 | 13754–14357 |

Each CSV row saves workbook number-column order in `n1..n5` and ascending order in `s1..s5`. **Workbook order has not been independently certified as the generator's extraction order.** The `lex_rank` column is the 0-based ascending lexicographic rank of the unordered set among all C(35,5)=324,632 tickets.

We verified zero missing draw IDs, zero duplicate IDs/dates/times, two expected draws per day, zero invalid tickets, correct 2024 leap-year handling, and exact agreement with the earlier 2026 normalized archive (including corrected #14249 = 2,4,30,33,35).

## Executed experiments

1. `seeded_prng_five_year.py`: **1,080 concrete** (PRNG, seed rule, sampler) configurations from the original `timestamp_prng_scan.py` library. Train/select ONLY on 2022–2024 (2,192 draws); freeze the single best before looking at 2025 and 2026 outcomes. Search-corrected Monte Carlo uses 400 full-family fair-ticket replications. The frozen winner is `splitmix64 + epoch_minute(offset=-60) + combinadic24` with 1,692 initial matching numbers. The winner generated **538 matches in 2025** (vs 521.43 expected) and **442 in 2026** (vs 431.43 expected), with **no exact tickets** in either year. 2025+2026 combined chance one-sided p = **0.160465**; the selection-stage familywise p = **0.097257**. These results are not strong evidence of a true implementation match.
2. `five_year_randomness_audit.py`: full archive Monte Carlo for global count balance, worst number deviation, maximum pair, year-specific frequency heterogeneity, rank-bin statistics, repeated tickets, consecutive numbers, serial overlaps across six lags; conditional position and afternoon/evening permutations. Results (`five_year_randomness_results.json`) do **not** reach a familywise 5% rejection threshold. Nominal uncorrected p-values for maximum pair and workbook-position structure are near 0.05, but disappear under the declared Bonferroni across 10 summary families.
3. `five_year_followup.py`: exact five-of-35 hypergeometric overlap probabilities, and an **explicitly exploratory** scan of the most frequent unordered pair in each of five years. The 2022 pair (4,8) occurred 29 times (expected 12.27, fixed-pair raw p ≈2.75e-5); correcting via 2,500 Monte Carlo simulations that scan all 595 pairs in all five years gives familywise **p ≈ 0.06477**. Not statistically compelling; no prediction or RNG fingerprint established.
4. `test_five_year.py`: **15 local unit tests**, including independent exhaustive 324,632-combination rank verification, known SplitMix64 output vectors, frozen-model prediction replay, year boundaries, dataset integrity, exact hypergeometric PMF tests and independent 2025/2026 scoring.

## Reproduce locally

Python 3.12+, `numpy`, `scipy`, `artifact_tool` for workbook input; no CI. To rebuild from original files, place the five `extra5_20XX.xlsx` workbooks in `/mnt/data`, or set `EXTRA5_INPUT_DIR` to their folder.

```bash
python prepare_five_year.py
python seeded_prng_five_year.py --calibration 400
python five_year_randomness_audit.py --reps 1000 --order-reps 1500
python five_year_followup.py
python -m unittest discover -s . -p 'test_five_year.py' -v
```

`selected_generator_PRE_EVALUATION.json` is create-once: the fitting program refuses to overwrite it when a regenerated selection differs. It trains from `train_2022_2024.csv` and generates later predictions using only `evaluation_calendar_2025_2026.csv` before freezing; only then does it open the combined outcome-bearing archive. Calendar metadata is predictable and is not outcome leakage. All historical results were already publicly available, so **this is retrospective temporal validation**, not a prospective blind test.

The provided workbooks are input provenance and are not reproduced wholesale in the Git repository. `provenance.json` contains individual input SHA-256 hashes and the normalized CSV hash. Original historical prediction locks remain untouched.

## What would constitute evidence of the actual RNG?

An independently authenticated production generator specification, its exact output-to-ticket mapping, key/seeding and entropy schedule, and a reconstructible internal state (or robust pre-reveal predictive success) are needed. The current [Allwyn EXTRA 5 description](https://allwyn.cy/en/games/extra-5/more-about/) confirms electronic draws with a certified RNG. The [OPAP 2020 Integrated Report](https://investors.opap.gr/~/media/Files/O/Opap-IR/06022020/Integrated%20Report%202020%2016062021%20compressed.pdf) describes independent secure cryptographic generators for EXTRA 5, KINO and SUPER 3. Neither source identifies a current SplitMix64 implementation or publishes the production seed.

The five-year archive contains at most 3,526 × log2(C(35,5)) = **64,555.58 bits** of unordered ticket information; if workbook order is actually extraction order, the ceiling is 88,909.28 bits. These are observation alphabets, **not** bits of recoverable secret state. Secret external entropy may make future outputs information-theoretically independent of past tickets.

See [REPORT.md](REPORT.md) for the evidence and uncertainty ledger.
