# RNG architecture evidence ledger

## Operator-era disclosures

OPAP's 2023 Integrated Report (p. 104) described independent cryptographically secure pseudorandom generation for electronic lottery games including EXTRA 5, with certification/audit and protection of betting/draw records. It identifies work associated with the Computer Technology Institute and Press (ΙΤΥΕ). **Treat the report as historical disclosure, not a cryptographic specification for the 2026 production system.**

Primary: https://media.opap.gr/OPAPIntegratedReport202327082024.pdf

## Academic research trail

1. *Electronic National Lotteries*, Konstantinou, Liagkou, Spirakis, Stamatiou and Yung (2004), https://doi.org/10.1007/978-3-540-27809-2_18 — architecture and operational security of an electronic lottery design.
2. *Random Number Generators: Principles and Applications*, Bikos, Nastou, Petroudis and Stamatiou (2023), `Cryptography` 7(4), 54, https://doi.org/10.3390/cryptography7040054 — discusses historical generators, physical entropy, implementation components and combinations.
3. 2005 security-engineering follow-up by researchers of the original national electronic-lottery design (refer to bibliographies in above academic papers).

## Historically documented components

| Layer | Examples described | What this does *not* establish |
|---|---|---|
| Physical entropy | Zener diode shot noise; resistor thermal noise; clock timing/phase | That a particular 2026 hardware entropy source remains in service |
| Seed shaping | Cryptographic processing including Naor–Reingold-type techniques | Current seed values, key material, reseed policy |
| Number generation | Blum–Blum–Shub; RSA/Rabin PRNG; DES-CFB; AES-CFB (including AES-192 in published descriptions) | Per-draw selection of these exact generators or their parameterizations in 2026 |
| Mixing and reconfiguration | XOR, Knuth M/B-derived methods and configurable generator combinations | The actual switching timetable, if any |
| Integrity and verification | Record hashing, independent verification and audits | That integrity controls identify the precise bit-to-5/35 sampler |

**Distinct concerns:** cryptographic hash for integrity ≠ RNG primitive, cryptographic RNG ≠ uniform range conversion, physical entropy ≠ deterministic predictability from published tickets.

## Information still missing

- Exact 2026 RNG software/hardware revision, source and certificate IDs.
- Complete stochastic state/entropy model, seed sizes, nonce/counter and reset/reseed schedule.
- Exact transformation from generator output bits to five distinct numbers from 1..35.
- Whether draw order is preserved in publicly available historical records.
- Current operator/regulatory independent assessment documents.

The mathematical identifiability obstacle: unbiased sampling schemes may produce identical distributions over unordered five-element sets. Matching ticket frequencies is not implementation attribution.

## Verified published binary M/B source algorithm (2026-10-29 forensic checkpoint)

The paper **§5.3.5** contains literal pseudocode (rather than just names) for the two-slot **binary** versions of M and B. Python reconstruction and exhaustive tests: [experiments/extra5_published_mixers.py](../experiments/extra5_published_mixers.py). Important: B's main loop becomes almost a shifted identity because `V[X[j]]=X[j]` writes a bit into its own index. M can change total bit counts (example X=001,Y=001 => 000). These facts concern the printed mixer, not claimed 2026 production internals. See [technical report](../experiments/extra5_published_mixers_report.md).
