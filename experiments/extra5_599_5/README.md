# EXTRA 5 — 599 training draws versus five quarantined outcomes

Read [`REPORT.md`](REPORT.md) for the full specification, calculations, exact predictions, evaluation and limitations.

**599 training IDs:** `#13754..#14352`. **Five evaluation IDs:** `#14353..#14357`. All data are copied exactly from the user-authoritative 2026 workbook via the already verified canonical CSV.

Run locally with Python 3 and numpy:

```bash
python -m unittest -v test_holdout.py
python forecast.py --train train_599.csv --lock /tmp/primary_replay.json
python challengers.py --train train_599.csv --lock /tmp/challengers_replay.json
python evaluate.py --test holdout_5_PRIVATE.csv --primary predictions_LOCK.json --challengers challengers_LOCK.json --out /tmp/results_replay.json
```

`forecast.py` and `challengers.py` **never read the five outcome rows**. `evaluate.py` independently verifies SHA-256-pinned lock files and scores them. Already-public outcomes and earlier related model exploration mean this is a *retrospectively quarantined* test, **not a genuinely untouched or prospective prediction**.

No CI. No edits to existing prediction locks. No real production RNG attribution.
