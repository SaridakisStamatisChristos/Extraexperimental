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
- [Reference engine](../experiments/extra5_historical_engine.py): `BBS`, `RSAParity`, `CFBZeroBits` (AES-192 / DES-compatible / CAST-128), published modified `mixer_m` and `mixer_b`, XOR, explicit `Route` / `RoutedBits.configure()` switching, a mathematical Naor–Reingold evaluator and an XOR helper for user-supplied entropy sample bytes.
- [17-case test suite](../tests/test_historical_engine.py): modular arithmetic differential checks, published M/B comparison across exhaustive small bit strings, 60-byte CFB independent reference checks for the three ciphers, rejection sampler and route tests, and deterministic demonstration streams.
- [Implementation and fidelity specification](RECONSTRUCTION_IMPLEMENTATION.md), plus [local test record](../experiments/extra5_historical_engine_test_results.json).

**Executed evidence:** Python 3.13.5, cryptography 46.0.4; `python -m unittest discover -s tests -p 'test_historical_engine.py' -v` executed locally with **17 tests, 0 failures and 0 errors**. Byte-compiled and executed the demonstration routes. This is a source-level implementation check, not CI or an independent clone-based check.

**Reproduce without CI:**

```bash
python -m pip install -r requirements.txt
python experiments/extra5_historical_engine.py --operation m --names bbs aes --draws 3
python experiments/extra5_historical_engine.py --operation xor --names bbs rsa des aes --draws 3
python experiments/extra5_historical_engine.py --operation single --names cast --draws 3
python -m unittest discover -s tests -p 'test_historical_engine.py' -v
```

**What is source-grounded:** historic BBS/RSA-style parity generation, DES/AES cipher-based generators, CAST-128 variant documented by the original developer for 2001–2002, modified paper M/B pseudocode, XOR family, optional generator switching. The earlier [published mixer](../experiments/extra5_published_mixers.py) remains untouched.

**What remains a hypothesis:** demo parameter values, BBS/RSA initialization conventions and secrecy, CFB full-block segment length and bit order, key and IV provenance, mixer block size (set to 256 bits as a test choice), buffer handling on switch, the complete entropy/Naor–Reingold seed chain, reseeding cadence, generator-selection schedule, and the final **five-without-replacement sampler**. The reference sampler uses unbiased bit rejection plus sequential removal solely as an interface placeholder. Sample outputs are synthetic and not purported to be any past or future operator draw.

**Research constraint:** a working historical-family reconstruction is NOT evidence that the current Allwyn production software uses this exact configuration and it does not recover production keys, seeds or forecasts. The reference module is deliberately not production cryptographic software.

**Next checkpoint, priority:** retrieve Vasiliki Liagkou's original thesis and the Financial Cryptography 2004 full text; search for the *exact bitstream-to-five-in-1..35 conversion*, explicit CFB segment sizes, original number-generation order, seed/IV initialization, route switching and any CAST-128→AES revision evidence. For each documented detail, add a new source-pinned profile or regression vector while leaving all hypothetical settings explicit. No CI.


## 2026-10-29 continuation — Step 7: seed, switching and 5-of-35 pipeline (IMPLEMENTED)

**User direction:** reconstruct the *underlying algorithms*, not more number-frequency or arbitrary-seed fitting. Preserve this direction for every future continuation.

**Source confirmation:** Bikos et al. (2023), *Cryptography* 7(4):54 §§5.2–5.3.5 describes a Generator/Verifier, coupon-file hash binding, XORed physical sources or an optional previous-state path, Naor–Reingold pseudorandom function, four RNG families (BBS, RSA/Rabin, DES and AES), mixing via published M/B/XOR and switchable generator combinations. The original developer's older CV lists CAST-128 in place of AES. None of this confirms the exact 2026 Allwyn production stack.

**Committed code:**
- [extra5_seed_switch_protocol.py](../experiments/extra5_seed_switch_protocol.py) — reference pipeline: XOR input, coupon binding, toy NR evaluator and explicit hypothetical key/IV expansion; instantiate BBS/RSA/DES/AES components; explicit per-draw route; three plausible **UNCONFIRMED** 5-of-35 samplers; demonstrative Generator/Verifier reproduction and checksums.
- [test_seed_switch_protocol.py](../tests/test_seed_switch_protocol.py) — dedicated regression, adversarial-input, 31-route and 324,632-combination mapping tests.
- [SEED_SWITCH_SAMPLER_FIDELITY.md](SEED_SWITCH_SAMPLER_FIDELITY.md) — evidence classification per component, full list of assumptions, mathematical mapping proof, reproduction commands.

**Design detail:** four independent sources permit **31 route structures** described by the 2023 paper: 4 single + 4 B + 12 ordered M + 11 XOR groups. This counts supported *types*, not the actual deployed route schedule. One uniform sampler maps a 19-bit rejection-sampled rank bijectively into `C(35,5)=324632` combinations. The correct mathematical distribution does **not** identify that sampler as the real one.

**Local execution evidence:** a full working development version of this pipeline was exercised together with the earlier historical engine, passing **44 local tests (27 new + 17 prior)**, including exhaustive five-subset unranking and all 31 routes. The committed compact implementation/test pair has not yet been independently exercised from a fresh clone; do **not** call the commit CI-verified or release-certified.

**Unresolved:** operator coupon-file encoding/hash, original NR secret parameters, real physical-noise samples and seed/previous-state behavior, NR-result-to-generator-key derivation, cipher mode segment width, route switching and buffer handling, exact winning-number conversion order/algorithm, historical CAST-128→AES revision evidence, and current certified production version. The reference values (NR p=23,q=11; SHA-256 coupon digest; SHAKE-256 labeled expansion; 256-bit mixer block; per-draw resets; SHA-256 toy receipts) are **didactic assumptions**, not recovered implementation facts. Existing state-derived input is modeled as reseeding rather than uninterrupted internal PRNG continuation.

**Next checkpoint:** focus on source acquisition for the original thesis and 2004 specification; implement versioned source-backed profiles only when evidence supplies explicit missing choices. Test the committed pair from a clean clone if a repository runtime becomes accessible. Do not add CI (user instruction). Do not claim statistical prediction.

## 2026-10-29 continuation — Step 8: seeded end-to-end generator replay (EXECUTED)

**User request:** seed the previously implemented historical cryptographic generator families and compare their actual synthetic output against recorded EXTRA 5 results; focus on identifying algorithms rather than generic frequency scans.

**Committed sources and documentation:**
- [Reproducible seeded replay](../experiments/extra5_seeded_replay.py) (uses the existing historical engine + seed/switch modules).
- [Research results and interpretation](SEEDED_GENERATOR_BENCHMARK.md).
- Input: [100 draw records](../experiments/extra5_last100_data.csv) (#14256–14355, 28 October 2026 cutoff). The old 80/20 split is **retrospective pseudo-holdout**, not unseen future data.

**Actual local execution:**
- Eight public, artificial seed indices (0–7), two assumed per-draw seed policies (fresh SHA-derived entropy pair or SHA-derived prior-state chain), 31 fixed historical-family routes plus two explicit hypothetical switching schedules, and three unbiased 5/35 sampler hypotheses.
- **1,584 attempted configurations. 1,479 completed; 105 hit a bounded 1,024-bit consumption safety limit** (mostly toy RSA/BBS bit-period issues in rejection samplers; do not attribute to deployed systems).
- Best selected solely by the first 80 draw overlaps: seed 0, chained-state assumption, fixed published `M(aes,bbs)` mixer, duplicate-rejection sampler; **80/400 first 80, 21/100 last 20**. Exact last-20 winning tickets: **zero**.
- Best selected *after looking at* last 20: same seed/mixer but sequential-removal sampler; **64/400 first 80, 25/100 last 20**. Exact last-20 winning tickets: **zero**.
- Draw #14355 actual `4,14,15,19,27`; training-selected output `1,11,13,28,34`; hindsight-selected output `1,12,13,20,30`; **zero overlap for either**.
- 3,000 iid fair 20-draw null histories were each scanned against all 1,479 successful candidate sequences. **2,735** had some candidate score **at least 25**. Smoothed family-wise probability **p=0.911696**; expected best after broad search is already around 26 matches.
- Benchmark source compiled and locally executed. Eight new supporting tests passed; across original historical-engine, seed-switch and benchmark tests **52 local tests passed**.
- A second independently written **compact rerun using the GitHub reproducer's algorithm** exactly reproduced attempted/completed configurations, model selection, overlaps and 2,735/3,000 null calibration. GitHub code is therefore checked against a separate local implementation.
- **Not disclosed/recovered:** the real physical entropy, historical coupon bytes, secure Naor–Reingold secret key, original BBS/RSA security-size parameters, per-draw switching, exact bit mapping, live 2026 software version. **No draw was recovered exactly; no prospective prediction or betting advantage exists.**

**Reproduction:** `pip install -r requirements.txt` then `cd experiments && python extra5_seeded_replay.py --seeds 8 --null-replicates 3000` (generates detailed CSV and JSON locally; no CI).

**Next checkpoint:** move from synthetic seed sweeps to **documentary protocol recovery**. Seek full Vasiliki Liagkou thesis, original FC2004 and ISC2005 lottery papers, exact CFB segmentation/initialization, NR input serialization, actual generator-selection protocol and output-to-five conversion. Cite concrete code-level evidence before changing source-derived components. Preserve uncertainty about 2026 production. Further arbitrary seed sweeps will not identify a properly entropy-seeded CSPRNG.

**Step 8 evidence:** EXECUTED deterministic historical replay and independent equivalent rerun; statistical calibration EXECUTED; production algorithm attribution UNVERIFIED; exact win reproduction and forecast NOT DEMONSTRATED. No CI.

### Step 8 addendum — independent reproducibility confirmation and archived records

- The committed compact source [`extra5_seeded_replay.py`](../experiments/extra5_seeded_replay.py) was run independently at the complete **8-seed / 3,000-null-history** settings; results **exactly agreed** with the original local long-form benchmark on all candidate counts, selected model outcomes, and the Monte Carlo exceedance `2735/3000`.
- The **1,479-row score CSVs are byte-identical across the two local implementations**, SHA-256 `86d9a47e992923e689308a2242083e14fb070c96dbd728e5a22f20a5304cc174`. This full CSV is regenerated on demand by the committed code; **it is not currently committed as a raw CSV**.
- Machine-readable [observation checkpoint](../experiments/extra5_seeded_replay_observations.json) now preserves exact counts, both selected candidates' **20 historical prediction sequences**, null calibration and the score checksum. Dataset SHA-256 `a5a78e5cb4b3c50023cfe6fe179911a19d3b9598b33afcd930ac8aabcfb2c5e4` was calculated on the local snapshot.
- [Local-only regression tests](../tests/test_seeded_replay.py) added; **59 tests passed in total locally** across the existing historical engine, pipeline, seeded original-benchmark tests and replay tests. No CI or workflow added.
- No conclusion about live Allwyn keys/software or prospective prediction changes.

## 2026-10-29 continuation — Step 9: expanded seeded replay (EXECUTED)

- User requested more seed experiments. Ran public synthetic seed indices **0–127** (same seed domain, 31 fixed routes + 2 switching schedules, 2 seed policies, 3 samplers); **25,344** attempts, **23,343** completed, **2,001** failed 1024-bit sampler budget.
- Cached locally executed engine was regression-checked against previous eight seeds: 1,479 completed-model rows and the full scores CSV **byte-identical**; local total **64 tests passed**.
- Highest first-80 training score: **85/400** for index **86**, previous-state, XOR(BBS,RSA,DES), sequential sampler; later-20 result only **12/100** (fair expectation 14.29).
- Highest later-20 **post-hoc** score: **29/100** for index **17**, previous-state, XOR(BBS,DES), combination-rank sampler; training 47/400. Across **1,200** fair null histories searched over all **23,343** completed models, **648** attained >=29; corrected p≈**0.5404**. No candidate matched a full 5/5 ticket in later 20.
- Full locally produced 23,343-row score CSV SHA-256: `aa6957f68853af23e4cadeb48cf86decc2d98c437910df58e26143aa80510c81`; output regenerable from existing [seeded replay code](../experiments/extra5_seeded_replay.py) using `--seeds 128 --null-replicates 1200`, though full re-execution with this slower original version was **not** performed. See [full report](EXPANDED_SEED_SWEEP.md) and [machine-readable summary](../experiments/extra5_seed_128_results.json).
- **Verdict:** no evidence of recovered live seed or predictive power; retrospective pseudo-holdout already publicly known. A much larger *arbitrary* seed search does not reveal a CSPRNG's inaccessible physical-entropy and key state. Next task remains original protocol/seed documentation. No CI.

**Step 9 evidence:** 128-index experiment EXECUTED locally, 1,200 null simulations EXECUTED, 64 tests PASS; real seed identification NOT DEMONSTRATED.

### Step 9 — Complete artifact archival (verified Git blobs)

- Supersedes the earlier Step 9 note that the large CSV and optimized script were not committed.
- The **exact locally executed** optimized [seed sweep](../experiments/extra5_seed_sweep.py), [full 23,343-row scores](../experiments/extra5_seed_sweep_scores.csv), [detailed results JSON](../experiments/extra5_seed_sweep_results.json), [report generator](../experiments/extra5_seed_sweep_report.py), and [five new local regression tests](../tests/test_seed_sweep.py) are now committed to the repository. Git blob hashes were compared to the local source files before attaching them to the main branch.
- Full CSV SHA256 **`aa6957f68853af23e4cadeb48cf86decc2d98c437910df58e26143aa80510c81`**; the new code was executed locally and matched all earlier 8-seed outputs byte-for-byte. The previously stated 64 passing local tests include the five new tests that are now archived.
- Reproduce exactly: `cd experiments && python extra5_seed_sweep.py --seed-start 0 --seed-stop 128 --null-replicates 1200 --out .`; then `python extra5_seed_sweep_report.py --results extra5_seed_sweep_results.json --out ../docs/EXPANDED_SEED_SWEEP.md`.
- **No prediction, live Allwyn entropy, secret key or production seed recovered. No CI added.**

## 2026-10-29 continuation — Step 10: requested 180/200 score (EXECUTED; NOT REACHED)

- User requested Trillion Protocol, C³ and O3 Shell approaches plus maximum effort to raise the match score to **180/200**. Interpreted as **180 individual overlapping numbers across 40 five-number draw predictions**; 180/200 is a user target, not a previously achieved benchmark.
- Ran the **same** reconstructed historical generator routes/synthetic seed hypotheses as Step 9 with **60 earlier draws for selection and 40 later publicly known draws for hindsight validation**. All 23,343 completed models' prior 80/20 scores were individually cross-checked against the previous committed CSV; no model or seed semantics were changed. The run used five batches after multiprocessing stalls.
- **Attempted 25,344, completed 23,343, 2,001 failed** the bounded sampler. Preselected on first 60: seed 0, M(AES,BBS), previous-state, distinct-rejection: **66/300 first60, 35/200 last40**. Post-hoc best: seed 23, XOR(BBS,RSA,AES), previous-state, sequential sampler: **43/300 first60, 48/200 last40**. One retrospective exact 5/5 match existed among the model bank's later-40 tickets, but no future match was predicted. **No 180/200 configuration**.
- Full 23,343-row dataset: [extra5_target_180_scores.csv](../experiments/extra5_target_180_scores.csv), SHA256 `059e32d34970301ee2d821d0e2a8ff51fe89ec00a007e9977561d7789ab8878b`. [Detailed report](TARGET_180_RESEARCH.md), [results JSON](../experiments/extra5_target_180_results.json), [simple replay](../experiments/extra5_target_180_replay.py), [exact combinatorial probability](../experiments/extra5_180_probability.py).
- **Mathematical fact conditional on iid uniform results:** fixed-model P(≥180/200) **2.407762919×10^-165**; valid 23,343-candidate fixed-model union bound ≤**5.62044098×10^-161**. A historically selected model's 35/200 is compatible with chance (p≈0.103); post-hoc 48/200 is not evidence of a valid predictor after thousands of comparisons.
- Simple independent replay of the first two seed indices reproduced all 368 completed scores and model identities; full 128-index second-implementation replay not run. An exact mathematical reference implementation and tests are archived. A 40-draw familywise Monte Carlo calibration was not run; no forward outcomes were tested.
- **NEXT:** Stop arbitrary synthetic-seed scaling as a path to a claimed 180/200 result. Investigate original physical-entropy/seeding protocol, actual generator/software version, private-state unavailability and the real five-number sampler; only source-backed hypotheses deserve another seed search. If a predictive claim is proposed, freeze its code and settings *before* future draw results appear.
- **Status:** TARGET NOT REACHED; PRODUCTION ALGORITHM NOT IDENTIFIED; NO FORECAST ADVANTAGE; NO CI.

## 2026-10-29 — Step 11: walk-forward fitting and an immutable forward draw test

**User directive:** fit draw sequences to an algorithm, then inspect the next draw. Do not confuse a perfect historical fit with recovery of the cryptographic generator.

**Executed:** [walk-forward model benchmark](../experiments/extra5_walkforward_fit.py), [full scores and per-draw predictions](../experiments/extra5_walkforward_fit_results.json), [report](EXTRA5_WALKFORWARD_PRECOMMIT.md), [exact-fit counterexample](../experiments/extra5_exact_fit_counterexample.py), [counterexample outputs](../experiments/extra5_exact_fit_counterexample_results.json), [7 regression tests](../tests/test_fit_prediction.py). All **7 new tests passed locally**; entire previous suite has not been rerun in this checkpoint.

- Input precisely 100 draws **#14256–14355** (SHA256 **a5a78e5cb4b3c50023cfe6fe179911a19d3b9598b33afcd930ac8aabcfb2c5e4**). The next 15:00 draw #14356 is *not present* in the data and is *not* used.
- Candidate family: 12 sequential fitting models, including smoothed counts, exponential weighting, mean reversion, lag-2 transition models, neighbor matching and ridge regression.
- Model choice based **only on 30 historical forward predictions** (target #14286–14315), minimizing average multi-label Brier score. The selected `cold` model uses shrinkage and inverse historical frequency (mean reversion).
- In a subsequent chronological 40-draw retrospective walk-forward evaluation, **two-draw-ahead** targets #14316–14355, refitting at each step without seeing the last unobserved outcome, `cold` scored **39/200 individual number overlaps**, versus fair expectation **28.571/200**. Conditional fixed-model exact one-sided null p≈**0.018859**; Brier **4.26607**, uniform **4.28571**. **Do not claim discovery**: the entire historical research archive, two horizon choices, family of models and window selection were not preregistered, and these draws were public during research. In the one-ahead secondary test `cold` scored **37/200** (p≈0.0471), not independent corroboration.
- Mathematical non-identifiability: a finite-field interpolation polynomial fits all **100/100** historical five-number tickets exactly; adding a polynomial vanishing at all observed draw IDs permits *any next ticket* with the same historical fit. Demonstrated two incompatible #14357 outputs under equally perfect fitting algorithms.
- **Actual time-stamped prospective checkpoint:** [extra5_draw14357_precommit.json](../experiments/extra5_draw14357_precommit.json) fixes the two-step forecast for draw **#14357 (29 Oct 2026, 19:00 Europe/Athens)** to **2, 11, 13, 14, 35**, with last available actual draw #14355; created locally at 2026-10-29 16:26:56+02:00. Canonical record SHA256 **c3059e8a186e4f204922d5e101529bff945f29590cc5e5ef5cf2b0143f6e1504**. **Never edit this precommit record after target publication.**
- Pending: check authoritative or corroborated public outcome for **#14357 after 19:00** and append a separate observed-result file with overlap and publication source; do not alter the prediction. One genuine draw is not sufficient to establish a reliable edge.
- **No CI** was added; current Allwyn RNG/seed remains unrecovered.

## 2026-10-29 — Step 12: one-draw synthetic seed fit with blinded historical reveal

- User gave **draw #14248**, date **5 September 2026**, results **13-16-22-30-31**, and **10,566 columns** (metadata only). The next consecutive draw **#14249** is blinded; its outcome was not searched or inspected.
- Implemented [single-draw seed search](../experiments/extra5_one_draw_seed_fit.py) based on the historically documented AES-192-CFB *family*. Public SHA512 seed index to key/IV, CFB128 segmentation, continuous stream, and 24-bit rejection/combinadic rank sampler are *hypotheses*, not current/historic operator configuration proof.
- Searched artificial seed indices **0..3,999,999**, obtaining **12 exact matching first tickets** (expected **~12.32** chance matches); all 12 yielded different second ticket combinations. **8 tests passed locally**, including exhaustive unranking of 324,632 combinations.
- Predetermined rule: select *lowest fitting numeric seed*, **1,231,545**. Model predicts **8-18-24-27-34** for #14249; [PRE-REVEAL IMMUTABLE LOCK](../experiments/extra5_draw14249_LOCKED_before_reveal.json) is committed in earlier commit **f218295f669fd9d556328d8ec57b4c2d86399915**. Do not modify lock after result is revealed.
- Details and all seed candidates are in [research report](BLIND_ONE_DRAW_FIT.md) and [machine-readable results](../experiments/extra5_blind_14249_fitting_seeds.json).
- **Critical distinction:** #14249 was publicly drawn long before this exercise; this is researcher-blinded retrospective evaluation, not truly prospective. Fitting one known lottery ticket by searching millions of seeds is expected under chance. No production seed or actual forecast capacity inferred.
- **Next step:** user reveals actual five numbers for #14249. Score the frozen first-seed prediction exactly; do not select another fitted seed after reveal. Then repeat on several independent user-hidden sequences without changing the model/seed, if possible.

## 2026-10-29 — Step 13: historical #14249 blind-result reveal (FAILED PREDICTION)

- User supplied **#14249**, drawn **5 September 2026**, numbers **2,4,30,32,35**, column count **10,010**; user-reported, not independently operator-verified in this step.
- Prior immutable commitment in [extra5_draw14249_LOCKED_before_reveal.json](../experiments/extra5_draw14249_LOCKED_before_reveal.json) at Git commit `f218295f669fd9d556328d8ec57b4c2d86399915`: seed index **1,231,545**, hypothetical AES-192-CFB continuous generator, predicted **8,18,24,27,34**. Predetermined lowest-exact-fit-seed rule preserved. **Blind result: 0/5**, no matching numbers. Chance for zero hits under independent uniform 5/35 = **0.4389770571**.
- All **12** pre-reveal fitted seeds were scored only *after* revelation: histogram **6×0, 5×1, 1×2** overlaps; seed 3,719,509 retrospectively scored 2/5, **not** a valid replacement for the precommitted prediction. [Full evaluation report](BLIND_14249_REVEAL.md), [machine-readable scores](../experiments/extra5_blind_14249_evaluation.json).
- Pre-reveal prediction and fitting results were **not edited**. Experiment outcome **FAILED to predict #14249**; no evidence of recovered operator state, cryptographic seed, or forecasting edge. Current status: source-family demonstration only; experimental KDF/CFB/sampler assumptions remain unresolved.
- NEXT: repeat the exact fixed protocol on a *different* pair of consecutive draw IDs held by user, with the target concealed until the prediction is committed; evaluate multiple independent pairs, report every miss. Avoid any target already included in public evaluation files and avoid picking the best seed after reveal.

