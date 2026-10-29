# EXTRA 5: 20-draw RNG simulation comparison

## Provenance and time boundary
- Public results: https://numerics.gr/extra-5/kliroseis-apotelesmata
- 20 actual draws: IDs 14336–14355, 19–28 October 2026 inclusive, chronological.
- Query was made on 29 October 2026 before the first draw of the day.
- Historic RNG research: Bikos et al. (2023), https://doi.org/10.3390/cryptography7040054

## Methods
- Algorithms: BBS, RSA/Rabin-style exponentiation, DES-equivalent CFB64 via 3DES with identical subkeys, AES-192-CFB128, ChaCha20, SHA256 counter, MT19937.
- These are **illustrative variants**. They do not reproduce any known live EXTRA 5 configuration. BBS/RSA variant specifics are ours.
- Seed bytes are deterministically derived from a constant domain string and generator name using SHA-256. No draw-derived seed or search was used.
- Two unbiased 5-of-35 samplers: remove-by-index with rejection, partial Fisher–Yates.
- Matches are intersection size between each candidate five-number combination and the real five-number combination from the *same draw ID*. 20 draws × 5 picks = 100 simulated picks.
- Under independent fair draws: E[overlap per draw] = 25/35 = 0.7142857, E[total] = 14.2857, SD(total) ≈ 3.287.
- Null single-model p-values use exact convolution of the hypergeometric(35,5,5) distribution. For model search, Bonferroni factor 14.

## Results: all configurations

| Algorithm | Sampler | Hits / 100 | 3+ matches | P(one-sided) | Adjusted p (14 tests) |
|---|---|---:|---:|---:|---:|
| SHA256-counter | remove | 20 | 1 | 0.0602 | 0.8427 |
| BBS | remove | 18 | 0 | 0.1634 | 1.0000 |
| SHA256-counter | partial-fisher-yates | 18 | 1 | 0.1634 | 1.0000 |
| MT19937 | remove | 17 | 1 | 0.2455 | 1.0000 |
| DES-CFB | partial-fisher-yates | 16 | 0 | 0.3472 | 1.0000 |
| DES-CFB | remove | 16 | 1 | 0.3472 | 1.0000 |
| AES-192-CFB | partial-fisher-yates | 13 | 0 | 0.6996 | 1.0000 |
| ChaCha20 | remove | 13 | 0 | 0.6996 | 1.0000 |
| MT19937 | partial-fisher-yates | 13 | 0 | 0.6996 | 1.0000 |
| RSA-Rabin-style | partial-fisher-yates | 13 | 0 | 0.6996 | 1.0000 |
| RSA-Rabin-style | remove | 13 | 0 | 0.6996 | 1.0000 |
| BBS | partial-fisher-yates | 12 | 0 | 0.7996 | 1.0000 |
| ChaCha20 | partial-fisher-yates | 12 | 0 | 0.7996 | 1.0000 |
| AES-192-CFB | remove | 7 | 0 | 0.9946 | 1.0000 |

## Draw-level observed-data diagnostics

- Frequency-dispersion Pearson χ² = 37.9; 100,000-sequence Monte Carlo upper-tail p = 0.1356.
- Most common number appeared 7 times; Monte Carlo p (maximum >= observed) = 0.4769.
- 3 of 35 numbers did not appear; Monte Carlo p (missing count >= observed) = 0.2012.
- Consecutive draws shared 17 total numbers across 19 transitions (expected 13.57); exact upper-tail p ≈ 0.1788.

## Interpretation
These data do not favor or identify a production generator. With secret and unknown seeds and an unbiased sampler, correct cryptographic generators produce indistinguishable draw statistics. The selected maximum across many candidates is a multiple-comparisons effect, not evidence of a match. No 5/5 result occurred in the 280 tested model-draw pairs.
Twenty draws are much too few to rule out small biases. Full timestamped draw sequences and genuine source/certification docs are necessary for implementation attribution.

## Reproducibility
`python extra5_last20_simulation.py` requires Python 3, scipy, sympy and cryptography; then `python extra5_add_diagnostics.py` also requires NumPy and matplotlib. Scripts write CSV and JSON locally.
Outputs: `extra5_last20_data.csv`, `extra5_last20_model_comparisons.csv`, `extra5_last20_simulation_results.json`, `extra5_last20_algorithm_comparison.png`.

## Safety/precision
The algorithm settings are synthetic. The last 20 results are public historical numbers, not a training set sufficient to recover entropy, secret seeds, internal generator state, dynamic combinations or production sampling logic. Simulations confer no demonstrated betting advantage.