# Independent calibration shards (B6, B7, F1, F5)

**Experimental research infrastructure.** This programme only makes
Monte Carlo evidence reproducible and auditable; it cannot justify
scientific inference or a 1.2 release by itself. The existing small CI
pilots remain unchanged in qualification.

## Why sharding matters

Previously the three simulation drivers used fixed seeds; re-running
them without changing source or a seed parameter would **repeat the
same simulated data**, creating false precision if all runs were pooled.
Their new `--master-seed` and `--shard-id` options now derive a
different deterministic high-entropy simulation stream for each
programme/scenario/shard/replicate. Every case row stores its actual
seed and shard identifier. The aggregator refuses to combine batches
with duplicate shards, duplicate case keys, observed seed collisions,
incorrect checksums, missing evidence or mismatched master seeds.

Seed derivation is collision-resistant, not a mathematical proof that
all 63-bit seeds are unique; the observed collision check is necessary.

## Produce independent small research batches

These example commands show **separate independently seeded runs**;
they are not sufficient for statistical calibration.

```bash
python scripts/run_b6_population_calibration_grid.py \
  --replicates 2 --draws 25 --warmup 40 \
  --master-seed 20261009 --shard-id 0 --out build/b6-shard-0
python scripts/run_b6_population_calibration_grid.py \
  --replicates 2 --draws 25 --warmup 40 \
  --master-seed 20261009 --shard-id 1 --out build/b6-shard-1
python scripts/aggregate_scientific_calibration_shards.py \
  --inputs build/b6-shard-0 build/b6-shard-1 \
  --out build/b6-aggregate
```

The same arguments work with
`scripts/run_b7_learned_planar_truth_pilot.py`,
`scripts/run_f1_f5_scientific_stress.py` (with separate
`--f1-replicates` and `--f5-replicates`), and the aggregator.
Never mix B6, B7 and F1/F5 programmes in one aggregate. Use one
master seed per predeclared study and distinct shard IDs; a different
master seed is a different study and is intentionally rejected from
a common aggregate.

Each shard must reside in its own directory. Keep its
`manifest.json`, `cases.csv` (or `f1-cases.csv`/`f5-cases.csv`),
`evidence.json` and `sha256.txt` intact. The aggregate returns a
case-level CSV and scenario-level evidence JSON.

## Statistical interpretation

- **B6/B7**: matched-prior generated scenarios estimate population
  posterior 90% marginal coverage; B6's near-tied and misspecified
  scenarios are *model stress*, not prior-based SBC.
- **B7 prediction**: a new subject's outcomes at distinct timepoints
  are **correlated**. Average pointwise inclusion must be summarized
  across independent held-out participants, not by pooling their
  individual time samples as binomial observations.
- **F1/F5**: the aggregator reports conditional rejection
  frequencies at alpha 0.01, 0.05 and 0.10 with exact Monte Carlo
  uncertainty intervals and fit-failure counts. When full fits fail,
  a rejection rate among completed fits is **not** the unconditional
  false-positive rate or power.
- **F5**: block-length settings are distinct scenario keys. The
  two-break data-generating scenario does not imply multiple-break
  model support.

Long chains, Rhat/ESS/MCSE, rank SBC, baseline comparisons,
independent real-world validation, design-appropriate null assumptions
and predeclared acceptance boundaries are **separate required evidence**.

As initial computation-planning targets, the B6 protocol suggests at
least 400 matched-prior refits per critical scenario, and the F1/F5
protocol suggests at least 1,000 null and 500 alternative refits per
critical scenario. These targets are NOT completed experiments; revisit
them using observed Monte Carlo precision, fit failures and computational
budget. For B7, preregister the replication plan before claiming
predictive or cross-covariance calibration.

Never promote any `scientific_inference_qualified`,
`release_authorized`, or root API flag from a successful batch
aggregation or passing GitHub Actions workflow.
