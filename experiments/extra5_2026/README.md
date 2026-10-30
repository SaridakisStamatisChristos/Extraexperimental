# EXTRA 5 2026: executable, source-traceable reconstruction campaign

**Status: generator not identified; no predictive advantage demonstrated.** The full 604-draw authoritative workbook supplied by the user is represented as `extra5_authoritative_2026.csv` (verified byte-for-byte at the record level against the original workbook). Research work here is retrospective except the separately labeled, deterministic and noninformative #14360 null control.

## Scope and commands (run from this directory)

Python 3.10+, NumPy. No other runtime dependencies for core experiments and tests; no CI is added.

```bash
python -m unittest -v test_research.py
python source_integrity.py /absolute/path/to/extra5_2026.xlsx  # optional XLSX source cross-check
python exhaustive_six.py             # ~19 sec; all 6,765,201 states (toy xorshift96)
python statistical_audit.py          # calibrates a declared 604-draw null battery via simulation
python walkforward_models.py         # 404 sequential historical one-draw forecasts, 15 models
python prospective_control.py       # verifies (or initializes) immutable #14360 null-control record
```

All result JSON files are generated deterministically except for the `elapsed_seconds` field of the exhaustive scanner. The CSV SHA-256 is `5fb393513548e1c5853165eeb137c66f1a859071eaf0c4c8203f5d487289d33e`; the supplied XLSX SHA-256 was `97f6b7ae5e41565d77ed8065a044c57bde539da8d5dca4e44917466c02b4738c`.

## Provenance and constraints

- Draw IDs **13754–14357**, inclusive; calendar **2026-01-01 through 2026-10-29**.
- All 604 IDs consecutive, two draws per day, five distinct numbers from 1 through 35.
- Workbook is authoritative over old manually supplied results; #14249 is sorted `(2,4,30,33,35)`, recorded order `(35,2,4,30,33)`.
- **Unverified:** whether original columns D–H are *actual extraction order* rather than display order. Position tests are conditional and exploratory.
- Previously published blind prediction locks and old incorrect-data experiments are untouched; their source data are labeled superseded.
- Historical xorshift96/128, BBS/RSA, AES-CFB, etc. are *models*, not established production algorithms. CSPRNG behavior cannot be inferred from superficial frequency tests.

## Main findings

1. **Exact conditional falsification of one xorshift96 branch.** Under xorshift96, continuous big-endian words, 24-bit rejection/combinadic mapping, and **no rejected raw chunks in the first four draws**, there are exactly `51^4 = 6,765,201` fitted states. All 324,632 possible fifth tickets occur; 25 states retrospectively reproduce the fifth draw. **Zero** also reproduce the sixth (#14254). This rules out the *specified branch* of the toy architecture over six consecutive draws. It does not exclude untested rejection histories, reseeding, other samplers, or generator variants.
2. **Full-sequence fingerprint battery.** Independent simulation calibration: 700 calibration sequences, 3,000 null sequences, 4,000 within-ticket order permutations. Familywise maxT p-value **0.8644**, conditional order-position p-value **0.7756**. No strong anomaly detected; no cryptographic attribution follows.
3. **Chronological predictive modeling.** 15 fixed configurations over 404 historical sequential one-step forecasts after a 200-draw warm-up. Mild `cold:None:0.2` has total log-likelihood improvement **+0.944** over uniform, likelihood ratio ≈2.57. Equal-weight 14 nonuniform-model LR mixture ≈**0.260**. This is far below compelling evidence, and candidate choice had prior retrospective influence. **Do not interpret as a registered test of unbiased randomness or a trading/betting edge.**
4. **Experimental null control.** `prospective_null_control_14360_LOCK.json` pins a SHA-256-derived fair-ticket control for target #14360 scheduled Saturday 2026-10-31 15:00, with data stopping at #14357. It is not an RNG prediction or recommendation. If published before the target draw, it can be scored without changing the lock.

See `R7_REPORT.md` for the detailed evidence ledger, theorem and caveats. Full scripts and results are inside this directory; no external API key or lottery operation is used.
