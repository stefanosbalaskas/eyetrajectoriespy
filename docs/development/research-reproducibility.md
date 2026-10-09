# Reproduce experimental research — without installing it as stable

!!! warning "Install the exact research branch, not the published wheel"
    The **stable 1.1.0 wheel does not contain the new F1/F5 and B6/B7 research prototypes**. Public site documentation is a non-executable evidence mirror; the experimental source, locked scripts, seeds and CI environment belong to the individual **draft branches**. These examples run on **generated synthetic data**, not independent eye-tracking recordings.

## Evidence and environment

Each numerical study has a named GitHub Actions run, source head SHA, retained case-level evidence artifact and check/qualification ledger. When reproducing, record the **exact original commit**, Python version, optional dependency versions, random seeds, scenario and number of Monte Carlo replications. A current branch may contain additional commits, so **a branch tip is not necessarily the original source used for a published number**.

For inspectable historical case-level data without rerunning expensive simulation, use the [scientific dashboard](research-scientific-dashboard.md) and the run's GitHub Actions **Artifacts** section. Artifacts are retained for a limited period and may expire; the permanent documentation preserves only audited aggregate results and source identifiers.

### B6/B7 native mixing comparison

The experimental fitting and diagnostic code resides in [draft PR #266](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/266), not in 1.1.0 or protected `main`.

```bash
git clone https://github.com/stefanosbalaskas/eyetrajectoriespy.git
cd eyetrajectoriespy
git checkout research/b6-b7-score-marginal-elliptical-slice-20261010
python -m pip install -e ".[dev,bayesian]"
python scripts/run_b6_b7_score_marginal_loading_pilot.py --design B6_rank1 --replicates 6 --draws 250 --warmup 350 --seed 20261206 --out build/reproduce-b6
```

**This uses the current research branch**, so check it against [original workflow #38000101053](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38000101053) before comparing numerical values. It does not certify covariance convergence, scientific uncertainty or inference.

### F5 independent AR(2) stress

The AR(1) vs AR(2) simulation code resides in [draft PR #267](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/267).

```bash
git clone https://github.com/stefanosbalaskas/eyetrajectoriespy.git
cd eyetrajectoriespy
git checkout research/f5-independent-baseline-ar2-null-reference-20261010
python -m pip install -e ".[dev]"
python scripts/run_f5_independent_baseline_ar2_stress.py --scenario ar2_misspecified --null-reps 100 --alternative-reps 50 --n-null 119 --n-parameter 99 --seed 20261207 --out build/reproduce-f5-ar2
```

**Interpretation:** 100 true-mean-null simulations per tested generator yield wide Monte Carlo intervals; no automatic dependence-model selection or scientifically qualified unknown-dependence p-values follow.

### F1 and other research

Use the research-only [F1 6,000-fit study](f1-high-precision-native-null-power.md) and [source run #37977625803](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/37977625803) for the exact script and artifact provenance. [Experimental F1–F6 inventory](f1-f6-scientific-expansion.md), [B5–B10 overview](bayesian-research-programme.md), [model contracts](research-method-api.md) and [research case studies](research-case-studies.md) describe the remaining source-level workflows and assumptions.

## Reporting template

Report **data origin**, recording geometry and coordinate units, independent sampling units, missingness, process assumptions, preregistered effect and null, estimator version/branch SHA, complete fit count with failures, Monte Carlo uncertainty, R-hat/ESS/MCSE when Bayesian, source run/artifact identifiers, exploratory vs qualified status, and explicit negative sensitivity results.

Real eye-tracking workflows require separate validation of sampling integrity, session/participant independence and ethical/data-permission constraints. A synthetic-only reproduction is not real-data qualification.

**Do not** relabel the research functions as stable 1.1.0 or turn on a 1.2 release gate when reproducing these demonstrations.
