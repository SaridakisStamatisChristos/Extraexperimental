# EXTRA 5: 60 RNG families × five sampling methods × fixed seeds

## Data provenance
Source: https://numerics.gr/extra-5/kliroseis-apotelesmata
100 results manually transcribed from the published results page, drawing IDs 14256–14355 (9 September – 28 October 2026). Latest 20 are cross-checked against https://www.lotteryextreme.com/greece/extra5-results and previous 20-draw source file.

## Experiment design
- **60 implemented RNG families**: conventional PRNGs (MT19937, Xorshift, Xoshiro, SplitMix64, PCG64, Philox), hash-counter (SHA-1, SHA-2, SHA-3, SHAKE, Blake), keyed HMAC/Blake, block cipher generators (AES-128/192/256 CFB, CTR, ECB counter; Camellia, DES-equivalent through equal-key 3DES, IDEA, CAST5, SEED, Blowfish), ChaCha20, and simplified number-theoretic BBS/RSA toys.
- **Five samplers**: uniform sequential removal, uniform rejection of duplicates, reservoir sampling, combinatorial unranking, random-key sort. Seed values independently chosen using deterministic SHA-512 expansion of a public constant. 32 seeds for most families, eight for BBS/RSA.
- **9,360 tested configurations**, zero runtime failures.
- Training: 80 chronological historical draws, IDs 14256–14335. Holdout: latest 20 draws, IDs 14336–14355. Model selected by highest training score with tie-breaking independent of holdout.
- Score: total matching individual numbers out of five per draw. A random combination has 25/35 ≈ 0.714 matching numbers per draw; expected training score 57.14, expected validation score 14.29.

## Reproducible outcomes
- **Best selected by first 80**: HASH-sha3_224, seed 0, remove. Train **88/400**; validation **17/100**; one-sided held-out exact null p = 0.2455.
- **Best found by inspecting the latest 20** (invalid as a held-out prediction): MATH-SPLITMIX64, seed 25, reservoir; **30/100** validation and 56/400 training. Single-model exact p = 1.04035e-05; Bonferroni adjustment for 9360 configurations = 0.0974.
- **Monte Carlo family-wise calibration**: 3000 independent random 20-draw datasets scored against the same 9360 fixed configurations; maxima >= 30 in 280 cases, p ≈ 0.0936 (plus-one estimate), median searched maximum 28, central 90% range 26–30.
- **No exact 5/5** among all 9,360 configurations over these 20 results (0 observed). Average held-out score across configurations: 14.262.
- Train/holdout score correlation: -0.028.

## Key limitations and interpretation
These are independently seeded illustrative generator variants, **NOT reproductions of Allwyn's implementation**. BBS/RSA variants are simplified mathematical toy constructions, not production cryptography. Even the AES/DES generators are not equivalent to the original closed-source mixture, seeding and switching mechanisms. The generator is modeled as a continuing byte stream without per-draw reseeding, which differs from some electronic lottery designs. Five-number outcomes lose the internal bits, output order, and seed information. Well-implemented uniform generators can be statistically indistinguishable based on outputs alone.

The 20 historical holdout draws were visible to us and are therefore a retrospective pseudo-holdout, **not a prospective live predictive claim**. The best 30-hit result is hindsight-selected, not an improvement over the random baseline. The correct takeaway is **no identified predictive model**.

## Reproduce
`python extra5_mass_algorithm_benchmark.py` followed by `python extra5_mass_algorithm_calibration.py`; requires Python 3, NumPy, SciPy, cryptography, matplotlib.

Files: `extra5_last100_data.csv`, `extra5_mass_algorithm_scores.csv`, `extra5_mass_algorithm_results.json`, `extra5_mass_algorithm_comparison.png`, and the runnable scripts.