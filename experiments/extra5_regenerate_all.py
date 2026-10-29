#!/usr/bin/env python3
"""Rebuild all derived EXTRA 5 experiment outputs locally, without CI or network access.

Runs deterministic numerical experiments from the committed 100-draw archive.
Preexisting figures, scores, JSON diagnostics and descriptive report may be overwritten.
"""
from pathlib import Path
import subprocess
import sys

BASE=Path(__file__).resolve().parent
def run(*args):
    command=[sys.executable,*args]
    print("RUN", " ".join(command),flush=True)
    subprocess.run(command,cwd=BASE,check=True)

if __name__=="__main__":
    run("extra5_reproducible_audit.py","--mc","100000","--output","extra5_audit_results.json")
    run("extra5_sampler_forensics.py")
    run("extra5_last20_simulation.py")
    run("extra5_add_diagnostics.py")
    run("extra5_mass_algorithm_benchmark.py")
    run("extra5_mass_algorithm_calibration.py")
    run("extra5_render_figures.py")
    print("Complete. The binary Monte Carlo mask cache was created at",
          BASE/"extra5_mass_algorithm_holdout_masks.npz")
