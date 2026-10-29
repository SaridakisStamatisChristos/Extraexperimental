# Step 10 — Quantitative 180/200 target evaluation

**Date: 29 October 2026. Status: EXECUTED; target NOT reached.** Research only; no current Allwyn generator state or keys were recovered.

## Objective and dataset

We interpret 180/200 as at least 180 shared numbers among 200 proposed integers, consisting of 40 predictions containing five distinct integers from 1 to 35 each. An actual independent random draw contains five distinct numbers. To test this particular denominator we scored **100 archived public draws #14256–14355** with the first **60 draws (#14256–14315)** for configuration selection and the later **40 (#14316–14355)** for *retrospective pseudo-holdout*. The later outcomes were public before this experiment: **this is not a real forward forecast**.

## Executed seeded reconstruction

The exact synthetic seed domain, generator routes and samplers from Step 9 were unchanged: 128 seed indices, two synthetic entropy/previous-state fixtures, 31 fixed historical-family routes plus two hypothetical switching schedules, and three proposed number-selection methods.

- **25,344 attempted; 23,343 fully completed; 2,001 failed** a finite 1,024-bit sampler budget.
- Historical scores from the old 80/20 split were verified to match the earlier full 128-seed search **for every one of the 23,343 successful configurations**.
- Highest *training-selected* result: seed 0, previous-state fixture, M(AES,BBS), duplicate rejection; **66/300** first-60, then **35/200** later-40.
- Highest *hindsight-selected* last-40 result: seed 23, previous-state fixture, XOR(BBS,RSA,AES), sequential sampler; **43/300** first-60, **48/200** later-40.
- Candidate mean later-40 score **28.5627/200**, versus **28.5714/200** fixed random expectation.
- **Zero models scored 180/200**; **one** model had any 5/5 match in the last 40, after searching thousands.
- Full scores CSV SHA-256: `059e32d34970301ee2d821d0e2a8ff51fe89ec00a007e9977561d7789ab8878b`; archived as [extra5_target_180_scores.csv](../experiments/extra5_target_180_scores.csv). Machine-readable [summary](../experiments/extra5_target_180_results.json).

The full run was executed in five contiguous batches, because a combined multiprocessing attempt stalled. A simple, independently implemented replay of the **first two seed indices (368 completed models)** agreed with the optimized batch results for every training/validation field. The full 128-index independent slow replay is available in [extra5_target_180_replay.py](../experiments/extra5_target_180_replay.py); **it was not rerun in full**.

## Exact mathematical probability (not Monte Carlo)

For an independently chosen fair actual ticket and any fixed five-number candidate, the intersection size K has multiplicities across all C(35,5)=324,632 possible actual tickets:
`[142506, 137025, 40600, 4350, 150, 1]` for K=0,1,2,3,4,5.

For forty independent draws the exact convolution is given in [extra5_180_probability.py](../experiments/extra5_180_probability.py). Its resulting upper-tail probability for a **preselected, fixed model** matching at least **180/200** is **2.407762919 × 10^-165**. A conservative union bound over all 23,343 *outcome-independent* fixed models is **5.62044098 × 10^-161**, valid regardless of dependence between candidates. **These probabilities are conditional on the stated fair independent draw null and apply to previously fixed predictions; they do not apply to candidates adapted after examining test outcomes.**

A fixed predictor achieving 35/200 has upper-tail probability ~0.1029, so the training-selected model's result is not compelling. The strongest 48/200 looks rare if it were one prespecified predictor (p~0.0000609), but it was picked *among 23,343 using the same 40 outcomes*. Its Bonferroni factor exceeds one, so it does not establish predictive ability. A complete 40-draw Monte Carlo calibration was **not** executed in this step.

## Scientific decision

**180/200 has not been achieved and cannot be justified by further arbitrary fixed-seed searching alone.** A known-history lookup can achieve 200/200 retrospectively without predicting anything. The actual cryptographic seed/state, coupon-file inputs, IVs and conversion method remain unknown. Useful progress requires real implementation documentation, an independently demonstrable flaw, or predeclared predictions on future unavailable draws.

Reproduction: `cd experiments && python extra5_target_180_replay.py --seed-start 0 --seed-stop 128 --out .` (slow). This produces a second score CSV with equivalent columns, but a possibly different row order. To reproduce the exact target tail: `python extra5_180_probability.py`.

**No CI or workflows added.**
