#!/usr/bin/env python3
"""Render research plots from archived numeric inputs (does not fit RNG seeds)."""
from pathlib import Path
import csv, json, shutil
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE=Path(__file__).resolve().parent
FIGURES=BASE.parent/"figures"
FIGURES.mkdir(parents=True,exist_ok=True)
d=json.loads((BASE/"extra5_sampler_forensics_results.json").read_text())
counts=[int(d["number_counts"][str(i)]) for i in range(1,36)]
expected=d["draws"]*5/35
fig,ax=plt.subplots(figsize=(12,5))
ax.bar(range(1,36),np.array(counts)-expected)
ax.axhline(0,ls="--",label="Uniform expectation")
ax.set_xlabel("EXTRA 5 number")
ax.set_ylabel("Observed - expected appearances")
ax.set_title(f"Historical number-frequency deviations ({d['draws']:,} draws)")
ax.set_xticks(range(1,36))
fig.tight_layout()
fig.savefig(FIGURES/"extra5_frequency_deviations.png",dpi=170)
plt.close(fig)

tests=d["candidate_tests"]
fig,ax=plt.subplots(figsize=(9,5))
labels=[str(t["bit_width"])+" bit" for t in tests]
vals=[t["candidate_z"] for t in tests]
ax.bar(labels,vals)
ax.axhline(0,ls="--")
ax.set_ylabel("Observed minus candidate expectation (standard deviations)")
ax.set_title("Candidate modulo-35 mappings; hypothetical samplers, not production code")
fig.tight_layout()
fig.savefig(FIGURES/"extra5_sampler_forensics_plot.png",dpi=170)
plt.close(fig)

pilot=json.loads((BASE/"extra5_last20_simulation_results.json").read_text())
by_alg={}
for x in pilot["comparison"]:
    if x["algorithm"] not in by_alg or x["total_matches"]>by_alg[x["algorithm"]]["total_matches"]:
        by_alg[x["algorithm"]]=x
names=list(by_alg)
fig,ax=plt.subplots(figsize=(11,5))
ax.bar(names,[by_alg[n]["total_matches"] for n in names])
ax.axhline(20*25/35,ls="--",label="Uniform random expectation")
ax.set_ylim(0,24)
ax.set_title("Last 20 draws — strongest of two synthetic samplers by family")
ax.set_ylabel("Overlapping numbers / 100 positions")
ax.tick_params(axis="x",labelrotation=25)
ax.legend()
fig.tight_layout()
fig.savefig(FIGURES/"extra5_last20_algorithm_comparison.png",dpi=170)
plt.close(fig)

src=BASE/"extra5_mass_algorithm_comparison.png"
if src.exists():
    shutil.copyfile(src,FIGURES/src.name)
else:
    rows=list(csv.DictReader((BASE/"extra5_mass_algorithm_scores.csv").open()))
    scores=np.array([int(x["holdout_hits_20"]) for x in rows])
    fig,ax=plt.subplots(figsize=(10,5))
    ax.hist(scores,bins=np.arange(scores.min()-.5,scores.max()+1.5,1))
    ax.axvline(20*25/35,ls="--",label="Expected: 14.29")
    ax.axvline(17,ls=":",label="Train-selected: 17")
    ax.axvline(30,ls="-.",label="Post-hoc maximum: 30")
    ax.set_xlabel("Overlaps on last 20 draws")
    ax.set_title("9,360 synthetic configurations")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGURES/"extra5_mass_algorithm_comparison.png",dpi=170)
    plt.close(fig)
print("Figures regenerated at",FIGURES)
