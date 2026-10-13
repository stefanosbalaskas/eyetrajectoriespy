# W3 R16 — original matched leverage × covariance results

!!! danger "Exploratory source evidence: no calibrated pointwise or simultaneous bands"
    All inclusion counts are known-truth *pointwise* midpoint comparisons, not simultaneous coverage. No method selection, empirical covariance oracle, production estimator or release qualification is inferred from the present study.

## Source provenance

- Draft research [PR #308](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/308), exact original run head `c859147068f161b2bce08a987ad1032a3df5f886`, [Actions run #38461655638](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38461655638).
- Original scientific job plus Python 3.11, 3.12 and 3.13 tests: **4/4 succeeded**.
- **2,304/2,304** planned model/source cases recorded and completed, **zero failures and zero missing records**.
- Only **96 independently generated source blocks**, reused in nested participant sizes, covariance conditions and bases. Table rows and nested conditions are paired, not statistically independent experiments.
- Original scientific artifact [#11845817636](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/38461655638/artifacts/11845817636) has been uploaded; original manifest checksum comparison against the archive has **not yet been independently verified in this report**.

## Original source results

Nominal 90% known-truth pointwise midpoint-slope inclusion. Numerators are counts out of 96 independent generating blocks within each condition. Jackknife is the centered delete-person CV3J comparator, not CR2.

| Participants | Mean basis | Leverage | Covariance | CR1 / 96 | CV3J / 96 | Oracle / 96 | Mean CR1/oracle SE | Max block leverage |
|---:|---|---|---|---:|---:|---:|---:|---:|
| 24 | legendre5 | ordinary | independent | 89 | 92 | 89 | 0.957 | 0.188 |
| 24 | cubic_spline13 | ordinary | independent | 86 | 90 | 88 | 0.962 | 0.202 |
| 24 | legendre5 | extreme | independent | 77 | 84 | 85 | 0.832 | 0.468 |
| 24 | cubic_spline13 | extreme | independent | 77 | 86 | 88 | 0.836 | 0.492 |
| 24 | legendre5 | ordinary | dependent | 82 | 84 | 89 | 0.954 | 0.188 |
| 24 | cubic_spline13 | ordinary | dependent | 82 | 84 | 89 | 0.953 | 0.202 |
| 24 | legendre5 | extreme | dependent | 75 | 83 | 90 | 0.754 | 0.468 |
| 24 | cubic_spline13 | extreme | dependent | 76 | 84 | 91 | 0.749 | 0.492 |
| 48 | legendre5 | ordinary | independent | 85 | 87 | 86 | 0.978 | 0.092 |
| 48 | cubic_spline13 | ordinary | independent | 86 | 87 | 86 | 0.985 | 0.100 |
| 48 | legendre5 | extreme | independent | 74 | 85 | 80 | 0.912 | 0.341 |
| 48 | cubic_spline13 | extreme | independent | 76 | 84 | 85 | 0.914 | 0.361 |
| 48 | legendre5 | ordinary | dependent | 85 | 85 | 85 | 0.968 | 0.092 |
| 48 | cubic_spline13 | ordinary | dependent | 85 | 86 | 87 | 0.973 | 0.100 |
| 48 | legendre5 | extreme | dependent | 86 | 87 | 89 | 0.848 | 0.341 |
| 48 | cubic_spline13 | extreme | dependent | 80 | 86 | 90 | 0.843 | 0.361 |
| 96 | legendre5 | ordinary | independent | 86 | 86 | 87 | 0.983 | 0.045 |
| 96 | cubic_spline13 | ordinary | independent | 86 | 86 | 86 | 0.987 | 0.050 |
| 96 | legendre5 | extreme | independent | 84 | 85 | 85 | 0.956 | 0.226 |
| 96 | cubic_spline13 | extreme | independent | 82 | 84 | 82 | 0.955 | 0.241 |
| 96 | legendre5 | ordinary | dependent | 83 | 85 | 88 | 0.976 | 0.045 |
| 96 | cubic_spline13 | ordinary | dependent | 84 | 85 | 88 | 0.980 | 0.050 |
| 96 | legendre5 | extreme | dependent | 85 | 86 | 90 | 0.918 | 0.226 |
| 96 | cubic_spline13 | extreme | dependent | 84 | 85 | 90 | 0.913 | 0.241 |


## Scientific interpretation and limitations

At n=24, extreme leverage degrades CR1 coverage even when the participant random slope is **predictor-independent**. For Legendre-5, ordinary/independent versus extreme/independent CR1 truth counts are 89 versus 77 of 96; corresponding mean CR1/oracle SE ratios are 0.957 versus 0.832. The extreme/dependent combined condition reaches 75/96 and ratio 0.754. The fitted conditional mean is represented by both fixed bases, with shared participant innovations, trials and timestamps across conditions.

This confirms a source-specific, independently seeded finite-cluster leverage contribution *not requiring predictor-dependent random-slope covariance*. The stronger combined stress indicates that the covariance mechanism can compound the effect. No hypothesis-test family was prespecified to prove a universal interaction; observed rates have Monte Carlo uncertainty. In the source study, centered CV3J often improves extreme-cell inclusion without consistently reaching 90%, and the oracle is known-source-only.

The present original script records maximum participant information-block leverage, **not** focal contrast partial leverage or effective independent-cluster information. The latter remain required diagnostics; independently validated CR2 bias-reduced linearization and associated degrees-of-freedom reference also remain outstanding. Do not relabel centered CV3J as CR3 or assume interchangeable variants.

Do not interpret 2,304 paired evaluations as independent Monte Carlo datasets. Real asynchronous gaze support and W3 simultaneously calibrated intervals remain open blockers. See [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) and [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296). Stable 1.1.0 is unchanged; development `1.2.0rc2.dev0` is unreleased, `production_release_ready=false`, and no merge to protected main, tag or PyPI upload is authorized.
