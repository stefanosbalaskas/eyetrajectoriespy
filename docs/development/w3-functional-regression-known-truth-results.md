# W3 functional regression: verified known-truth evidence (24 blocks)

!!! warning "Simulated scientific benchmark, not human eye-tracking validation"
    The source data are computer-generated with fixed, known functional
    coefficients. The experiment verifies the tested workflow and error under
    two stipulated generative designs; it does **not** establish p-value
    validity, confidence-interval coverage, causal identification, or
    generalization to real eye-tracking samples.

## Original result

The original [scientific workflow #38173426113](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38173426113)
saved artifact `11715355738`, containing `case-ledger.json`, `evidence.json`,
`source-truth-recovery.svg`, the source commit and SHA256 checksums.
The downloaded archive was independently checked against all four original
SHA256 entries. Original source artifact records the PR-merge commit
`baf3a7dbcc83a94d4b9684eb1e15da111739625d`; the corresponding
research PR implementation was at `9126f6bb8af5a7e32a86e21c4cc6397dc5bf9d98`.

| Metric | Independent curve-level | Participant-level (3 repeated trials) |
|---|---:|---:|
| Independent generating blocks | 24 | 24 |
| Successfully fitted workflows | 24 of 24 | 24 of 24 |
| Source trajectories per dataset | 72 | 108 |
| Independent inference units per dataset | 72 curves | 36 participants |
| Mean RMSE of estimated condition function | 0.0088577 | 0.0270639 |
| Largest observed RMSE | 0.0104314 | 0.0455377 |
| Largest absolute deviation from independent OLS | 5.55 × 10⁻¹⁶ | 5.55 × 10⁻¹⁶ |
| Prespecified exploratory RMSE criterion (≤0.12) | 24 of 24 passed | 24 of 24 passed |

The 48 fitted cases are *not* 48 independent generating blocks: each
replicate index is paired across the two source-design variants.

![Verified per-block slope RMSE for two W3 generating designs](../assets/research/w3-functional-regression-source-rmse-20261011.svg)

*Original source-ledger visualization redrawn from the 48 verified case-level
RMSE values (rounded to seven decimal places). The vertical scale is
deliberately zoomed to 0–0.055 to distinguish the observed values;
the exploratory target of 0.12 is off-scale and is not drawn. This is
not an accuracy comparison between estimators: both designs use the same
OLS model but different independent units and noise structures.*

## Scientific interpretation

The coefficient functions are known before model fitting. An independent
`numpy.linalg.lstsq` computation on the specified design matrix and
manually constructed participant-averaged responses serves as a numerical
oracle, rather than relying only on the package's direct estimator.
At every coefficient, time point, and dimension the workflow agreed with
this oracle to numerical precision. Recovery errors relative to known truth
are not zero when independent noise or participant effects are present.

The repeated-trial case contains a smooth participant-level random
intercept; condition is participant-constant and each participant's
three trajectories are averaged first. No claim is made that treating the
108 trials as independent units would produce correct inference.

**Limitations:** This study does not test robust HC1 standard error
calibration, wild-bootstrap simultaneous bands, nominal interval coverage,
sparse observation, nonignorable missingness or real eye-tracking device
quality. Exploratory RMSE threshold selection is not a hypothesis test.
See [the prespecified protocol](w3-functional-regression-known-truth-protocol.md)
and the downloadable original scientific artifact for verification.

The stable distribution remains **1.1.0**; `1.2.0rc2.dev0`
remains unpublished development code and all publication safeguards remain
disarmed.
