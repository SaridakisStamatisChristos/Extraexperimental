# Step 3 — How surprising is the 80-draw underdispersion after an archive-scale search?

**29 October 2026 · Executed Monte Carlo, not a historical replication**

## Question

The preceding 100-draw analysis found the most balanced 80-draw segment within archived IDs #14256–14355 at **#14264–14343**. The across-label population standard deviation of its 35 appearance counts is **2.01828**. Considering an isolated prespecified 80-draw window, that is rare under independent uniform 5-of-35 sampling. But what if a researcher could have selected any 80-draw segment over the entire lifetime of the lottery?

**Scope:** this does *not* obtain earlier archived results, and it does not measure the real minimum over historical draws. It calibrates a **hypothetical look-elsewhere effect** using 14,355 synthetic independent draws, matching the last published draw ID as a convenient assumed window-search horizon. The actual number of accessible, examined historical windows remains uncertain.

## Null model and statistic

Each synthetic draw is five distinct numbers chosen uniformly from 1..35, independent across draws. Each five-vector is generated using uniform integers 0..34 with entire-vector rejection/resampling if any labels repeat. Conditional on all five labels being distinct, each unordered five-set has probability `1 / C(35,5)`.

For a window of 80 draws, let `c_i` be the number of appearances of label `i` for i=1..35. The total count is 400. We compare the equivalent integer statistic

`T = sum_{i=1}^{35} c_i^2`.

The original minimum window has `T=4714`, equivalent to `sqrt((T - 400^2/35)/35) = 2.01828377` population SD.

Define an extremal event as **any** 80-draw window whose `T <= 4714`.

## Executed experiments

1. **Single prespecified 80-draw segment:** 200,000 null realizations. 188 had `T<=4714`. Smoothed Monte Carlo probability = **189/200001 = 0.000945**. A separate, independently coded NumPy `argpartition` implementation produced 128/120,000 or ~0.001075, consistent with sampling error.
2. **A predetermined grid of disjoint windows:** 14,355 contains `floor(14355/80)=179` non-overlapping blocks. Plugging in the fixed-window probability, the chance that **at least one** crosses the threshold is approximately `1-(1-0.000945)^179 = 0.1557`. This is a reference calculation, not a direct archival test.
3. **All overlapping 80-draw windows:** 14,355 synthetic draws contain 14,276 possible starts. In **4,795 of 5,000** independent complete synthetic histories, at least one crossed the observed threshold. Smoothed Monte Carlo probability **4796/5001 = 0.959008**, with binomial 95% interval about **0.9531–0.9643** (for raw 4795/5000).

### Interpretation

A fixed prespecified interval as balanced as the observed interval is rare under the ideal model. **But looking retrospectively across a full-length history makes it very common to find such an interval somewhere.** The original 80-draw observation therefore provides no persuasive evidence for an algorithmic defect or prediction once this broad alternative selection mechanism is considered.

The full-archive correction is a *sensitivity analysis*, not the exact p-value for the real historical discovery process: we have not examined 14,355 verified historical draws and do not know how many windows were actually considered in selecting the original interval. The actual segment was found in the latest 100 draws, so the 21-window correction within that specific 100-draw sample is also relevant. The 14,276-window calculation illustrates how much the interpretation depends on the scope of selection.

Do **not** claim a verified historical global minimum, a compromise, an algorithm identification, or successful predictions.

## Reproduce

From `experiments/`:

```sh
python extra5_archive_scale_null.py --replicates 5000 --fixed-replicates 200000 \
  --seed 202610291 --scan-horizon 14355
```

Outputs `extra5_archive_scale_null_results.json`. The input is `extra5_last100_data.csv`; it is used only to recover the already-discovered real threshold. Software in the executed run: Python 3.13.5, NumPy 2.3.5. The code stores a newline-normalized SHA-256 for portability. The two Monte Carlo streams use seeds 202610291 and 202610292.

## Sources and provenance

- Original period data: `extra5_last100_data.csv` in this repository, already spot-checked but **not** wholly authoritative.
- Public EXTRA 5 archives and draw numbering: https://numbers.gr/extra-5 and https://numerics.gr/extra-5/kliroseis-apotelesmata
- Formal game format: five distinct labels from 1 to 35, i.e. `C(35,5)=324632` possible subsets.
- No past-draw file from outside the 100-draw archive was retrieved in this step. Public operator API access was unsuccessful in this research environment. This fact is part of the evidence ledger, not an indication that earlier results do not exist.

**Status:** Executed, reproducible synthetic null study; independent historical replication remains open.