# Step 22 — Fixed-state inverse search for the four known EXTRA 5 draws

The earlier four-draw catalog of **9.28 million synthetic seed attempts in 11 families** found **zero full four-draw matches** (the prior enumeration and sampler caveats remain unchanged). Instead of continuing uniform brute-force seed guessing, this step inverts a **fixed linear PRNG state transition** with GF(2) Gaussian elimination.

## Contract and target

| Draw | User-provided numbers | Lexicographic rank |
|---|---|---:|
| #14249 | 2, 4, 30, 32, 35 | 55817 |
| #14250 | 2, 5, 9, 30, 33 | 57278 |
| #14251 | 10, 18, 21, 25, 29 | 268706 |
| #14252 | 1, 7, 9, 14, 18 | 23073 |

Fixed 5/35 sampler: 32-bit generator words become **continuous big-endian bytes**. Consume 24 bits per candidate, reject candidates at least `floor(2**24/324632)*324632`, and map accepted values modulo 324632 to the lexicographic five-number combination. As a *specific no-rejection initial branch* choose each raw accepted 24-bit value equal to its combination rank, producing 12 fixed bytes (96 output bits). This is the same sampler *style* as the prior synthetic experiments, not published operator details.

## Executed fixed-PRNG inversion results

| Fixed transition | Initial state size | Canonical no-rejection raw branch | Outcome |
|---|---:|---|---|
| xorshift64 (13,7,17 shifts; top 32 bits) | 64 bits | inconsistent GF(2) equations | no fit for this branch |
| xorshift96 (16,5,1 shifts; 3×32 state) | 96 bits | unique 96/96 GF(2) inversion | **4/4 exact fit** |
| xorshift128 (11,19,8 shifts; 4×32 state) | 128 bits | 96 independent constraints | **4/4 exact fit; 2^32 states for fixed raw branch** |

Canonical xorshift96 seed: `92a140efbdfe8769d18dcbdc`. Forward replay of the unchanged fixed transition and 24-bit sampler yields **all four observed lottery tickets exactly**. First fifth ticket is **9,24,25,30,33** for **draw #14253**, locked *before user disclosure* in the separate Git commit `db050505c8a184bed0390fed1aec0f4f494beac9`; see [immutable primary lock](../experiments/extra5_draw14253_XORSHIFT96_STATE_LOCK_before_reveal.json). For an independent witness, switch only the first training raw word from rank 55817 to rank+324632 = 380449 and invert the *same algorithm*: seed `2c5afd000d825d1fcaadd647` reproduces all four, yet gives **15,17,22,29,35** for #14253.

## Critical non-identifiability

For each observed five-number combination, **51 distinct accepted 24-bit values** generate it. Across four draws, there are **51^4 = 6,765,201** raw no-rejection sequences. The xorshift96 3-word linear output map is invertible, so each corresponds to a **different valid initial seed**, with the same fixed PRNG and no rejected first-four candidates. Thus a four-draw fit does **not uniquely recover the underlying 96-bit state**, and the correct operator generator/seed remains unknown. Allowing rejection histories could increase possibilities.

The previously established impossibility of autonomous *one-state integer-polynomial maps on the 324632-valued combination rank* is not contradicted: here the PRNG has a **hidden 96-bit multistate register** and a many-to-one output projection.

## Reproducibility and limits

- [Pure Python implementation](../experiments/extra5_four_draw_inverse_reproducer.py) (no dependencies).
- [Seven regression tests](../tests/test_extra5_four_draw_inverse_reproducer.py), including exact inversion of 12 independent random 96-bit seeds, all passed locally under Python 3.13.
- [Experiment results](../experiments/extra5_four_draw_inverse_reproducer_results.json).
- Run `python experiments/extra5_four_draw_inverse_reproducer.py`, or `python -m unittest discover -s tests -p 'test_extra5_four_draw_inverse_reproducer.py'`.

**No additional 9.28M brute-force sweep was performed in Step 22**; that catalog is archival evidence. No CI; the historical draw results were user-provided rather than operator-verified. No actual Allwyn configuration, physical seeding or forecasting advantage identified.

**Next:** obtain #14253 only after the immutable lock, grade the original canonical primary and the secondary separately without cherry-picking. A miss is expected unless the toy assumptions happen to model the real generator.
