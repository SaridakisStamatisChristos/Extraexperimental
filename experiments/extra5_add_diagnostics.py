#!/usr/bin/env python3
"""Reproduce historical 20-draw Monte Carlo diagnostics and its primary PNG chart."""
import json
from pathlib import Path
import numpy as np
from scipy.stats import hypergeom
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = Path(__file__).resolve().parent
p = BASE / "extra5_last20_simulation_results.json"
r = json.loads(p.read_text(encoding="utf-8"))
count = np.array([r["observed"]["frequencies"][str(i)] for i in range(1, 36)])
mean = 100 / 35
chi2 = float(np.sum((count - mean) ** 2 / mean))
rng = np.random.default_rng(20261029)
reps, block = 100000, 1000
extreme_chi = 0
lower_chi = 0
extreme_max = 0
extreme_missing = 0
for _ in range(reps // block):
    freq = np.zeros((block,35), dtype=np.int16)
    for _ in range(20):
        idx = np.argpartition(rng.random((block,35)), kth=4, axis=1)[:, :5]
        np.add.at(freq, (np.repeat(np.arange(block),5), idx.ravel()), 1)
    sims = np.sum((freq - mean) ** 2 / mean, axis=1)
    extreme_chi += int(np.sum(sims >= chi2))
    lower_chi += int(np.sum(sims <= chi2))
    extreme_max += int(np.sum(np.max(freq, axis=1) >= np.max(count)))
    extreme_missing += int(np.sum(np.sum(freq == 0, axis=1) >= np.sum(count == 0)))
single = hypergeom.pmf(np.arange(6),35,5,5)
mass = np.array([1.0])
for _ in range(19):
    mass = np.convolve(mass,single)
shared = int(r["observed"]["consecutive_draw_overlap_total"])
r["draw_level_diagnostics"] = {
    "frequency_pearson_chi2": chi2,
    "frequency_chi2_monte_carlo_upper_tail": extreme_chi/reps,
    "frequency_chi2_monte_carlo_lower_tail": lower_chi/reps,
    "max_number_frequency_observed": int(max(count)),
    "max_frequency_monte_carlo_upper_tail": extreme_max/reps,
    "numbers_not_seen_observed": int(np.sum(count == 0)),
    "missing_numbers_mc_upper_tail": extreme_missing/reps,
    "consecutive_overlap_total": shared,
    "consecutive_overlap_exact_upper_tail": float(mass[shared:].sum()),
    "monte_carlo_draw_sequences": reps,
    "mc_rng_seed": 20261029
}
p.write_text(json.dumps(r, indent=2, ensure_ascii=False)+"\n",encoding="utf-8")
scores={x["algorithm"]:x["total_matches"] for x in r["comparison"] if x["sampler"]=="remove"}
names=["BBS","RSA-Rabin-style","DES-CFB","AES-192-CFB","ChaCha20","SHA256-counter","MT19937"]
fig,ax=plt.subplots(figsize=(11,5))
vals=[scores[name] for name in names]
ax.bar(names,vals)
ax.axhline(20*25/35,ls="--",label="Uniform random expectation: 14.29")
ax.set_ylim(0,23)
ax.set_ylabel("Matching numbers / 100 positions")
ax.set_title("EXTRA 5: uncalibrated RNG families, 20 published draws")
ax.tick_params(axis="x",labelrotation=25)
ax.legend()
fig.tight_layout()
fig.savefig(BASE/"extra5_last20_algorithm_comparison.png",dpi=170)
plt.close(fig)
print("Regenerated pilot diagnostics and chart:",p.name)
