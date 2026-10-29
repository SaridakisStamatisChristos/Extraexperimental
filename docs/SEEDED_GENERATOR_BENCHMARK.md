# Step 8 — Seeded generator comparison (29 October 2026)

## Purpose

Test the **already implemented historical generator families** against the 100 archived Greek EXTRA 5 draws (#14256–14355). We generate explicit public synthetic seeds and compare output from the documented historical BBS/RSA parity/DES-CFB/AES-192-CFB family and published M/B/XOR mixers. **Not an identification of production keys or generator state.**

The original per-draw physical entropy, secret values, original coupon-file bytes, real seed-to-state mapping, current switching schedule and bit-to-number algorithm are unavailable. This study cannot directly reproduce the production system even if the generator families are correct.

## Protocol and executed results

The local benchmark used:

- **Eight fixed public seed indices:** 0–7; domain `EXTRA5-INDEPENDENT-SEED-SEARCH-v1|NOT-OPERATOR-SEEDS|`.
- **Two illustrative seed policies:** per-draw SHA256-derived pair of entropy samples; SHA256-based previous-state chain.
- **33 route schedules:** 31 fixed published-family structural M/B/XOR/single routes, plus two arbitrary switching schedules.
- **Three explicitly hypothetical 5-from-35 selection algorithms:** sequential removal, combinatorial rank and duplicate rejection.
- **1,584 configurations attempted**, of which **1,479 completed all 100 draws**. The other **105** exhausted a 1,024-bit safety limit in a sampler; this is a limitation of small toy RSA/BBS parameters and/or the mapping hypotheses, **not a claim about Allwyn's software**.
- **First 80** historical draws used for model selection. **Last 20** (#14336–14355) compared afterward; both blocks were already known, so this is a *retrospective pseudo-holdout*, not a future forecast.

| Candidate | Matches first 80 (400 picks) | Matches last 20 (100 picks) |
|---|---:|---:|
| Training-selected `M(aes,bbs)`, seed 0, chained-state toy seed, duplicate-rejection sampler | **80** | **21** |
| Last-20 hindsight-best `M(aes,bbs)`, seed 0, chained-state toy seed, sequential-removal sampler | **64** | **25** |
| Independent uniform 5/35 expectation | 57.14 | 14.29 |

No completed candidate matched an entire five-number winning combination in the last 20 draws.

**#14355 actual:** `4,14,15,19,27`.

- Training-selected candidate: `1,11,13,28,34` — zero shared numbers.
- Hindsight-selected candidate: `1,12,13,20,30` — zero shared numbers.

## Search calibration

An independent set of **3,000 fair simulated histories**, each containing 20 draws, was compared with the same fixed 1,479 candidate sequences. In **2,735** simulations, some candidate matched at least 25 numbers across 20 draws.

The **plus-one empirical search-adjusted p ≈ 0.91170**. The null median best score was **26** and null mean **26.021**. Thus the retrospective best score of 25 is ordinary after searching so many models.

The training-selected model's score of 21 has a nominal one-sided fixed-model probability ≈ **0.03329**, but the model family, tests, and historical block were selected through an exploratory research process. That nominal p-value is **not** proof of prediction or a global false-positive rate.

## Independent local execution

Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0 and cryptography 46.0.4. In the local development workspace, 52 tests passed covering the original historical engine, seed/switch pipeline and eight new benchmark tests. No CI was requested or added.

A compact reproducer is archived at [`experiments/extra5_seeded_replay.py`](../experiments/extra5_seeded_replay.py), which rebuilds the configurations and writes detailed scores and JSON locally:

```bash
python -m pip install -r requirements.txt
cd experiments
python extra5_seeded_replay.py --seeds 8 --null-replicates 3000
```

This uses tiny *illustrative* Naor–Reingold subgroup parameters (`p=23,q=11`), toy BBS/RSA moduli and synthetic coupon bytes, **not** the original documented cryptographic parameter sizes or authenticated entropy.

## Scientific assessment

**Negative result:** no exact historical draw reproduction and no identified live algorithm. Increasing arbitrary synthetic seed indices is not a reliable strategy to reconstruct a secret entropy-fed CSPRNG.

**Next research:** recover precise seed serialization, real historical number mapping, CFB segment settings and generator-switch protocol from the original academic thesis and full implementation papers, or establish the currently certified RNG version through public technical documentation. No additional indiscriminate frequency or seed sweeps until they can distinguish a defined implementation.
