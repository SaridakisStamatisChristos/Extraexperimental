# Phase 2C — Exact unordered five-removal SMT for unrestricted xorshift128

**Run date:** 2026-10-31. **Status:** VERIFIED FORMULATION / FULL UNKNOWN STATE RECOVERY NOT ACHIEVED.

## Model

- Marsaglia xorshift128 with four unrestricted 32-bit initial words (128 unknown bits), 32-bit output word after each step.
- Exactly five outputs per draw, no gaps in the benchmark. Index at step `j` is **exactly** `floor(word * (35-j) / 2^32)`; selected element removed from initially sorted `1..35`.
- A published ticket is an unordered set of five distinct values. Extraction order is **not supplied**. For each draw, the formula introduces five 3-bit rank variables, each restricted to `0..4` and mutually distinct. This implicitly enumerates all 120 possible extraction orders without materializing them. Each selected number's removal index is its original zero-based value minus the count of lower-ranked numbers removed earlier.
- The five removal indices are equated to exact `38`-bit bitvector products of their corresponding 32-bit PRNG outputs by 35, 34, 33, 32, and 31. The generator's full 128-bit state transition is unrolled as xor/shift bitvector expressions.
- An optional *logically necessary* per-position upper-five-bit domain derived from the unordered set supplements, but does not replace, the exact sampler constraints.

## Executed verification

- 5/5 regression tests: pinned true states SAT on 4-draw oracle fixtures with and without redundant prefix bounds; incorrect pinned states UNSAT; independent full-ticket replay of an unpinned 3-draw SAT model; 200 simulated tickets checked against every five-position necessary prefix domain.
- Unpinned 3-draw instance: SAT in ~0.29 s, **3/3 complete unordered tickets replay**, but a **different** 128-bit seed from the hidden fixture (expected underdetermination; not state recovery).
- Unpinned 5-draw instance: UNKNOWN timeout at 5 seconds.
- Unpinned 8-draw instance: UNKNOWN timeout at 8 seconds, both plain and domain-strengthened.
- **Pinned** true 8-draw hidden state: SAT in ~0.06 s. This only demonstrates consistent encoding and DOES NOT recover an unknown state.
- Incorrect pinned 3-draw state: UNSAT in ~0.004 s.
- These are local libz3 measurements; no CI, proof of unique solution, or actual RNG attribution.

## Reproduce

```bash
python -W error -m unittest -v test_exact_smt128.py
python benchmark_full_smt.py
python exact_smt128.py --n 8 --timeout 8000
python exact_smt128.py --n 8 --timeout 8000 --strengthen
```

Requires Python 3.10+ and shared library `libz3.so.4`. The command-line generator uses deterministic planted fixtures; no real lottery data are loaded. Full inputs, outputs and run times are recorded in `P2C_RESULTS.json`.

## Evidence ledger

- Model correctness on pinned synthetic controls: **TESTED**.
- Full-state **unrestricted** unordered seed recovery: **UNKNOWN / timeout**.
- Real EXTRA 5 RNG: **UNKNOWN** (not tested with this unsolved inverse).
- The 3-draw witness only satisfies a short observed prefix and is not the original planted seed.

**Next algorithmic task:** replace the large disjunctive nonlinear bitvector solve with an XOR-aware independent linear algebra preconditioner and an exact correlated sampler constraint system. Profile concrete 5- and 8-draw cases. Never infer `UNSAT` from budget exhaustion or a model fitted only to historical tickets.
