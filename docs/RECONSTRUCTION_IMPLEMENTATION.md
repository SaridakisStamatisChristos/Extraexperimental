# Historical EXTRA 5 generator — reference implementation (Step 6)

**Date:** 2026-10-29 · **Status:** runnable algorithm-family reconstruction, not reverse engineering of the 2026 deployed RNG.

## Objective

Implement the most specific public technical components described by Bikos, Nastou, Petroudis & Stamatiou (2023), *Random Number Generators: Principles and Applications*, *Cryptography* 7(4):54, especially §5.3, and the alternate CAST-128 historical evidence in Stamatiou's 2018 professional CV. Preserve a hard distinction between published formulas and deliberately invented interfaces needed to run a complete toy demonstration.

Original publication: <https://doi.org/10.3390/cryptography7040054>
Original design evidence and CAST-128 discrepancy: [GENERATOR_VERSION_EVIDENCE.md](GENERATOR_VERSION_EVIDENCE.md).

## Implemented modules

| Component | Code | Evidentiary status |
|---|---|---|
| BBS parity generator | `BBS(p,q,seed)`, modular squaring, least significant output bit | Formula documented; **prime values/seed/initial-state convention are toy assumptions** |
| RSA/Rabin parity generator | `RSAParity(p,q,e,seed)` | Family and formula documented; parameters/initial-state convention are toy assumptions |
| AES-192 in CFB | `CFBZeroBits('aes192',key,iv)` | AES-192 CFB with zero-input is described; **CFB segment size, byte order, key and IV unknown** |
| DES-compatible CFB | `CFBZeroBits('des',key,iv)` | DES CFB family described; reference uses 3DES with identical subkeys (equivalent DES primitive), **NOT proven binary compatibility with legacy mcrypt** |
| CAST-128/CAST5 CFB | `CFBZeroBits('cast128',key,iv)` | CAST-128 appears in 2001–2002 designer's CV, but is **not** one of the four 2023 paper examples; mode/role assumed |
| Bit mixer M | `mixer_m(X,Y)` | Literal published §5.3.5 pseudocode; crosschecked exhaustively for lengths 2–7 against separately archived reference |
| Bit mixer B | `mixer_b(X)` | Literal published §5.3.5 pseudocode; crosschecked exhaustively for lengths 2–7 |
| XOR 2–4 streams | `Route('xor',names)` | XOR combination of two/three/four generators described; **chunk size/alignments assumed** |
| Switching | `RoutedBits.configure(Route(...))` | Option to switch described; **trigger, cadence, handling of residual buffers and stream state are assumptions** |
| Physical entropy XOR | `xor_physical_sources(*samples)` | Combining physical samples using XOR described; **no physical hardware interfaced; no entropy claim** |
| Naor–Reingold mathematical evaluation | `naor_reingold_eval()` | Published algebraic example; **not wired to authentic RNG seed/reseed procedure** |
| 5/35 selection | `bits_below` + `sample_five_of_thirty_five` | **Entirely hypothetical** unbiased rejection sampling and sequential removal. The real conversion is NOT published. |

**Important M/B subtlety:** the literal modified bit algorithms are not guaranteed to be permutations of their input bit strings. Example: `M([0,0,1],[0,0,1]) == [0,0,0]`. This means they should not be silently replaced with a standard Knuth shuffle.

The tiny demonstration BBS/RSA factors have deliberately low security and are **not** recommended cryptographic parameters. The demonstration AES/DES/CAST key material is generated from public constant labels. No simulated output represents historical or future lottery draw outputs.

## Execute locally, without CI

From the repository root with Python 3.10+:

```bash
python -m pip install -r requirements.txt
python experiments/extra5_historical_engine.py --operation m --names bbs aes --draws 3
python experiments/extra5_historical_engine.py --operation xor --names bbs rsa des aes --draws 3
python experiments/extra5_historical_engine.py --operation single --names cast --draws 3
python -m unittest discover -s tests -p 'test_historical_engine.py' -v
```

The first command yields reproducible synthetic, *not operator*, tickets. `--operation` accepts `single`, `b`, `m`, `xor` with the documented source-count restrictions. `--block-bits` is an explicit chunk-size hypothesis, default 256. `--names` must refer to `bbs`, `rsa`, `des`, `aes`, `cast`. Route switching can also be called programmatically through `.configure(Route(...))`; no undocumented stochastic switching policy is invented.

## Verification evidence

- 17 local `unittest` cases passed on Python 3.13.5, cryptography 46.0.4 (29 October 2026).
- BBS/RSA bit sequences differential-checked against direct modular arithmetic for 512/256 steps.
- AES-192, DES-compatible and CAST-128 continuous CFB streams compared byte-for-byte against independent `cryptography` Cipher constructions over 60 bytes.
- Published M/B mixing was cross-checked exhaustively on all bit strings up to length 7 and all corresponding M bit-pairs: 21,840 pair cases; preserved standalone exhaustive tests in `experiments/extra5_published_mixers.py` span larger ranges.
- Rejection branch, input validation, route switching, deterministic outputs and 5-distinct-number invariant checked.
- Results include no real-world draw fit and no claim of prediction.

## Fidelity gaps / future work (specific and actionable)

1. Obtain Vasiliki Liagkou's thesis or original 2004/2005 conference material to determine **actual CFB segment width and bit ordering, state initialization, sizes and block boundaries**.
2. Determine whether CAST-128 was superseded by AES and identify source of the version discrepancy; do not mix them into one asserted live pipeline.
3. Determine exact meaning of “seed” in the production generator (entropy XOR, coupon-file hash, Naor–Reingold key parameters, reseeding cadence, IV handling). Never claim fixed toy seeds replicate original draws.
4. Locate the exact conversion from bit sequences to five unique 1–35 labels and whether winning-number emission order is preserved. Until then, the unbiased sequential-removal algorithm is merely a **candidate interface**.
5. When implementation-level evidence is obtained, add a separate **named, source-pinned profile** with reference test vectors. Keep toy/research demo untouched.

No CI, workflows or production cryptographic claims.