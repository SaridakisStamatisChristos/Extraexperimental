# Second-selection parity is redundant for unordered tickets

**Model:** five sequential selections without replacement from the initially sorted list 1..35; modulo sampling; a published **unordered** five-number set S. The fourth choice is from a 32-element list, hence its index j4 equals the emitted word's bottom five bits. The second choice is from 34 elements and its index j2 has the parity of the second emitted word's lowest bit.

## Exact theorem

For each possible fourth-selection index j4 in A(S), **both** values of j2 mod 2 occur in compatible extraction orders of S. Consequently the allowed joint domain for (j2 mod 2, j4) is precisely {0,1} × A(S). Adding this one second-word GF(2) bit to the existing fourth-index disjunction yields no additional constraint on the initial state.

**Proof.** Fix any extraction order witnessing j4, and retain its first-three-number *set* {a,b,c}, relabeled a<b<c, along with the fourth and fifth selected numbers. The first three may be reordered without changing the remaining set before selection four, so j4 remains fixed. Choose b as the second selected number. If a is first, b has zero-based second-selection index b-2. If c is first, b has index b-1. These are consecutive integers and have opposite parity. Both are legal without-replacement extraction orders. Thus both parities exist for each fixed admissible j4. No stronger joint filter is obtainable from second index parity alone. QED.

## Executed falsification control

`test_second_parity.py` independently enumerates all 120 extraction orders for each of 203 deterministic five-number sets and confirms exact equality of the joint domain and its claimed Cartesian product. Result: **1/1 test method PASS**, all 203 sets.

This theorem does not imply that the complete second emitted word is irrelevant. Its nonlinear residue and other sampler relationships can still constrain a state; only this specific free-standing parity observation is redundant after order elimination.

**Evidence classification:** algebraically proved for the specified model; empirical 203-case oracle passes. No claim about the production lottery.
