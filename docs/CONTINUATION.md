# Continuation note for a future research conversation

**Repository:** https://github.com/SaridakisStamatisChristos/Extraexperimental  
**Snapshot:** 29 October 2026, Europe/Athens  
**Task:** Continue independent Greek EXTRA 5 (5/35) RNG research from this archival checkpoint.

## Suggested resume instruction

> Continue the EXTRA 5 RNG investigation using the GitHub repository `SaridakisStamatisChristos/Extraexperimental` as the canonical project record. Read `README.md`, `RESEARCH_LOG.md`, `docs/ARCHITECTURE.md`, `docs/METHODOLOGY.md`, `docs/DATA_PROVENANCE.md`, `docs/OPEN_QUESTIONS.md`, and `experiments/README.md` before changing claims or code. Preserve the historical simulations and exact limitations. Do not add CI unless specifically requested. Seek authoritative present-day implementation/certification evidence and source-verified chronological draw data. If running a new experiment, predeclare hypotheses and controls, correct for algorithm/seed searches, and make no predictive claims from historical-only fit.

## What was done

1. Traced historically documented architecture: BBS, RSA/Rabin, DES-CFB, AES-CFB, physical entropy and mixing mechanisms discussed by original-system researchers.
2. Audited cumulative historical frequencies: 14,346 draws to 24 October 2026, global p≈0.292. Short 80-draw interval appeared overly balanced (exploratory lower-tail MC p≈0.003, uncorrected for window search).
3. Rejected a specific *hypothetical* naive 8-bit modulo sampler on published historical counts; did not identify a live implementation.
4. Simulated seven RNG families and two samplers on 20 publicly known draws: best 20/100 overlap, not significant after search.
5. Simulated 60 RNG families, five sampling methods, up to 32 synthetic fixed seeds = **9,360 configurations** on 100 recorded draws. The model selected using the earlier 80 achieved **17/100** on the later 20; no credible advantage. Post-hoc maximum 30/100 occurred in ~9.36% of 3,000 fair-null searches across the candidate library.
6. Preserved the textual code, core reports, historical-draw datasets and full scores CSV. Recovered both missing JSON diagnostics and four plotted figures in PNG and SVG formats; the regenerable NPZ cache remains intentionally untracked. Use `python experiments/extra5_regenerate_all.py` after installing requirements.

## What has NOT been done

- No verified 2026 proprietary generator implementation, entropy source, algorithm switching schedule, sampling rule, internal state or source code.
- No demonstrated prediction, exploitation, manipulation, or true prospective out-of-sample advantage.
- No complete authoritative operator-certified chronological archive across all historical draws.
- No CI, GitHub Actions, or build/test automation, by user request.

## Priority next work

- Investigate regulator/operator/public procurement records and academic references for the exact current draw sampling mechanism.
- Verify draw timestamps, IDs and original order using the operator's historical records if available.
- Run preregistered serial-correlation, pair and rolling-window analysis over a validated complete archive. Account for look-elsewhere effects.
- If a plausible forecasting hypothesis is proposed, register the model and predictions **before** future results are public; score against an exact fair-lottery baseline.

**Scientific safeguard:** Similar output frequencies do not identify a cryptographic RNG. Large algorithm searches produce accidental hindsight matches. This is an independent, unofficial archive.

## 2026-10-29 continuation — Step 1: provenance and local data validation (EXECUTED)

- Repository state inspected: 41 tracked files on `main`; scripts, inputs, diagnostic JSON files, and PNG/SVG figures present; no CI requested.
- Examined `experiments/extra5_last100_data.csv` locally: 100 rows, consecutive IDs **14256–14355**, each sorted, each exactly five distinct integers within 1..35, no repeated IDs. `extra5_last20_data.csv` is a separately archived pilot input, not an additional 20 independent observations.
- Independent source spot-checks: **#14355 = 4,14,15,19,27** and **#14351 = 6,10,17,28,31** match [Allwyn Cyprus EXTRA 5 results](https://allwyn.cy/en/games/extra-5/draws-and-results/) and [Numerics historical results](https://numerics.gr/extra-5/kliroseis-apotelesmata). **#14256 = 6,10,21,29,32** and **#14259 = 1,11,20,27,30** also match the historical [Foufos public listing](https://www.foufos.gr/extra). Only selected records were externally spot-checked, not all 100.
- Important semantics: archived five-number sets are **sorted**; they do **not** preserve or prove generator emission order. A separate result page that displays an unsorted sequence does not establish that it is the RNG's original draw order.
- Initial serial diagnostic (descriptive, no conclusion yet): among the 99 adjacent pairs, overlap frequencies were `{0:43, 1:40, 2:15, 3:1, 4:0, 5:0}`, with mean **73/99 = 0.7374** versus fair-null expectation **5/7 = 0.7143**. Formal calibrated serial tests follow as Step 2.

**Step 1 evidence label:** file-integrity checks EXECUTED; selected source results CROSS-CHECKED; full authoritative data verification NOT DONE.

## 2026-10-29 continuation — Step 2: serial-overlap and 80-window scan (EXECUTED)

- New committed program: [extra5_serial_window_audit.py](../experiments/extra5_serial_window_audit.py), outputs [extra5_serial_window_results.json](../experiments/extra5_serial_window_results.json); methods and limitations in [extra5_serial_window_report.md](../experiments/extra5_serial_window_report.md).
- Under the **independent uniform 5-of-35** null, 50,000 Monte Carlo replicate 100-draw histories (seed 20261029, NumPy PCG64; draw 5 smallest of 35 iid uniform ranks) were generated. This run is **historical and exploratory, not preregistered**.
- Over 100 draws #14256–14355, count frequencies are *unusually even*: adjusted Pearson chi-square(34) = **17.068**; **lower-tail** Monte Carlo p = **0.00672** (upper-tail p = 0.993; do not mistake that for evidence of normal dispersion).
- Earlier noticed 80-draw interval #14268–14347 reproduces on raw draw records with population count SD **2.1285**, fixed-interval lower-tail Monte Carlo p **0.00234**.
- Allowing selection of the **minimum among all 21 overlapping 80-draw windows** in this 100-draw archive, the most even window is #14264–14343 with population count SD **2.0183**; within-this-archive search-adjusted Monte Carlo p = **0.00588**.
- The 99 adjacent overlaps have counts **0×43, 1×40, 2×15, 3×1** (sum 73, expectation 70.714). Lags 1–5 overlap totals: **73, 84, 73, 66, 58**. The maximum absolute standardized lag deviation was **1.924**; familywise null Monte Carlo p **0.2514**: no convincing detected short-lag signal.
- **Interpretation:** local underdispersion is a replicated descriptive observation but **not** established RNG bias, tampering, code attribution or forecastability. The 100-draw period itself was chosen retrospectively after examining historical data, and the test family/period were not selected prospectively; the 21-window correction does not cover the entire historical search space. Source records are only spot-checked, not all 100 verified against an authoritative operator export.
- **Priority next:** obtain an independently selected **non-overlapping prior 100-draw window**, preferably operator-verified, and apply the frozen script with the same statistic and directional hypotheses. The current script intentionally pins IDs 14256–14355 and must be parameterized for the new control window **without changing the statistical test**.

**Step 2 evidence label:** local experiment EXECUTED, 50,000 randomized null replicates; significance descriptive and selection-limited, prospective prediction NOT DONE.

## 2026-10-29 continuation — Step 3: archive-scale look-elsewhere correction (EXECUTED)

- Previous minimum in the 21 80-draw windows within 100 archived records: **#14264–14343**, appearance-count population SD **2.01828377**, integer squared-count sum **4714**.
- New reproducible code: [extra5_archive_scale_null.py](../experiments/extra5_archive_scale_null.py), [results](../experiments/extra5_archive_scale_null_results.json), [report](../experiments/extra5_archive_scale_null_report.md).
- **Fixed single 80-draw window:** under iid uniform 5/35, **188/200,000** null simulations as evenly balanced; smoothed lower-tail **p=0.000944995**. Independent second sampler using 120,000 generated windows obtained 128 extremes, consistent within sampling error.
- **Hypothetical full-lifetime retrospective search:** in a sequence of **14,355 independent synthetic draws**, there are **14,276 overlapping 80-draw windows**. Searching all such windows, **4,795/5,000** synthetic complete histories contained at least one window with squared-count sum <=4714 (smoothed **p=0.959008**; binomial 95% interval for observed fraction ~0.9531–0.9643).
- **Scientific correction:** the previously highlighted short-window underdispersion is rare for one fixed window but **very common somewhere within a sufficiently long lottery history**. The latest-100 sample's 21-window local p≈0.0059 is not a global search-corrected p. This severely limits interpreting the retrospective anomaly as evidence of RNG bias, algorithm identification or forecastability.
- **Important limitation:** no 14,355-draw actual archival dataset was obtained or analyzed for Step 3. The long-horizon run uses *synthetic* fair draws and an illustrative number of possible search windows, not an asserted reconstruction of the historical selection process. The true selection/search space is unknown. The actual independently selected older 100-draw control remains **not retrieved**.
- **Future checkpoint:** acquire 100 non-overlapping, source-verified earlier results; freeze the existing statistic and compare the new 80-window scan with the same null. After that, extend the real archive and perform one unified prespecified scan under proper correction. Continue pursuing documentation of current certified draw implementation. No CI.

**Step 3 evidence label:** simulations EXECUTED; independent sampling implementation cross-check EXECUTED; actual older-block replication NOT DONE; predictive claim NOT SUPPORTED.

