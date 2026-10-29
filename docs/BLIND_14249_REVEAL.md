# Step 13 — Reveal and evaluation of historical blind draw #14249

**Timestamped research entry:** 29 October 2026. The user revealed the results of historical draw **#14249 (5 September 2026)** as **2, 4, 30, 32, 35** (10,010 columns). These numbers are **user-provided and not independently checked against operator records in this step**.

## Immutable pre-reveal commitment

The frozen prediction in [the original committed lock](../experiments/extra5_draw14249_LOCKED_before_reveal.json) was **8, 18, 24, 27, 34**, derived from the *smallest* matching synthetic AES-192-CFB seed index **1,231,545**, after fitting just one known ticket: draw #14248 = 13, 16, 22, 30, 31.

Pre-reveal GitHub commit: [f218295f669fd9d556328d8ec57b4c2d86399915](https://github.com/SaridakisStamatisChristos/Extraexperimental/commit/f218295f669fd9d556328d8ec57b4c2d86399915).

**Primary blinded score = 0/5.** This does **not** mean the generator's secret state was recovered or that the generator is proven wrong; the seed and mapping were synthetic assumptions. Under an ideal uniform 5/35 draw, P(0 matches) = C(30,5)/C(35,5) = **0.4389770571**. The failure is unsurprising under a fair draw.

## Exploratory outcomes of all 12 *previously computed* matching seeds

The candidate predictions were already saved before the hidden numbers were supplied. Their scores below are calculated **after** the reveal and must not replace the locked prediction.

| Synthetic seed index | Before-reveal next-ticket output | Hits after reveal |
|---:|---|---:|
| 1231545 | 8, 18, 24, 27, 34 | 0 |
| 1490414 | 9, 10, 11, 16, 17 | 0 |
| 1532809 | 2, 15, 21, 23, 33 | 1 |
| 1828592 | 2, 14, 18, 27, 29 | 1 |
| 2090880 | 4, 7, 17, 21, 25 | 1 |
| 2466460 | 12, 14, 26, 30, 33 | 1 |
| 2783003 | 7, 9, 19, 26, 34 | 0 |
| 2802749 | 6, 23, 26, 27, 28 | 0 |
| 2844983 | 1, 13, 14, 15, 29 | 0 |
| 3657902 | 3, 18, 21, 28, 32 | 1 |
| 3719509 | 1, 4, 9, 10, 32 | 2 |
| 3771097 | 9, 15, 22, 24, 28 | 0 |

Six candidates scored 0, five scored 1, and one scored 2. The highest retrospective overlap was **2/5** (seed 3,719,509), **not** a successful blind forecast. The chosen and committed lowest-seed model scored zero.

## Inference and next protocol

A single observed 5-number set imposes relatively little information: 4,000,000 public synthetic seed indices yielded **12 equally exact first-draw matches** and widely varying next tickets. Therefore it is not defensible to assume the original operator's physical-entropy-seeded CSPRNG state can be recovered from one unordered output.

**Next checkpoint:** use a new, user-held-out consecutive draw *pair*, fixing the generator version, sampler, seed search range, and lowest-index tie-break in advance. Commit the next-draw prediction **before** obtaining its result; retain failures and evaluate across multiple such blind pairs. Do not train on historical records #14256–14355 if an allegedly held-out target is inside that archive. The user should supply training numbers, then withhold next-draw numbers.

This is a **researcher-blinded retrospective comparison**, not a truly prospective future draw. No CI, no key/seed recovery, and no prediction claim.
