# EXTRA 5 — Independent RNG Research Archive

**Research snapshot: 29 October 2026 · Greece · documentation and reproducible experiments**

This repository preserves an independent, exploratory investigation of the Greek **EXTRA 5 (5-of-35)** lottery draw process, its historically documented cryptographic RNG architecture, public draw statistics, and simulation experiments. The aim is **research, documentation and reproducibility**, not an assertion that the current production generator has been identified, compromised, or predicted.

> **Bottom line:** We have identified historical design components through academic papers, tested aggregate statistics and selected faulty sampling hypotheses, and benchmarked **9,360 synthetic RNG/sampler/seed configurations** against 100 recorded draws (80 model-selection, 20 retrospective holdout). **No configuration demonstrated reliable predictive power.** The 20 “holdout” results were already public and were not prospective forecasts.

## Findings at a glance

| Stage | Evidence | Result |
|---|---|---|
| Historical architecture | OPAP reports and researchers' publications | BBS, RSA/Rabin, DES-CFB, AES-CFB, physical entropy, generator mixing/switching discussed in historical designs. **2026 deployment unknown**. |
| Aggregate audit | Third-party cumulative frequency snapshots | 14,346 draws through 24 Oct 2026: adjusted chi-square(34) ≈ 37.99, p ≈ 0.292; no global frequency departure detected. |
| Exploratory short-window audit | Difference of cumulative snapshots, 80 draws | Very even appearance frequencies, lower-tail Monte Carlo p ≈ 0.003 **before correction for choosing windows retrospectively**. Requires independent replication. |
| Faulty sampler tests | 14,353-draw frequency snapshot | Naive 8-bit `x % 35 + 1` plus duplicate rejection strongly inconsistent with totals. This is **not** evidence the operator used that method. |
| 20-draw pilot | Seven illustrative RNG families × two samplers | Best model 20 matching numbers among 100 picks; chance-like once search is accounted for. |
| Mass comparison | 60 families, five samplers, up to 32 fixed seeds | 9,360 configurations; train-selected model scored 88/400 in earlier 80 and 17/100 in later 20, against 14.29 expected on a 20-draw holdout. |
| Post-hoc best of 9,360 | Latest 20 (already observed) | 30/100 overlaps; in 3,000 null search simulations, ≥30 occurred in 280 (~9.36% plus-one). **Not predictive evidence**. |

A “hit” in the simulations means a **number appearing in both an individual synthetic ticket and the historical draw with the same ID**, not an exact winning ticket.

## Repository layout

- [RESEARCH_LOG.md](RESEARCH_LOG.md) — chronological record of the investigation and decisions.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — historical RNG paper trail, separation between historical and current claims.
- [docs/METHODOLOGY.md](docs/METHODOLOGY.md) — statistical models, simulations, inference limits, reproducibility.
- [docs/DATA_PROVENANCE.md](docs/DATA_PROVENANCE.md) — draw windows, date/ID boundaries, source and transcription limitations.
- [docs/OPEN_QUESTIONS.md](docs/OPEN_QUESTIONS.md) — unknowns, proposed experiments, evidence needed.
- [experiments/](experiments/) — preserved Python scripts, draw CSVs, result JSON/CSV and research reports.

The main experiments:
1. [Aggregate audit](experiments/extra5_audit_report.md)
2. [Bitstream-to-number mapping](experiments/extra5_sampler_forensics_report.md)
3. [20-draw pilot](experiments/extra5_last20_research_report.md)
4. [60-family benchmark](experiments/extra5_mass_algorithm_research_report.md)

## Reproduce

Install Python 3 with `numpy scipy cryptography matplotlib sympy`. For the original mass run, run from the experiments directory:

```bash
cd experiments
python extra5_mass_algorithm_benchmark.py
python extra5_mass_algorithm_calibration.py
```

The benchmark regenerates the mass scores JSON/CSV and the cached per-draw bitmasks needed by the calibration script. For a complete local rebuild, use `cd experiments && python extra5_regenerate_all.py`. Regenerated PNG and SVG figures are stored under `figures/`. Other experiments:

```bash
python extra5_sampler_forensics.py
python extra5_last20_simulation.py
python extra5_reproducible_audit.py --draws extra5_last100_data.csv
```

If a generated intermediate is absent, run its producing script first. **There is deliberately no CI**.

## Research safeguards

1. **Historical hardware/software ≠ current Allwyn production installation.** Papers from researchers in the original project document historical configurations, not 2026 keys, entropy, software releases or sampler details.
2. A fair `5/35` draw selects one of `C(35,5) = 324,632` combinations uniformly. Correct unbiased sampling schemes may be observationally indistinguishable from published unordered draws.
3. Aggregate frequency tests are not tests of cryptographic security. Apparent patterns in a searched archive require selection/multiple-comparison correction.
4. Model scores are **retrospective descriptive comparisons**. Fixed artificial seeds do not recover secret seeds; searching enough candidates produces striking matches by chance.
5. Third-party draw transcriptions and snapshots should be reconciled against authoritative operator records before stronger conclusions.

## Public references

- Bikos, Nastou, Petroudis & Stamatiou (2023), *Random Number Generators: Principles and Applications*, [Cryptography 7(4):54](https://doi.org/10.3390/cryptography7040054).
- Konstantinou, Liagkou, Spirakis, Stamatiou & Yung (2004), *Electronic National Lotteries*, [Financial Cryptography proceedings](https://doi.org/10.1007/978-3-540-27809-2_18).
- [OPAP Integrated Report (2023)](https://media.opap.gr/OPAPIntegratedReport202327082024.pdf), p. 104.
- Historical draws: [numerics.gr EXTRA 5 results](https://numerics.gr/extra-5/kliroseis-apotelesmata).
- Historical aggregate statistics: [Foufos EXTRA 5](https://www.foufos.gr/en/stats/extra).

**Status:** documented exploratory research; no identified live RNG, compromise, or betting advantage. Independent, unofficial project; not affiliated with Allwyn/OPAP.


## Algorithm-first historical reconstruction (Step 6)

A **working modular reference implementation** of the publicly described eLottery components is now available: [historical engine](experiments/extra5_historical_engine.py), [17 local unit tests](tests/test_historical_engine.py), [fidelity/limitations specification](docs/RECONSTRUCTION_IMPLEMENTATION.md), and [local test record](experiments/extra5_historical_engine_test_results.json).

It models BBS, RSA-style parity generation, AES-192/DES-compatible/CAST-128 CFB, the published modified M/B bit mixers, XOR and explicit switching. **The final 5/35 number sampler, physical entropy and seed wiring, CFB settings, and live 2026 configuration are unknown; all demonstration draws are synthetic.** No CI has been added.
