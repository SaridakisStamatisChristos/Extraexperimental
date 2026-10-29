# EXTRA 5 generator attribution — historical version evidence

**Scope:** identify actual documented cryptographic algorithms, not draw-frequency patterns. **Date:** 29 October 2026.

## Important primary-source discrepancy

| Evidence | Context | RNG source families |
|---|---|---|
| [Yannis C. Stamatiou CV (2018)](https://www.bma.upatras.gr/images/new/encvstam2018.pdf), PDF p.4, project dated **2001–2002** | Specifically identifies original EXTRA 5 and SUPER 3 hardware/software design | **BBS, RSA, DES, CAST-128** |
| [Bikos, Nastou, Petroudis & Stamatiou (2023)](https://doi.org/10.3390/cryptography7040054), §§3.2.1–3.2.3, 5.3 | Describes a historical implemented electronic lottery, with published algorithm details | **BBS, RSA/Rabin, DES-CFB, AES-CFB** (AES-192; library mcrypt 2.5.3) |

**CAST-128 versus AES is NOT resolved.** An upgrade, a different installation, or a retrospective description are plausible explanations but are *not* source-established. Never combine these source lists into a purported single 2026 configuration.

## Exact formulas described in the technical publication

- **Blum–Blum–Shub (BBS):** choose modulus N=pq, update x ← x² mod N and emit LSB(x). Secure implementations require large suitable primes and secret state.
- **RSA/Rabin generator:** choose N=pq and exponent e with gcd(e,(p−1)(q−1))=1; update x ← x^e mod N; emit LSB(x).
- **2023 cipher generators:** DES and AES-192 in CFB mode, encrypting zero-valued byte(s) with physical-noise-derived IV. **Undocumented:** CFB segment width, how keys are provisioned, key/IV resets and the precise bit consumption order.
- **NR seed transformation:** for key (P,Q,g,a_0..a_n), where Q divides P−1, compute f_a(x)=g^(a_0·product_{i:x_i=1} a_i) mod P. Publication cites P≈1000 bits and Q≈200 bits as historical implementation sizes. Coupon-file hash and entropy contribute to seed processing; exact serialization and secret parameters are unknown.
- **Mixing:** apply published modified bit-level algorithms M, B, XOR groups and optional switching. Reference implementation and exhaustive tests: [extra5_published_mixers.py](../experiments/extra5_published_mixers.py) and [report](../experiments/extra5_published_mixers_report.md).

## Exact algorithm identification remains incomplete

An algorithm family is not a complete program. To reproduce a real published draw one would also need: the actual seed/entropy for that draw, PRNG parameters (N, p/q or private states, encryption keys and IVs), mode selected and switching protocol, and **the final conversion from bits to five distinct integers in 1..35**. The current publicly examined sources do not specify that conversion.

## Strong independent documentary lead

**Vasiliki Liagkou**, *Μελέτη και ανάλυση πρωτοκόλλου γένεσης τυχαίων αριθμών και ανάπτυξη στατιστικών μεθόδων για τον έλεγχο των ψευδοτυχαίων γεννητριών*, University of Patras, repository metadata indicates 2005 submission; another library catalog lists 2007 publication. The abstract describes evaluation of different generators used in an implemented real-world lottery protocol.

- [University catalog record](https://search.library.upatras.gr/Record/nemertes-10889-143/Details)
- [Openarchives metadata](https://www.openarchives.gr/aggregator-openarchives/edm/nemertes/000009-10889_143)
- Original Nemertes handle: http://nemertes.lis.upatras.gr/jspui/handle/10889/143

**The full thesis has NOT yet been obtained.** Do not infer implementation details beyond its abstract.

### Next source-acquisition targets

1. Retrieve thesis text and inspect any actual code, parameter tables, generator specification, and bitstream-to-game-number mapping.
2. Obtain and compare full *Electronic National Lotteries* (FC 2004) and *Trust Engineering* (ISC 2005) for implementation-level disclosures.
3. Seek independent current certification/version evidence from operator, regulator or laboratory.
4. Only after a concrete specification exists should simulations attempt to match production draw behavior.

**Evidence:** primary sources support specific historical components; the 2026 deployed algorithm is not established.
