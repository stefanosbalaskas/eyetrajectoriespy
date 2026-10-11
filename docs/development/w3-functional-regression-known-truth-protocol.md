# W3 known-truth functional regression — reproducible research protocol

!!! warning "Development scientific validation, not inferential qualification"
    This study checks 1.2 typed-workflow equivalence to direct OLS and an
    **independently computed numerical oracle**, plus estimation accuracy
    against known generating coefficients. It does not validate HC1 pointwise
    standard errors, simultaneous bands, nominal interval coverage or
    observational causal interpretation. The source data are simulated.

## Study design

Prespecify 24 independent generating seed blocks and two related designs
per block (48 fitted workflows, **24** independent generating blocks).
Each has 31 time points and two response dimensions with smooth, known
intercept and condition-effect coefficient functions.

1. Independent-curve analysis: 72 independent curve-level units and 72 source
   trajectories per generating block; noise is Gaussian.
2. Repeated-trial participant analysis: 36 independent participants, 3
   trials each (108 source trajectories); fixed condition is participant
   constant. The true response contains a participant-specific smooth
   random intercept and trial-level independent noise. **Participant means**
   are the analysis unit; treating the 108 trials as 108 independent people
   is forbidden.

The independent oracle uses NumPy `lstsq` on a constructed intercept-plus-
condition matrix and response arrays manually aggregated to participants
where applicable. Compare **every coefficient, time point and dimension**
against the workflow estimate and the unchanged 1.1.0 scientific primitive.
Prespecified maximum absolute coefficient discrepancy ≤2e-10.

The known-truth recovery outcome is the per-dataset slope coefficient RMSE
over both dimensions and all 31 time points. The exploratory per-case target
is RMSE ≤0.12, tested without excluding failures. Noise-free recovery is
also checked at numerical precision. These are engineering and limited
simulation objectives, **not a nominal 90%/95% interval coverage target**.

## Provenance and original visuals

All 48 attempted fits, exceptions, source-curve counts, inference-unit
counts, oracle differences and recovery outcomes are preserved in original
JSON files with source commit and SHA256SUMS. The source workflow produces
an original SVG showing one RMSE point per generating block and design, plus
the preregistered target line. Any missing case or missed criterion is a
recorded scientific nonpass even if code executes.

Run:
```bash
python scripts/run_w3_known_truth_workflow_validation.py \
  --blocks 24 --out build/w3-known-truth
```

Limitations: This is an exact-OLS-contract and finite-simulation recovery
test, not a general power, p-value or uncertainty-calibration study.
The two designs' seeds are related by an explicit ledger but their source
data are separately generated. The observed independent unit is the curve
in design 1 and the participant in design 2; source trials must not be
substituted as independent statistical units.

1.1.0 remains stable. 1.2 development source and all publication gates
remain unchanged. Bayesian and F5 inferential blockers are separate.
