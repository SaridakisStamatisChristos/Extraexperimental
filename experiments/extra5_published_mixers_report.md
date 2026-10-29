# Historical EXTRA 5 RNG — source-level mixing algorithms, forensic note

**29 October 2026; exact target: identify published algorithmic mechanisms, not test lottery number frequencies.**

## Source and provenance

Bikos, Nastou, Petroudis & Stamatiou (2023), *Random Number Generators: Principles and Applications*, *Cryptography* 7(4), 54: https://doi.org/10.3390/cryptography7040054 . Sections **3.2.1–3.2.3 and 5.2–5.3.5** describe a historical eLottery generator-verifier protocol developed and operated for several years. The paper's **§5.3.5 prints executable-level pseudocode for its specific binary variants of Knuth M and B**. The reproduction in `extra5_published_mixers.py` follows those printed steps literally. This is **not an authenticated copy of the historical implementation or 2026 Allwyn deployment**.

## Documented historical pipeline

1. Physical entropy seeds; source examples include semiconductor shot noise.
2. Combine new entropy/current internal state with the post-betting **coupon-file hash**, as described in the paper (e.g. XOR).
3. Apply **Naor–Reingold** pseudorandom-function processing and commitment mechanisms.
4. Generate bits via four candidate families: **BBS**, **RSA/Rabin**, **DES CFB** (64-bit effective-key standard DES; 64-bit key input in the source), **AES CFB** (paper cites 192-bit key), with mcrypt 2.5.3 historically specified for DES/AES.
5. Select one or several sources, with optional **XOR**, bit-level **M** (two inputs) or bit-level **B** (single input), with dynamic change via verifier or schedule as an architectural option.
6. Convert bits to winning game numbers and authenticate/reproduce via **Verifier**. **The exact 5-from-35 extraction/sampling procedure is *not specified* in the inspected sections.** No current hardware/seed/parameter/software version is verified.

## A concrete algorithmic finding about the printed B variant

Let `X` be binary and `V=[X[0],X[1]]`. At each main-loop index `j >= 2`, the code uses `i = X[j]`, outputs `V[i]`, and then assigns `V[i]=X[j]=i`.

**Proof:** Each of the only two table cells `V[0]` and `V[1]` becomes permanently equal to its index when that bit appears as a main-loop index. Therefore, at most the **first occurrence of bit 0** and the **first occurrence of bit 1** can produce main-loop output differing from `X[j]`. The sequence's main-loop output is effectively `X[2:]` after these at-most-two startup discrepancies. The two final wrap steps can be analyzed similarly; exhaustive testing shows the *full* output differs at no more than two positions from the two-place cyclic rotation `X[2:]+X[:2]` for tested lengths.

This **is not cryptanalysis of a deployed RNG**: B only reorders/mixes bits after an upstream cryptographic primitive. Its behavior does not make cryptographic source bits predictable.

## A concrete issue with calling the printed M variant a permutation

Literal bit-level M uses `i=Y[j]`, outputs table cell `V[i]`, and overwrites it with `X[j]`. A single table cell can be selected multiple times; it need not preserve the count of 1-bits. Exhaustive counterexample:

- `X=001`, `Y=001`, literal `M(X,Y)=000`.
- Input had one 1-bit; output has zero. Hence the printed bit-level algorithm is **not always a permutation of X**, unlike a common verbal description of the classical Knuth shuffle.

This is a statement about **the printed variant only**. It is not an allegation of an implementation vulnerability.

## What was actually run

Run: `python extra5_published_mixers.py`. Exhaustively examined B for **all 32,764 binary sequences of lengths 2–14**, plus all pairs of M inputs for lengths 2–7. No violations of the B main-loop maximum-two-mismatch invariant. Counterexample above reproduced. See generated `extra5_published_mixers_results.json`.

## What to seek next (implementation attribution)

- Full text of **Vasiliki Liagkou's thesis**, “Μελέτη και ανάλυση πρωτοκόλλου γένεσης τυχαίων αριθμών και ανάπτυξη στατιστικών μεθόδων για τον έλεγχο των ψευδοτυχαίων γεννητριών” (University of Patras repository record https://www.openarchives.gr/aggregator-openarchives/edm/nemertes/000009-10889_143). Indexed abstract reports analysis of the implemented protocol; the complete thesis text has **not yet been retrieved/checked**.
- Detailed 2004 *Electronic National Lotteries* protocol: https://doi.org/10.1007/978-3-540-27809-2_18
- Current 2026 operator/CTI certification or version-level design document, plus actual bits-to-5-of-35 sampler and per-draw configuration.

**Evidence: historical published algorithm successfully reproduced; present-day production algorithm still unknown.**
