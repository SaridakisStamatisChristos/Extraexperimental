# EXTRA 5 seed, switching and 5/35 algorithm reconstruction — Step 7

**Date:** 2026-10-29  
**Status:** IMPLEMENTED reference hypothesis; **not** recovered current operator software.  
**Primary source:** Bikos, Nastou, Petroudis, Stamatiou, *Random Number Generators: Principles and Applications*, Cryptography 7(4), 54 (2023), [DOI](https://doi.org/10.3390/cryptography7040054), especially §5.2–§5.3.5.

## What the paper actually states

1. A **Generator** and independent **Verifier** exchange authenticated information; the Verifier supplies the closed coupon-file hash. The generator produces numbers only upon a draw request.
2. Source randomness comes from physical noise generators; multiple entropy sources can be **XORed**. The system may also continue from existing internal state instead of collecting fresh entropy on every draw.
3. The source/state and coupon-file hash are combined, and a **Naor–Reingold (NR) pseudorandom function** is applied to produce seed material.
4. Four pseudorandom generator families are described in the 2023 version: **BBS**, **RSA/Rabin**, **DES-CFB**, **AES-CFB**; the original 2001–02 designer CV instead lists **CAST-128** rather than AES. This is an unresolved version distinction.
5. Four types of output route are described: a source alone, modified paper **B**, ordered source pair with paper **M**, and XOR of two, three or four generator outputs. The system allows changing the combination periodically or upon an external Verifier signal.
6. Generator signs its numbers / committed seeding information; a Verifier recreates the number sequence and accepts or rejects it.

Source excerpts/evidence: [paper §5.2](https://www.mdpi.com/2410-387x/7/4/54), §§5.3.3–5.3.5. Full details of the deployed seed serialization, keys and game-number conversion are **not disclosed**.

## Implemented in experiments/extra5_seed_switch_protocol.py

| Stage | Evidence state | Reference implementation |
|---|---|---|
| Entropy or previous-state input | Paper describes both paths | Explicit mutually exclusive `SeedInput`; does not read any actual diode |
| XOR entropy and closed coupon hash | Mechanism in paper | Strict 32-byte XOR; coupon byte encoding/choice of SHA-256 is hypothetical |
| NR function | Published mathematical expression | Mathematical `NRKey.evaluate`; **toy p=23, q=11, public g=2**, 257 factors for 256-bit input |
| Expand processed seed for four generators | **Not specified** | Domain-separated SHAKE-256 expansion, hypothetical |
| BBS, RSA/Rabin, DES/AES | Published families | Reuses previous `extra5_historical_engine.py`; **tiny insecure BBS/RSA** and chosen full-block CFB |
| Route structure | Paper-supported | Enumerates **31** combinations: 4 single + 4 B + 12 ordered M + 6 pair XOR + 4 triple XOR + 1 four-XOR |
| Route timing and buffering | **Not specified** | Explicit `DrawSpec.route` per draw, 256-bit buffer assumption |
| Five distinct 1..35 numbers | Required game interface, conversion unspecified | Three deliberately HYPOTHETICAL unbiased samplers: sequential removal; 19-bit rejection then lexicographic unranking; repeated unbiased draws rejecting duplicates |
| Verifier / seed commitment | Concept in paper; packet crypto and exact serialization unknown | Deterministic recomputation and SHA-256 **demo checksum**; **not** a secure production commitment, signature, or authenticated protocol |

### Exact combinatorial mapping

There are `C(35,5)=324632` unordered tickets. A uniformly sampled rank `r in [0,324632)` maps **bijectively** to a ticket using combinatorial unranking. To get an unbiased rank from ideal unbiased bits, consume a 19-bit integer and reject numbers `r>=324632`. Each ticket has exactly one rank, so each has probability `1/324632`. The branch uses *no modulo bias* under the ideal-bit assumption; it is **not** an attribution of this sampler to EXTRA 5.

The other two samplers generate the same uniform distribution when given unbiased independent bits, and cannot be distinguished from unordered published results on distributional grounds alone.

### Seed material caveat

The historical text indicates NR processing with primes of approximately 1000 and 200 bits, whereas our fixture deliberately uses **23 and 11**. The expansion `SHAKE256(domain || draw ID || NR output || mixed input)` and per-component labels are reasonable research interfaces, **not** recovered mcrypt or operator implementation parameters. `SeedInput.prior_state` models state-derived **reseeding**, not genuine continuation of cipher/PRNG internal state. These distinctions prohibit attributing generated numbers to the lottery.

### Reproduce locally

```bash
python -m pip install -r requirements.txt
python experiments/extra5_seed_switch_protocol.py --draws 3 --sampler combination_rank
python -m unittest discover -s tests -p 'test_seed_switch_protocol.py' -v
python -m unittest discover -s tests -p 'test_historical_engine.py' -v
```

On 2026-10-29 the development workspace passed **44 tests** on the closely corresponding full pipeline (27 new + 17 prior), including exhaustive combinatorial unranking over 324,632 possible tickets and all 31 routes. **The committed compact reference module/test pair has not been rerun from a fresh clone**, and this is not CI validation. Preserve this distinction.

## Known research blockers / next implementation

- Obtain full Vasiliki Liagkou thesis: https://search.library.upatras.gr/Record/nemertes-10889-143/Details
- Identify exact **bitstream → five distinct integers** algorithm and original *generated ordering* of the five numbers. Avoid assuming that sorted public results reflect source bit order.
- Find actual **seed/coupon canonical serialization, NR key generation and sizes, source-to-key/IV expansion, CFB segment widths, bit order and reset policy**.
- Identify authentic **switch trigger, route timing, mixer buffer length and handling of source state on switches**.
- Determine the **historical CAST-128 versus AES replacement** (or different system revisions) using original publications/versioned documents.
- Obtain current operator/system certification, manufacturer and version evidence before claiming 2026 implementation attribution.
- Do not use large historical outcome-fit searches as substitute for missing cryptographic state; do not claim prediction.

**Research classification:** published mechanisms SOURCE-DOCUMENTED; implementation executable and locally tested; encoding/sampler/switch schedule ASSUMED; current 2026 deployment UNKNOWN; no live-draw reproduction or predictive performance established.
