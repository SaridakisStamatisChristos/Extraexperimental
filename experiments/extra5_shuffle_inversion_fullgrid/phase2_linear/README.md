# Phase 2 — 128-/256-bit linear state core (partial gate)

Date: 2026-10-31. Branch: `research/inverse-64-hybrid`; parent verified at `2272e7367948c1a0ad1dec18911c0b062c0032e6`.

## Exactly what was implemented

`inverse_linear.py` implements (a) Marsaglia xorshift128 using 4x32-bit words and the output word as specified; (b) a xoroshiro128 transition using rotation parameters 24/16/37, with **raw first 64-bit state word** as a diagnostic projection; (c) the xoshiro256 state transition with **raw first 64-bit state word** as a diagnostic projection. The latter are NOT published `+`, `++`, `**` scrambled-output generators. This is explicitly a transition-only algebraic test, not a claim of xoroshiro/xoshiro deployed generation.

The full 128-/256-bit initial state is represented as a binary vector. The fourth removal from the 35,34,33,32,31-element list is a 32-way choice; under modulo it equals the emitted word's bottom 5 bits and under multiply-high it equals its top 5 bits. The implementation builds 5 exact GF(2) equations per *known fourth extraction index*, performs elimination, reports rank/nullspace, detects algebraic contradictions, and replays whole sets. The published order is NOT used and a known fourth index is an extra oracle which an unordered ticket does not supply.

`test_inverse_linear.py` separately implements reference transitions and demonstrates 24/24 planted exact-state recoveries across three state models, two sampler types, two fixed gaps, and two seeds, with 50 reserved synthetic tickets per case (**1,200/1,200 full-ticket continuations**). Seven test methods all pass locally (`python -W error -m unittest -v test_inverse_linear.py`). Rank-deficient systems and a contradictory model are tested, as are unordered fourth-domain enumeration and linear forms.

`benchmark_phase2.py` records the planted experiments and resource measurements in `PHASE2_RESULTS.json`. Under these fixtures xorshift128 reaches rank 128 with 26 exact fourth indices, xoroshiro128_raw with 26–27, xoshiro256_raw reaches rank 256 with 52. These observations are not actual unordered recovery.

`smt_unordered.py` uses Z3 native library through ctypes to impose **disjunctive allowed fourth-index domains** from unordered tickets, never pretending to know the internal selection order. Three planted xorshift128 case probes (24/35/50 observations, 1500 ms each) returned `UNKNOWN: timeout`. This means no real or synthetic 128-bit state was recovered from unordered sets in this stage. No 128/256 production family is refuted. Fixed timeouts are not UNSAT certificates.

## Run

From this directory:

```sh
python -W error -m unittest -v test_inverse_linear.py
python benchmark_phase2.py --smt-ms 1500 --output PHASE2_RESULTS.json
```

The benchmark probes need libz3.so.4; core algebra/tests require only Python 3.10+. No network is required. The prior Phase 1 tests still pass. No prior dataset, lock, or CI workflow modified.

## Remaining gate

To claim Phase 2 complete, recover 128/256-bit states from **unordered** planted sets without oracle extraction indices, preferably by an XOR-aware SAT backend with domain filtering, rank-guided dependencies, or a complete meet-in-the-middle solver. Nonlinear output scramblers and variable output consumption must then be modeled independently. Do not run the unknown model on real data or declare a real generator recovery until these synthetic gates pass. Current status: **GF(2) core EMPIRICALLY_VALIDATED; unordered 128-/256-bit recovery UNKNOWN**.