# W3 same-dataset multiplier × computational-budget sensitivity

!!! warning "Computational diagnosis, not independent statistical calibration"
    The original [64-dataset-per-design W3 frequentist study](w3-fixed-truth-uncertainty-pilot-results.md)
    documented nominal-90% simultaneous confidence-band undercoverage.
    This next *controlled* experiment reuses the first **16** generating
    dataset indices per design from that study. It does not increase the
    number of independent generating datasets.

## Prespecified experimental contrast

The model, generating truth, trajectory data, inference units, residual
functions and HC1 pointwise standard errors are held exactly fixed within
each dataset. No new estimator or posterior architecture is introduced.

The **2 × 2** bootstrap configuration grid is:

| Random multiplier | 199 bootstrap draws | 999 bootstrap draws |
|---|---|---|
| Rademacher (original) | Same seed/contract as the original 90% pilot | Same first 199 draws, plus 800 |
| Normal (sensitivity) | Separately declared seed | Same first 199 normal draws, plus 800 |

All four cells per fitted dataset use *one* Rademacher or normal
multiplier per independent curve/participant, **not** one multiplier per
repeated trial or time point. The four bootstrap computations are
strongly paired; they must never be counted as four independent
generating datasets.

### Scientific outcomes

- Check all coefficient and HC1 standard-error arrays against an
  independent NumPy numerical oracle.
- Recompute every slope maximum-studentized bootstrap critical value,
  and fail closed on discrepancy with the package's computation.
- Compare 199- versus 999-draw critical values *within* multiplier
  with identical prefix weights. Report the per-dataset change in
  the critical value and whether known-truth inclusion changed.
- Compare normal versus Rademacher multipliers at both budgets
  while keeping original data/model/HC1 references fixed.
- Preserve **all 32 fitted source datasets**, four sensitivity cells
  each, the exact source commit and SHA256 original-artifact hashes.
  Negative outcomes are results, not exclusions or CI failures.

The observed inclusion frequencies across the selected 16 datasets
are sensitivity diagnostics; they are **not** independently replicated
coverage estimates, calibrated power, or evidence that a multiplier
choice universally improves frequentist intervals. The eventual
scientific response to undercoverage requires fresh independent
generating blocks, sample-size designs and misspecification stress.

## Source command

```bash
python scripts/run_w3_same_dataset_bootstrap_sensitivity.py \
  --out build/w3-matched-multiplier-budget
```

See [scientific issue #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289),
which remains OPEN until independent, externally repeated interval
calibration evidence is adequate. The Bayesian undercoverage issue #255
and F5 dependent-inference issue #256 remain separate.

**Governance:** Stable 1.1.0 unchanged; development `1.2.0rc2.dev0`
unchanged; `production_release_ready=false`. No GitHub release,
literal release-candidate tag or PyPI publication.
