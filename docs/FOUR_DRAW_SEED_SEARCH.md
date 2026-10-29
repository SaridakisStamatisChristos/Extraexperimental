# Step 20 — Four consecutive draw, all available seeded families

**Executed 29 October 2026.** Historical results supplied by user (not independently operator-verified):

| Draw | Five numbers | Lexicographic rank |
|---|---|---:|
| #14249 | 2, 4, 30, 32, 35 | 55,817 |
| #14250 | 2, 5, 9, 30, 33 | 57,278 |
| #14251 | 10, 18, 21, 25, 29 | 268,706 |
| #14252 | 1, 7, 9, 14, 18 | 23,073 |

## Exact-match contract

One unaltered synthetic integer seed per attempt; fixed generator family/KDF, continuous state across draws and the same hypothetical 24-bit rejection-to-combinadic mapper. **No resetting or parameter refitting between tickets**. Match four sorted tickets in order, not just number-overlap.

## Scope and real executed results

**11 families tested:** 8 historical-inspired crypto/mixer options and 3 artificial arithmetic controls. **4,640,000** previously covered seeds were not fully rerun; all **16** previously recorded exact first-ticket candidates were recomputed for all four draws. **4,640,000 new disjoint seeds were actually executed**, producing 13 additional first-ticket matches.

| Family | New seeds executed | New first-ticket fits | Full 4/4 fits | Unresolved first decode (1,024 bytes) |
|---|---:|---:|---:|---:|
| `aes192-cfb128` | 400,000 | 1 | 0 | 0 |
| `des-cfb64` | 400,000 | 0 | 0 | 0 |
| `cast128-cfb64` | 400,000 | 1 | 0 | 0 |
| `bbs-parity-toy` | 80,000 | 0 | 0 | 0 |
| `rsa-parity-toy` | 80,000 | 0 | 0 | 152 |
| `xor-aes192-des` | 100,000 | 0 | 0 | 0 |
| `m-aes192-bbs` | 100,000 | 1 | 0 | 0 |
| `b-bbs` | 80,000 | 0 | 0 | 2 |
| `splitmix64` | 1,000,000 | 4 | 0 | 0 |
| `xorshift64star` | 1,000,000 | 1 | 0 | 0 |
| `lcg64` | 1,000,000 | 5 | 0 | 0 |

**Total attempted:** 9,280,000 synthetic seed hypotheses = 4,640,000 prior + 4,640,000 new. **Verified exact first-draw seeds: 29**; **exact first two: 0**; **exact first three: 0**; **exact all four: 0** among the first-draw matches available and decoded.

**Caveat:** 154 newly tested toy RSA/BBS configurations did not yield *any accepted first ticket* within the 1,024-byte fallback. They are **unresolved**, not silently counted as outputs or statistically random. The earlier experiment also excluded 505 finite six-byte preview failures, and this checkpoint does not claim those historical rejected seeds were all completely classified. Conditional synthetic enumeration therefore does not rule out other bitstream policies, long rejection runs or actual operator states.

Under an ideal independent uniform-ticket toy model, expected exact two-ticket matches across 9.28 million independent configurations are **0.00008806**; exact four-ticket matches **8.36×10⁻¹⁶**. Zero matches is expected even if the family generator is properly random and the correct *true* key is absent. These quantities are not claims that the toy seeds behave perfectly independently.

## A stronger exact mathematical falsification

The four ticket ranks are **55,817, 57,278, 268,706, 23,073** in modulus **324,632**. We can refute **every deterministic one-state integer-coefficient polynomial congruential recurrence on that rank**, regardless of its degree.

Take input ranks y=57,278 and z=268,706. Their difference **211,428** is divisible by 28, so y≡z (mod 28). Also 28 divides 324,632. For any integer polynomial P, P(y)≡P(z) (mod 28). Yet the required outputs are z=268,706≡18 (mod 28) and w=23,073≡1 (mod 28). Contradiction. Thus no P with x(t+1)=P(x(t)) (mod 324,632) maps all four known draws. The previously fitted affine and quadratic recurrences are special cases and correctly failed at #14252.

The theorem does **not** rule out non-polynomial recurrences, vector/hidden-state transitions, different number encodings, cryptographic generators, reseeding or generator switching.

## Files and checks

- [Executable new-range seeded experiment](../experiments/extra5_four_draw_search.py).
- [Machine-readable 11-family counts, exact candidate continuations, and mathematical obstruction](../experiments/extra5_four_draw_search_results.json).
- [Regression tests](../tests/test_four_draw_search.py).
- Local command: `python -m unittest discover -s tests -p "test_*.py"` -> **14/14 passed** (6 new plus 8 earlier). Python 3.13.5. No CI.
- Reproduce from repo `cd experiments && python extra5_four_draw_search.py --new-scale 1` (requires existing `extra5_multifamily_compact.py`, `extra5_multifamily_blind.py`, `extra5_three_draw_seed_test.py`, `extra5_one_draw_seed_fit.py`, archived input JSONs).

**Result:** No operator seed identified, no predictive advantage demonstrated. The finite synthetic-seed space is not a substitute for published production seeding/entropy and 5/35 conversion details. Next research should investigate stronger state models with a fixed protocol and blind fifth draw, or obtain actual implementation documents. Avoid fitting all four by adding arbitrary free parameters and relabeling them recovered seeds.

## Reproducibility correction (30 October 2026)

An inspection of committed source revealed two stale import names and one outdated arithmetic-archive schema in the Step 20 entry point. This correction changes `FAMILIES` to import from the committed `extra5_multifamily_compact.py`, aliases the previously committed `tickets` generator as `simple_seed_tickets`, and reads `arithmetic_seed_sweeps[family].tested`. The associated unit test import was corrected. These repairs do not alter the stored seed-search measurements, numbers, sampler or fitted candidates. They **have not been verified by a fresh full 4.64M-seed execution** in this correction checkpoint; the original `14/14 passed` claim in the Step 20 report refers to the previous local prototype and should not be interpreted as a successful fresh-clone verification of the formerly broken committed source. A new successful fresh-clone test remains pending.
