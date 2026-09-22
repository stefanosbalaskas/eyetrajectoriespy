# Stabilized-volatility FPCR truncation selection

The heteroscedastic wild bootstrap needs an inference truncation h.

The 2026 method by Yeon, Dai, and Nordman proposes a practical **stabilized volatility method (SVM)** that selects h by examining where target-specific wild-bootstrap intervals stop changing materially in both width and center.

## What is fixed first

The method separates three truncations:

- k: residual estimation;
- g: bootstrap pseudo-truth;
- h: target inference.

The recommended practical structure is:

    choose k separately
    set g = k
    search h >= g

The paper suggests prediction-error cross-validation as one practical way to choose k.

eyetrajectoriespy already provides leakage-aware FPCR prediction CV through <code>cross_validate_fpca_regression()</code>.

## Candidate grid

SVM requires a finite set H of **consecutive integer h values**.

For example:

    H = (2, 3, 4, 5, 6)

when k=g=2.

The 0.17 API requires at least two candidates, strict increasing order, consecutive spacing, and every h>=g.

## Shared multiplier draws

Interval volatility should reflect changing h, not independent Monte Carlo randomness.

The scan therefore:

1. fits one fixed FPCA/MFPCA basis at max(H);
2. fits the k-component residual model once;
3. generates each wild pseudo-response once;
4. reuses that same pseudo-response across every candidate h;
5. recomputes the h-specific projection and bootstrap-level heteroscedastic studentization.

This also guarantees that the largest candidate exactly agrees with the standalone 0.16 wild-bootstrap inference when all other settings are equal.

## Interval width and center

For every target and candidate h, the scan retains:

- centered reference projection;
- heteroscedastic SE;
- bootstrap critical value;
- lower and upper limits;
- interval center;
- interval width;
- all studentized bootstrap roots.

The current 0.16/0.17 intervals are symmetric, so their center equals the reference h-component projection.

The center is still retained explicitly because SVM is defined through interval center and width.

## Stability rule

For a target, let w_h denote interval width and c_h interval center.

The transition beginning at h is width-stable when:

    abs(w_(h+1) - w_h) <= rho_w

and center-stable when:

    abs(c_(h+1) - c_h) <= rho_c

A stable transition satisfies both.

The package arguments are:

    width_threshold = rho_w
    center_threshold = rho_c

Both thresholds are required and strictly positive.

## The paper's r parameter

The paper defines a small integer r>=0 and chooses the earliest h for which the transition at h and the following r transitions are all stable.

Thus:

- r=0 requires one stable transition;
- r=1 requires two consecutive stable transitions;
- r=2 requires three consecutive stable transitions.

The API preserves that definition through <code>stability_run=r</code>.

## Why 0.01 is not a package default

The paper's numerical study illustrates SVM with rho_w=rho_c=0.01.

Those are **absolute** changes in interval width and center.

Their numerical meaning therefore depends on the outcome's units and scale.

eyetrajectoriespy requires analysts to supply both thresholds explicitly rather than transplanting 0.01 to every outcome.

## Target-specific h

The method can choose a different h for each target trajectory.

This is intentional: the paper notes that appropriate truncation can depend on the regressor X0 at which mean-response inference is performed.

The selection output therefore contains one selected h per target.

## What if no stable run exists?

The default is an error.

The package does not silently choose max(H), min(H), or the smallest-width interval.

For exploratory diagnostics, <code>on_failure="warn"</code> or <code>"ignore"</code> retains unselected targets with missing selected summaries.

Any later scientific decision remains explicit.

## Worked API

    scan = scan_wild_bootstrap_fpca_truncations(
        gaze,
        outcome,
        targets=targets,
        candidate_components=(2, 3, 4, 5, 6),
        n_bootstrap=1000,
        residual_components=2,
        scaling="dimension_sd",
        multiplier="normal",
        confidence_level=0.95,
        independent_unit_column="participant_id",
        random_state=2027,
    )

    selection = select_fpca_wild_bootstrap_truncation(
        scan,
        width_threshold=0.15,
        center_threshold=0.10,
        stability_run=1,
    )

## Plotting

Plot either width or center against h for one target:

    plot_fpca_wild_bootstrap_truncation_scan(
        selection,
        target=0,
        metric="width",
    )

When a selection is available, the selected h is marked.

## Interpretation

SVM is a practical inferential tuning heuristic.

It does not create an optimality guarantee for bootstrap coverage.

The paper explicitly notes that optimal truncation for coverage accuracy remains a topic for further investigation.

Treat the selected h as the output of a declared tuning rule, not as a universally optimal number of FPCs.

## Reporting example

> Residual truncation was fixed at k=2 and the bootstrap pseudo-truth used g=k. Wild-bootstrap intervals were then scanned over consecutive inference truncations h=2,...,6 using identical standard-normal multiplier draws across h within each bootstrap replicate. For each target, adjacent intervals were defined as stable when absolute width and center changes were no larger than 0.15 and 0.10 outcome units, respectively. Using r=1, the earliest h beginning two consecutive stable transitions was selected. Thresholds were specified before inspecting the final target conclusions; no default 0.01 criterion or largest-h fallback was used.

## API links

- <code>scan_wild_bootstrap_fpca_truncations()</code>
- <code>select_fpca_wild_bootstrap_truncation()</code>
- <code>FPCAWildBootstrapTruncationScanResult</code>
- <code>FPCAWildBootstrapTruncationSelectionResult</code>
- <code>fpca_wild_bootstrap_truncation_scan_frame()</code>
- <code>fpca_wild_bootstrap_truncation_selection_frame()</code>
- <code>plot_fpca_wild_bootstrap_truncation_scan()</code>
- <code>fpca_wild_bootstrap_truncation_reporting_text()</code>
- <code>cross_validate_fpca_regression()</code>
- <code>wild_bootstrap_fpca_projection()</code>
