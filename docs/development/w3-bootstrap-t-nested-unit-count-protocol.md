# W3 root-cause R2: bootstrap-t restudentization and independent-unit count

!!! danger "Research-stage statistical falsification only"
    A successful engineering check is not evidence of nominal frequentist
    coverage. Existing [W3 blocker #289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289)
    remains open regardless of this pilot's observed results.

## Why another experiment?

The original [W3 nominal 90% interval study](w3-fixed-truth-uncertainty-pilot-results.md)
found slope-function simultaneous-band truth inclusion of 41/64 (64.1%)
among independent curves and 50/64 (78.1%) among participant-level means.
The [matched bootstrap sensitivity](w3-same-dataset-bootstrap-sensitivity-results.md)
reused exactly the same generating datasets and found no inclusion-decision
changes when increasing 199 Rademacher or normal bootstrap draws to 999.

The next falsifiable questions concern the *sampling approximation* rather
than the number of simulated bootstrap draws:

1. Does recalculating the HC1 standard error inside each wild-bootstrap
   pseudo-sample, instead of dividing by the observed-data HC1 SE, alter
   maximum-studentized critical values and full-grid truth inclusion?
2. How does each diagnostic vary as independent inference units increase,
   while the generating coefficients and population mechanisms remain fixed?

## Experimental design

**24 independently seeded generating blocks per design**, 2 generative
designs, and **nested** unit sizes n=36,72,144 within each block. Each
block creates 144 condition assignments and source participant/curve
responses *once*; n=36 is a prefix of n=72 and n=144. Therefore the
144 fitted cells across designs and n are **not** 144 independent
generating blocks. Between the two designs, the seeds and response
mechanisms are distinct.

- **Independent-curve design:** n curves, 31 equally spaced times, two
  dimensions, Gaussian observation noise, known smooth intercept and
  condition-effect coefficient functions.
- **Participant design:** n independent participants, three repeated
  trials each, participant-constant condition, smooth Gaussian
  participant random intercept and trial noise. The inference unit is
  the participant mean, never the individual trial.

All three sample sizes within one block share the **same first n
original responses**, truth, and first n Rademacher bootstrap weights.
The tested CI target is nominal **90%** simultaneous slope coefficient
truth inclusion at *all* 31 × two grid locations. Each case uses
199 Rademacher draws, with the same exact wild pseudo-responses for
the two statistical reference constructions:

- **Existing fixed-HC1 reference:** the maximum over time and dimension
  of `abs(beta*_slope - beta_hat_slope) / HC1(original)`. Independent
  vectorized algebra is checked against the package's actual
  `function_on_scalar_simultaneous_bands` result using identical
  bootstrap coefficient arrays and multipliers.
- **Candidate bootstrap-t diagnostic:** refit OLS and recompute HC1
  from residuals **inside each wild pseudo-sample**, then take the
  maximum of `abs(beta*_slope - beta_hat_slope) / HC1(bootstrap)`.
  This is an *investigational alternate reference distribution*,
  not a replacement stable API or a demonstrated correction.

Both critical values are evaluated against the **same original-data
studentized truth-deviation supremum**. It is the critical values,
not the data, that differ between reference choices. All
coefficient-point estimates, original HC1 SEs, truth, pseudo-response
arrays and source units remain fixed between alternatives.

## Prespecified outputs and limitations

For each of 24 × 2 × 3 = **144 original fitted cases**, retain
source-inference-unit counts, software/numerical-oracle agreement,
the two critical values, the truth statistic, inclusion decisions,
fitting exceptions, and full original SHA256 evidence. Summarize
**per design and n** by generating-block denominator 24, with Wilson
95% Monte Carlo intervals and within-dataset inclusion switches.

Do not interpret these small-n exploratory estimates as generalized
nominal calibration, a systematic n-effect, a scientific-method winner,
or a remedy for real gaze-device errors. No routine should exclude a
failed band, modify the target level after viewing results, or promote
inference automatically. Independent replication and realistic
heteroskedastic/irregular-sampling stress tests are required.

Source run:

```bash
python scripts/run_w3_hc1_restudenization_nested_n.py \
  --out build/w3-hc1-restudentization
```

The scientific programme is isolated from protected `main`. Stable
1.1.0 remains published, unreleased 1.2 remains `1.2.0rc2.dev0`,
and no literal RC, release tag, or PyPI publication is authorized.
