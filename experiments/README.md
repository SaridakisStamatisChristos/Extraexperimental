# Experiment artifact index

All archived experiments were performed or recorded on 29 October 2026. Run the scripts from **this directory**; scripts resolve data relative to their source directory. Install project dependencies with `pip install -r ../requirements.txt` (versions may differ from the original execution).

| Experiment | Program | Archived analysis | Input/output |
|---|---|---|---|
| Full-history cumulative frequencies | `extra5_reproducible_audit.py` | `extra5_audit_report.md` | `extra5_audit_results.json`; `--draws extra5_last100_data.csv` adds draw-level tests |
| Sampling mapping forensics | `extra5_sampler_forensics.py` | `extra5_sampler_forensics_report.md` | `extra5_sampler_forensics_results.json` |
| 20-draw pilot | `extra5_last20_simulation.py` | `extra5_last20_research_report.md` | `extra5_last20_data.csv`, `extra5_last20_model_comparisons.csv` |
| 60-family mass experiment | `extra5_mass_algorithm_benchmark.py` | `extra5_mass_algorithm_research_report.md` | `extra5_last100_data.csv`, `extra5_mass_algorithm_scores.csv` |
| Multiple-search calibration | `extra5_mass_algorithm_calibration.py` | Section in mass report | requires mass benchmark generated JSON and NPZ bitmask cache |

**Run order:**

```bash
python extra5_mass_algorithm_benchmark.py
python extra5_mass_algorithm_calibration.py
```

The benchmark generates `extra5_mass_algorithm_results.json`, 9,360-row scores CSV and `extra5_mass_algorithm_holdout_masks.npz` in this directory; calibration then generates its Monte Carlo outputs and chart. The CSV included here is the recorded result from the original run. The **binary NPZ cache, PNG plots and certain generated JSON diagnostics were not transferred** to this repository; they are regenerable by the included primary scripts (except optional pilot figure diagnostics). See reports and project documentation for preserved numerical results. A synthetic demonstration file (`extra5_test_synthetic.csv`) is **not** lottery history; do not use it for empirical claims.

**Evidence:** The synthetic candidates are NOT the actual EXTRA 5 RNG system; no candidate showed reliable predictive ability or compromised a system. The 20 later historical draws were known before model evaluation; not prospective predictions.
