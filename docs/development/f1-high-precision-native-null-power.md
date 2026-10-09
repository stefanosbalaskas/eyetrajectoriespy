# F1 higher-precision native sparse-PACE null and power study (research only)

The previously retained full-fitted F1 study had 300 null datasets per
scenario and 199 permutations per fit. In the balanced independent
equal-covariance null, 23/300 (7.67%) simulations rejected at
nominal 5%. This interval was too wide to certify a statistically
calibrated procedure. Source [original waveform study #37965949039](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37965949039);
checksum-recovered source study [#37969068128](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37969068128).
No production inferential qualification follows.

## A *new* independent 6,000-attempt study

The `research-f1-independent-null-and-moderate-power.yml` workflow is
limited to **one pull request opened event** or **explicit manual
dispatch**, avoiding expensive resimulation on documentation edits.
The original scientific evidence is not reused as independent data.

Four predeclared settings, each **1,000 independent true-null fits**
and **500 moderate alternatives** (6,000 total), all invoking
the real `test_sparse_functional_groups` full sparse-PACE fit,
with 199 participant-unit permutations per attempt and new
deterministic independently keyed master seed `20261125`:

| Design | Group units | Observations/curve | Trial structure | Label-exchangeability |
|---|---:|---:|---|---|
| Balanced equal covariance | 8 + 8 | 17 | 1 trial/unit | Nominal null assumption |
| Two trials per participant | 8 + 8 | 17 | 2 repeated participant trials | Permute participant labels as clusters |
| Unequal and heteroscedastic | 8 + 16 | 17 | 1 trial/unit | **Violated; stress only** |
| Very sparse independent | 8 + 8 | 9 | 1 trial/unit | Nominal null assumption if conditions met |

True null effect is exactly **0** and alternative sinusoidal shift
amplitude **0.04**. This is a new, less extreme alternative than
the earlier `0.11` model; power at this one effect size cannot
establish a general power curve or optimal sample-size recommendation.
Noise SD is 0.015, and the native PACE test's measurement-error and
bandwidth contracts stay unchanged to ensure genuine replication of
the original procedure.

Each fit retains its exact seed, design, participant-level condition,
p-value or error, and status. Reports show **unconditional attempted
denominators**, counts of failures and conditional-on-fit rejection
at alpha .01/.05/.10 with **exact Monte Carlo intervals**.
Failed fits are never silently discarded or reclassified as
calibrated nonrejections. A failure-free run is not a statistical
qualification by itself.

The aggregator checks original SHA256 files, **6,000 distinct
simulation seed streams**, exactly 1,000 null and 500 alternative
cases per design, case-level status and agreement of empirical
rejection counts to per-shard source evidence. No automatic
scientific/promotional flag is set upon a green workflow.

## Qualification boundary

Balanced and sparsely sampled independent group conditions should
be judged separately from participant-clustered and deliberately
nonexchangeable heteroscedastic conditions. Even 1,000 nulls give
finite Monte Carlo uncertainty; exact binomial intervals and the
199-permutation discrete p-value grid must be reported. The
clustered-trial implementation requires its own independent review
that participant IDs, not trials, define the permutations.

The broader F1 inferential programme still requires alternative
effect sizes, sample-size and missingness studies and independent
comparison with a second test. Until then
`statistical_null_size_qualified=false`,
`statistical_power_qualified=false`, and
`release_authorized=false`.

No change to protected main or stable 1.1.0 is part of this experiment.


## Completed independent 6,000-fit F1 study (source-verified)

![Actual 6,000-F1-fit empirical null-size and moderate-power comparison](../assets/research/f1-6000-null-power.svg)



[Original exact-source workflow #37977625803](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37977625803)
completed **5/5 study jobs**, including 4,000 independent native sparse-PACE
true-null fits and 2,000 moderate-effect alternatives with **zero
exceptions**. The original immutable combined archive artifact is
`11640464273`; four separately SHA256-audited design artifacts were retained.

| Predeclared design | α=.05 true-null rejects/1,000 | Exact 95% MC interval | α=.05 moderate alternative rejects/500 | Exact 95% MC interval |
|---|---:|---|---:|---|
| Balanced equal covariance | 49/1000 = 4.9% | 3.65–6.43% | 79/500 = 15.8% | 12.71–19.30% |
| Repeated two trials/participant | 51/1000 = 5.1% | 3.82–6.65% | 91/500 = 18.2% | 14.91–21.87% |
| Unequal heterogeneous noise | 52/1000 = 5.2% | 3.91–6.76% | 96/500 = 19.2% | 15.84–22.93% |
| Very sparse | 44/1000 = 4.4% | 3.21–5.86% | 71/500 = 14.2% | 11.26–17.57% |

**Interpretation:** the new independent null sizes are all statistically
consistent with nominal 5% at this single sample-size/parameter setting.
The previous balanced 23/300=7.67% null rate is less precise and does
not establish a stable anti-conservative pattern. Neither apparent null
alignment nor zero fit failures guarantees universal valid inference.
The unequal heteroscedastic condition intentionally breaks pooled
permutation exchangeability, so its approximately nominal observed
size is an empirical outcome, **not** a mathematical validity proof.

Moderate effect `0.04` detection was only **14.2–19.2%** at α=.05.
The previous 0.11-effect pilot's ~98–99% rejection is not general
power. The native sparse-PACE method's inferential use now needs a
power/size curve across realistic amplitude, independent participant
sample size, and missingness, plus separate cluster and
heteroscedasticity validity review. **No scientific or release gate
is automatically promoted.** All original cases and scientific
exceptions remain retained for independent review.
