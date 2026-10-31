# Phase 3B — Exact bounded rejection-path/state inference

**Checkpoint:** 2026-10-31; research branch `research/inverse-64-hybrid`.

**Scope:** A hypothetical one-word/one-combination-rank sampler, a known persistent PRNG transition, a known fixed number of extra output words per ticket, and a **bounded total** number of rejected output words. No extraction-order information is needed. Actual EXTRA 5 state/generator is **UNKNOWN**. Do not interpret a timeout, rank-deficient path or unsearched skip path as eliminated. All results below are model-conditional.

## Mathematical model

One PRNG word (32 or 64 bits) is mapped via `word % C(35,5)` into a lexicographic combination rank. For unbiased conventional rejection, define `N=324632`, `U=2^word_bits`, `L=floor(U/N)*N`. If `word>=L`, discard the word, advance the PRNG, and retry until `word<L`. Advance the generator a fixed number of `gap` additional words **after each accepted ticket**. This differs from five sequential draws, collision/retry, entropy reseeding, and arbitrary variable consumption.

For a fixed rejection path `r_d` (number of discarded words before accepted ticket `d`), the accepted word has zero-based ordinal

`q_d = d*(gap+1) + sum_{i=0}^d r_i`.

The path-dependent low-bit projection from initial state `s` is *linear* for Marsaglia xorshift128 (three bits) and xoroshiro128+ / xoshiro256+ (only their lowest addition-output bit). Since `N` is divisible by 8, a published combination rank reveals those bits exactly under this sampler hypothesis. For every candidate path, compute the GF(2) equations using precomputed unit-state transition forms. A contradiction excludes that path; a unique reconstructed state must independently replay the **whole ticket sequence** under the precise rejection rule. Rank-deficient paths remain `UNKNOWN`.

The enumerator covers every path with **at most K total rejected words** over `n` draws, including more than one rejection before a single draw. The complete search space has `sum_{k=0}^K C(n+k-1,k)` paths. A budget cap (`--max-paths` programmatically) returns `UNKNOWN` when interrupted. A bounded `UNSAT` is not an unrestricted RNG exclusion.

The optional `accept_multiple` is only a deliberately inefficient but still unbiased synthetic **stress control**, reducing `L` to an integer multiple of N and thereby increasing rejection frequency. Real-data tests use only the conventional maximal acceptance threshold.

## Identifiability counterexample (important)

If the first output word is rejected and the second is accepted, a model initialized at the *one-step-forward state*, with no first rejection, produces exactly the same accepted ticket stream, provided later outputs are the same. Thus even unlimited exact output replay may not uniquely identify the original pre-rejection seed without information about initialization or earlier consumption. Our forced-rejection fixture exhibits both seeds, exactly reproducing 180 tickets. `SAT` means a valid replay witness, **not original-seed uniqueness**. A `minimum_skips=1` variant is used only for synthetic controls to demonstrate the planted pre-skip state can be recovered under the extra assumption.

## Synthetic execution and independent controls

- `python -W error -m unittest -v test_variable_rejection.py`: **11/11 green**, including independent Marsaglia forward implementation, inverse-transition-engineered early and late rejections, real nonlinear '+' output forced rejection in both 128- and 256-bit models, two separated rejects in one planted sample, zero-skip exhaustive UNSAT, budget `UNKNOWN`, rank-nullity `UNKNOWN`, and ordinal parity checks.
- `python benchmark_phase3b.py`: **6/6 verified synthetic instances**, each with 100 reserved complete ticket continuations, 600/600 full tickets. The first-rejection case deliberately recovers a distinct yet future-equivalent seed; other stated controls recover their planted original states exactly when their hypotheses pin the correct skip behavior.
- `python -W error -m unittest -v ../phase3_rank/test_rank_inverse.py`: previously preserved Phase 3A **7/7** green; combined **18/18**.
- Benchmark timings in `PHASE3B_RESULTS.json` are local Python 3.13.5 on Linux x86_64. State generation time and regression-suite runtime are excluded from per-case inversion timings.

## Historically observed ranks: narrow bounded exclusions

`audit_real300.py` uses the **previously preserved first 300 ranks** in `../phase3_rank/real_first300_ranks.csv`, not a newly downloaded canonical CSV. Its provenance claim is only the earlier Phase 3A GitHub source transcription of blob `eff4bdcb94a67bad95dd1a8e8da0e61354746d15`; source full-CSV SHA verification still needs a repository checkout. These results must not be represented as a fresh independent canonical data reconciliation.

- For **3 candidate generator families × 3 fixed gaps** = 9 models, all **301/301 paths** for 0 or 1 total rejection in the first 300 tickets were exhaustively ruled out under the precise continuous-state sampler assumption, with full-rank coverage and zero surviving witnesses. See `REAL_300_BOUNDED.json`.
- Stronger **0/1/2 total rejection** coverage: Marsaglia xorshift128 with first 85 tickets (3 gap variants; **3,741/3,741** paths each) and xoroshiro128+ with first 165 tickets (3 gap variants; **13,861/13,861** paths each) returned bounded `UNSAT`. See `REAL_2REJECTIONS_128BIT.json`.
- For xoshiro256+, the **two-rejection bounded test was NOT completed**; the one-rejection 300-ticket test was completed. Models allowing larger skip budgets are `UNKNOWN`.

No statement about the real RNG, actual entropy/key material, independent stream initialization, sampler identity, rejected-word count, or future ticket prediction follows from these tests.

## Reproduce in GitHub checkout

From this directory:

```bash
python -W error -m unittest -v test_variable_rejection.py
python -W error -m unittest -v ../phase3_rank/test_rank_inverse.py
python benchmark_phase3b.py
python audit_real300.py --ranks ../phase3_rank/real_first300_ranks.csv --output REAL_300_BOUNDED_REPLAY.json --max-skips 1
```

For the 128-bit two-rejection cases, use `recover_bounded` on the first 85/165 ranks as recorded in `REAL_2REJECTIONS_128BIT.json`. The audit runs only the first 300 historical ranks, not a full 3,526-draw brute-force sweep.

## Next gates

1. Path search scaling beyond 2 rejected words, with early GF(2) contradiction pruning, witness enumeration and explicit initial-state equivalence classes.
2. Introduce additional exact sampler models: multistep 5-of-35, collision/retry and unbiased multiply-high; keep output-consumption automata model-specific.
3. Handle nonlinear `++` and `**` output functions without pretending the full output is GF(2)-linear.
4. Apply to authentic draws only after independent canonical source verification; require full-ticket replay, untouched holdout and truly prospective lock before any production claim.
