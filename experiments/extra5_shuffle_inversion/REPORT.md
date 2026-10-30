# Shuffle-invariant inverse-state solver — scientific findings

**Date:** 2026-10-30. **Status: no deployed RNG recovered.**

### Problem

Given unordered EXTRA 5 tickets, test whether they arise from a continuous 32-bit GF(2)-linear xorshift PRNG with five successive modulo selections without replacement, a fixed number of generator steps per draw, and an arbitrary shuffle of the published result. A known odd output multiplier may be present.

### Correct inversion

Write each draw's unordered ticket as `T_t`. Let `A(T_t)` be the set of all fourth-selection indices across the 5! possible generation orders. The fourth index `j_t` satisfies:

`j_t = raw_word_{t,4} mod 32`, with `j_t ∈ A(T_t)`.

`raw_word_{t,4} = M_t s_0` over GF(2), where `s_0` is the unknown 32-bit initial state and `M_t` is a computed binary matrix representing the fourth PRNG output after the fixed stride.

The algorithm branches on `j_t ∈ A(T_t)`, incrementally Gaussian-eliminates the five linear constraints, and reconstructs each resulting seed when the system reaches full rank. Remaining free variables are enumerated exactly when the prefix limit is reached. Every candidate is then checked by an independent full five-number sampler. `exhaustive=true` is emitted only if all branches and free-bit assignments were completed under the budgets.

For an odd output multiplier `m`, replace each allowed fourth-index by `j*m^-1 mod 32` during inversion and verify using all 32 scrambled output bits.

### Executed runs

| Test | Models | Exhaustive | Full-sequence survivor |
|---|---:|---:|---:|
| Systematic a,b,c = 1..12; strides 5..8 | 6,912 | 6,912 | 0 |
| Three scramblers × 50 parameter triples × six strides | 900 | 900 | 0 |
| Total | **7,812** | **7,812** | **0** |

The 6,912-model search generated 426,484,815 reconstructed candidate-state evaluations across models. Each was tested against complete five-number tickets. **5,224** such candidates survived the first-ticket check but none survived the first two-ticket check *while also satisfying the prefix's necessary fourth-index constraints*. This is NOT an exhaustive count of all possible states that could match only the first two tickets. There is no full 12-draw matching state in any tested model.

The scrambled models add another 36,018,631 candidate-state evaluations with no full-sequence survivor.

Nine planted-state controls recover the exact seed and all 60 output combinations, establishing that the inversion method detects a generator when the specified family is correct.

### Independent verification

The C++ solver and Python reference model use different implementations of the selection procedure. `test_reconstruction.py` checks all nine positive controls, verifies fourth-index sets via an independent combinatorial formulation, confirms the GF(2) bit masks equal direct output bits, checks invertibility of all tested scramblers modulo 32, validates data integrity and asserts complete result coverage.

### Explicit unresolved issues

1. Real EXTRA 5 transition/state and sampler are not identified.
2. Search coverage is restricted to 32-bit xorshift left-right-left transitions, the named stride settings, and the three tested multipliers; no blanket family refutation is justified.
3. The sampler's five fixed sequential outputs, single shared state, and absence of variable rejection/skipping are **assumptions**, not documented properties of the deployed system.
4. The exploratory 128-bit nonlinear SMT prototype timed out. Its `unknown` status must **not** be reclassified as `unsat`.
5. Full historical fitting alone is not prediction; a recovered real generator must be frozen and evaluated prospectively.

### Next structural problems

Implement an XOR-aware SAT/SMT backend for 64-/128-bit nonlinear output mixing and variable advances; support alternative without-replacement sampling procedures. Continue rejecting any hypothesis not satisfying complete unordered tickets beyond its identification prefix.
