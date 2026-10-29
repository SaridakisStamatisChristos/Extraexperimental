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

## 2026-10-29 continuation — Step 4: implementation forensics, published M/B mixers (EXECUTED)

**Research priority changed at user direction:** identify the actual algorithms and code-level mechanisms; do NOT continue broad statistical distribution/seed-search sweeps unless they directly distinguish an implementation. The historical public results alone do not disclose per-draw secret entropy or configuration.

- Re-inspected primary source [Bikos et al. (2023), §§3.2–3.2.4, 5.2–5.3.5](https://doi.org/10.3390/cryptography7040054). Documented original eLottery sequence: physical entropy and/or evolving internal state; closed coupon file hash; Naor–Reingold processing; BBS, RSA/Rabin, DES-CFB and AES-CFB bit sources; selectable **XOR**, bitwise **M** and **B**, dynamic optional switching; generator/verifier cryptographic commitment.
- **New algorithm-level source evidence:** section 5.3.5 publishes precise pseudocode for binary M and B mixers. Committed literal [Python reconstruction](../experiments/extra5_published_mixers.py), [exhaustive results](../experiments/extra5_published_mixers_results.json), and [technical note](../experiments/extra5_published_mixers_report.md).
- **B observation and proof:** in its main loop, `i=X[j]`, `out[j-2]=V[i]`, `V[i]=X[j]`. Since bits are only 0 or 1, each slot `V[b]` becomes `b` after its first use and stays there. The principal output is consequently a 2-position shift of X except at most two startup mismatches. Exhaustive B tests cover **32,764 possible inputs over lengths 2–14**, no violation.
- **M concrete counterexample:** X=001, Y=001 gives output 000 under published variant; input and output have different Hamming weights, so this bit-level construction is **not always a strict permutation**. That does not prove any compromised generator.
- **Outstanding implementation gap:** neither the inspected publication nor archived experiments establish the current 2026 generator revision, keys, seed, M/B selection, switching schedule, or *exact map from bits to five distinct integers in [1,35]*. Do not mislabel this historical reconstruction as a verified Allwyn production clone.
- **New documentary lead:** Vasiliki Liagkou's University of Patras thesis, [repository record](https://www.openarchives.gr/aggregator-openarchives/edm/nemertes/000009-10889_143), specifically studies the real lottery generation protocol; full text not yet acquired. This is a better next research source than random-number frequency testing.

**Next step:** seek thesis/full 2004 implementation specification and source-level final 5/35 sampler; construct a versioned module-by-module historical simulator with unambiguously labeled *source-confirmed* versus *hypothetical* transitions; only then consider tests that could distinguish implementations. User requested no CI.

**Evidence classification:** historical algorithm description SOURCE-VERIFIED; mixer analysis PROVED for main loop and EXHAUSTIVELY TESTED for finite lengths; 2026 deployment UNVERIFIED; prediction NOT CLAIMED.

## 2026-10-29 continuation — Step 5: original EXTRA 5 cipher identification (PRIMARY SOURCES)

- User explicitly prioritized **identifying the real algorithm** over statistical-frequency scanning. Preserve this as the principal task direction.
- NEW high-confidence historical source: the original designer Yannis C. Stamatiou's [2018 academic CV](https://www.bma.upatras.gr/images/new/encvstam2018.pdf), p.4 of PDF, **explicitly names the 2001–2002 EXTRA 5/SUPER 3 generators as BBS, RSA, DES and CAST-128**, plus three entropy sources (Zener diode, thermal resistor and motherboard clock) and Knuth M/B.
- VERSION DISCREPANCY: the author's [2023 peer-reviewed group paper](https://doi.org/10.3390/cryptography7040054) instead describes historical **BBS, RSA/Rabin, DES-CFB, AES-192-CFB** and libmcrypt 2.5.3. **CAST-128 vs AES cannot be silently harmonized.** A documented change of version is currently a hypothesis, not an established finding.
- Exact mathematical mechanisms from the 2023 publication: BBS `x←x² mod N; emit LSB`; RSA `x←x^e mod N; emit LSB`; cipher-feedback encrypting all-zero plaintext; Naor–Reingold function using combined physical-entropy and closed-ticket hash inputs; optional M/B/XOR mixing and generator switching. Actual **CFB segment width, keys, IVs, source/version, switching schedule and 5-of-35 bit sampler remain UNDISCLOSED**.
- The published **M/B implementation pseudocode** is already archived and independently exhaustively exercised at [extra5_published_mixers.py](../experiments/extra5_published_mixers.py); 8 additional local reference tests of BBS/RSA/NR/CFB/M/B also passed on 29 Oct but have not been pushed as a standalone repository module.
- NEW documentary lead: the University of Patras thesis by original researcher **Vasiliki Liagkou**, [catalog record](https://search.library.upatras.gr/Record/nemertes-10889-143/Details), likely relevant to exact historical protocol, but **full text not obtained**. Archive the evidence comparison in [GENERATOR_VERSION_EVIDENCE.md](GENERATOR_VERSION_EVIDENCE.md).
- Research direction: obtain full 2004 paper and Liagkou thesis; examine any precise 5/35 conversion, CFB mode configuration and version change; seek present-day current RNG certificate/supplier/technical documentation. **Do not claim live algorithm attribution or output prediction.**

**Step 5 evidence state:** 2001–02 design families DOCUMENTED BY ORIGINAL DESIGNER; later paper's architecture DOCUMENTED; 2026 version UNVERIFIED; no exact five-number draw reproduction achieved.


## 2026-10-29 continuation — Step 6: historical generator architecture reference implementation (LOCAL TESTS PASS)

**Change of focus:** algorithm identification and faithful source-based implementation, not additional RNG frequency surveys or arbitrary-seed lottery matching.

**Committed artifacts:**
- [Reference engine](../experiments/extra5_historical_engine.py): \`BBS\`, \`RSAParity\`, \`CFBZeroBits\` (AES-192 / DES-compatible / CAST-128), published modified \`mixer_m\` and \`mixer_b\`, XOR, explicit \`Route\` / \`RoutedBits.configure()\` switching, a mathematical Naor–Reingold evaluator and an XOR helper for user-supplied entropy sample bytes.
- [17-case test suite](../tests/test_historical_engine.py): modular arithmetic differential checks, published M/B comparison across exhaustive small bit strings, 60-byte CFB independent reference checks for the three ciphers, rejection sampler and route tests, and deterministic demonstration streams.
- [Implementation and fidelity specification](RECONSTRUCTION_IMPLEMENTATION.md), plus [local test record](../experiments/extra5_historical_engine_test_results.json).

**Executed evidence:** Python 3.13.5, cryptography 46.0.4; \`python -m unittest discover -s tests -p 'test_historical_engine.py' -v\` executed locally with **17 tests, 0 failures and 0 errors**. Byte-compiled and executed the demonstration routes. This is a source-level implementation check, not CI or an independent clone-based check.

**Reproduce without CI:**

\`\`\`bash
python -m pip install -r requirements.txt
python experiments/extra5_historical_engine.py --operation m --names bbs aes --draws 3
python experiments/extra5_historical_engine.py --operation xor --names bbs rsa des aes --draws 3
python experiments/extra5_historical_engine.py --operation single --names cast --draws 3
python -m unittest discover -s tests -p 'test_historical_engine.py' -v
\`\`\`

**What is source-grounded:** historic BBS/RSA-style parity generation, DES/AES cipher-based generators, CAST-128 variant documented by the original developer for 2001–2002, modified paper M/B pseudocode, XOR family, optional generator switching. The earlier [published mixer](../experiments/extra5_published_mixers.py) remains untouched.

**What remains a hypothesis:** demo parameter values, BBS/RSA initialization conventions and secrecy, CFB full-block segment length and bit order, key and IV provenance, mixer block size (set to 256 bits as a test choice), buffer handling on switch, the complete entropy/Naor–Reingold seed chain, reseeding cadence, generator-selection schedule, and the final **five-without-replacement sampler**. The reference sampler uses unbiased bit rejection plus sequential removal solely as an interface placeholder. Sample outputs are synthetic and not purported to be any past or future operator draw.

**Research constraint:** a working historical-family reconstruction is NOT evidence that the current Allwyn production software uses this exact configuration and it does not recover production keys, seeds or forecasts. The reference module is deliberately not production cryptographic software.

**Next checkpoint, priority:** retrieve Vasiliki Liagkou's original thesis and the Financial Cryptography 2004 full text; search for the *exact bitstream-to-five-in-1..35 conversion*, explicit CFB segment sizes, original number-generation order, seed/IV initialization, route switching and any CAST-128→AES revision evidence. For each documented detail, add a new source-pinned profile or regression vector while leaving all hypothetical settings explicit. No CI.
