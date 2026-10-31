# EXTRA 5 — Shuffle-Invariant Exact Inverse-State Laboratory (2026-10-30)

**Research status: VERIFIED MODEL FALSIFICATIONS; production generator NOT recovered.**

This package is an executable research continuation for `SaridakisStamatisChristos/Extraexperimental`. It does **not** fit polynomials through known winning numbers. It constrains candidate PRNG states by inverting a specified 5-of-35 sampler, treating the five published values as an **unordered set**, so a subsequent publication/display shuffle does not invalidate the mathematical test.

## Completed scope

- 3D research extension: unknown-order five-output inverse-state engine, two sampler architectures (`state % remaining_size` and `floor(state * remaining_size / 2^32)`), both xorshift32 directions, every shift triplet `(a,b,c)` in `1..31`, and additional fixed output gaps `0..4`.
- `31³ × 2 × 5 = 297,910` models per sampler; **595,820** across both samplers.
- Stage 1: choose seven informative draws from the first 100, solve 35 low/high-bit linear equations over `GF(2)` plus consistency constraints and at most one remaining free state bit.
- Stage 2: choose eight informative draws for previously underdetermined models, solve 40 equations.
- Under both samplers: **144,440/297,910 fully enumerated**, **153,470/297,910 underdetermined**. A configuration is *only* treated as exhaustively evaluated if its selected observation matrix has rank at least 31 and the code enumerated every compatible permitted fourth index and remaining free bit.
- 324 verified maximal-period transition configurations across both directions; all **1,620** generator+gap configurations per sampler, or **3,240** across the two samplers, were exhaustively evaluated with no state satisfying the selected consistency constraints and full first draw.
- Twelve synthetic planted-generator recoveries (six for each sampler) identify the **exact hidden 32-bit initial state** and reproduce **60 complete synthetic draws** in each experiment.
- Python independently verifies all 3,526 real draws and all generated fourth-selection masks, and replays matched full-ticket witnesses.
- `python -W error -m unittest -v test_lab.py` passes **12/12** regression tests.

**Crucial caveat:** The parameter search uses necessary constraints from a selection of the first **100 known draws**. A reported full-ticket match is conditioned on satisfying those constraints; it is **not** a historical one-step prediction. A model is eliminated as an explanation of the complete archive if no initial state can match both its necessary constraints and the requisite complete tickets. Models reported *underdetermined* are **not eliminated**.

## Mathematical contract

Assume state `s ∈ GF(2)^32`, a fixed xorshift32 transition `T`, exactly five output words consumed per lottery draw, and `g ∈ {0,1,2,3,4}` extra transitions after each ticket. Let the **fourth** emitted word of draw `d` be:

```
u_d = T^(d*(5+g)+4)(s)
```

Five distinct numbers are selected by removing an indexed member from an initially sorted list `1..35` of length `35,34,33,32,31` at successive selections. The fourth selection has exactly 32 choices.

For the modulo sampler its index is `u_d & 31`. For multiply-high it is `u_d >> 27`. Thus both samplers expose **five exact linear bits** of `s` under their respective assumptions. The published five-number set `S_d` constrains the fourth index to a finite allowed set `A(S_d)` computed from all possible preceding subsets of three of the other four selected numbers. The published order is **never used**.

The 7-/8-observation C++ solvers derive the 35-/40-row binary matrix, enumerate all allowed fourth-index values for those observations, reject inconsistent linear systems using dependency syndromes, enumerate zero/one remaining free bit, apply four extra necessary index constraints, and replay full tickets for survivors. This is exact enumeration under the stated transition/sampler model.

## Contents

- `shuffle_inverse32.cpp`: seven-observation, modulo sampler; complete source.
- `shuffle_inverse32_8obs.cpp`: eight-observation, modulo sampler for previously underdetermined models.
- `shuffle_inverse32_high.cpp` and `shuffle_inverse32_high_8obs.cpp`: multiply-high equivalents.
- `maximal_period32.cpp`: deterministic primitive-period certification via orbit-order factor tests of `2^32-1`.
- `independent_verify.py`, `audit_results.py`, `test_lab.py`: source-independent checks, complete grid accounting, tests.
- `real_unordered.csv` and `extra5_2022_2026_authoritative.csv`: preserved observations.
- `full_*.csv`, `stage2_*.csv`, `high_full_*.csv`, `high_stage2_*.csv`: every full-grid executed result (six shards per stage). No untested configuration is silently labeled eliminated.
- `synthetic_xorshift32_*` and `synthetic_high_*`: planted-generator controls and frozen recovery outputs.
- `RESEARCH_RESULTS.json` and `REPORT.md`: machine-readable findings and interpretation.
- `smt_inverse64.py`, `smt_*35.*`: experimental 64-bit SMT formulation, returned **UNKNOWN/timeout**, not UNSAT. This component does not yet recover 64-bit hidden states and is not evidence against the actual RNG.

## Reproduce without rerunning the expensive grids

Requires Python 3.10+, GNU `g++` with C++20. A local `libz3.so.4` is required only for the optional 64-bit SMT test.

```bash
g++ -O3 -std=c++20 -Wall -Wextra -Werror shuffle_inverse32.cpp -o shuffle_inverse32
g++ -O3 -std=c++20 -Wall -Wextra -Werror shuffle_inverse32_8obs.cpp -o shuffle_inverse32_8obs
g++ -O3 -std=c++20 -Wall -Wextra -Werror shuffle_inverse32_high.cpp -o shuffle_inverse32_high
g++ -O3 -std=c++20 -Wall -Wextra -Werror shuffle_inverse32_high_8obs.cpp -o shuffle_inverse32_high_8obs
g++ -O3 -std=c++20 -Wall -Wextra -Werror maximal_period32.cpp -o maximal_period32
python -W error -m unittest -v test_lab.py
python audit_results.py
```

To rerun a short valid planted-generator recovery:

```bash
./shuffle_inverse32 synthetic_xorshift32_13_17_5_stride5.csv sample_replay.csv 1 2 60 60 12032 1
```

The `offset` is zero-based `(a-1)*961 + (b-1)*31 + (c-1)`; for `(13,17,5)` it equals **12,032**. This call tests the corresponding `(13,17,5)` model's two directions and three gaps. Compare the `direction=0,extra_gap=0` row to the planted `0x89ABCDEF` seed.

To rerun the **complete** grid, the `start_full_search.py`, `start_stage2.py`, `start_high_full.py` and `start_high_stage2.py` scripts create six parallel shards per stage. Run the stages in that order, generating `unresolved_from_seven.csv` and `high_unresolved_from_seven.csv` from the first-stage `enumerated=0` records before their respective second-stage searches. These scripts use the local data files and require substantial CPU time; do **not** add them to CI by default.

## Scientific interpretation

Eliminated: precisely those fully enumerated xorshift32+sampling+fixed-gap configurations that cannot explain the observed constrained historical prefix.

Unresolved: 153,470 models per sampler due to inadequate linear rank with only 7/8 chosen observations; all higher-word generators; nonlinear scramblers; variable rejection/skips; unknown public/private seed inputs; any reseeding; alternative ticket-selection logic; all questions of the actual EXTRA 5 implementation.

**No demonstrated live prediction capability or recovered production generator.** This is an inverse-engineering instrument and falsification result—not a lottery forecast.
