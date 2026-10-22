# W3 R93/R93-A — exact original and independent observable-law evidence

**Scope:** exact rational binary-outcome counterexample conditional on one originally missing target stratum. This is neither a fitted continuous gaze model nor a frequentist validation study. The ledger retains original source/provenance and the independent mandatory artifact replay.

## Original exact proof and full source-artifact archive

| Item | Verified evidence |
|---|---|
| Original exact rational construction | [Draft research PR #456](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/456) |
| Original proof test and SHA256 archive jobs | [Run #39854975837](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39854975837) — **4/4 PASS** |
| Actual original exact 27-world source proof | [Artifact #12458809012](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39854975837/artifacts/12458809012) |
| Original ZIP digest | `sha256:26d3b03ae48d1a47cf002a32f275296948b8009a2e36a2f0f466e744ec705a2a` |
| Corrected original source branch head | `20e058cd188ef41b520bb64af3c3a0bf846d91d0` |
| Frozen original PR merge checkout | `6e874d0c2c91fcd22dceaf6aba61bcfc624d0b6b` |
| Event model | Known randomized invitation, unknown outcome-specific actual completion for binary bounded $Z$ |
| Conditional completion fractions | 99.9%, 99%, 95% |
| Invitation probabilities | 25%, 50%, 100% |
| Exactly distinct rational latent parameterizations | 27 |
| Equivalence cells | 9 |
| Randomized real-world participants or source blocks | **None** |

The original archive includes `exact_rational_evidence.json` and `SHA256SUMS`, and preserves each of the 27 exact rational models and all four observable event probabilities. The original GitHub workflow run binds artifact provenance to the original checkout. The artifact **does not** include a separately embedded `source-commit.txt`; no such file is claimed.

**Failure-inclusive CI note:** The original first attempt had three failing pytest jobs before the mathematics ran, because its minimal workflow installed only pytest while the repository's test `conftest.py` imports `matplotlib`. The research workflow was amended to install full repository development dependencies, without altering the proof equations, and the corrected 4/4 run above passed. Both CI records should be retained.

## Independent source algebra, SHA256 and exact likelihood audit

| Item | Verified evidence |
|---|---|
| Independent implementation | [Draft research PR #457](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/457) |
| Independent standalone algebra and mandatory original-archive replay | [Actions run #39855518388](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39855518388) — **4/4 PASS** |
| Actual independent full-source replay artifact | [Artifact #12459401983](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39855518388/artifacts/12459401983) |
| Independent ZIP SHA256 | `sha256:9b9e1761bffe6483e4c5f2e7990bd1610f352b529707c5da01d022bb7c114929` |

The independently coded R93-A script does **not** import the original R93 proof module or public eyetrajectoriespy methods. It independently reconstructs the outcome probabilities by assigning the invited nonreturn mass to the $Z=0$ group, to both equally, or to the $Z=1$ group. It verifies exact $p$, $c_0$, $c_1$, returned successes $q_0$, $q_1$, invited nonresponse, all source-likelihood probabilities, complete nine-cell/27-world keys and original SHA256 integrity. Three Python-version tests plus a separate **actual immutable source-artifact download and replay** passed. The audit tests equal product likelihood for observed event sequences, while the unconditional finite-length implication follows from equality of one-record distributions under the stated independent-record submodel.

## Exact sharp sets and interpretation

| Actual invited-record return | Exactly observed success masses $q_0=q_1$ | Sharp binary $p$ region | Width |
|---|---|---|---|
| 99.9% | 0.4995 | [0.4995, 0.5005] | 0.001 |
| 99% | 0.495 | [0.495, 0.505] | 0.010 |
| 95% | 0.475 | [0.475, 0.525] | 0.050 |

The sharp *population* region $p\in[q_1,1-q_0]$ is identified from the **observed distribution** and the assumed binary support, not a realized finite-sample confidence interval. With $g=0.50$ and 99% invited completion, all three latent worlds yield observed probabilities $(0.5, 0.2475, 0.2475, 0.005)$ in the order not invited, returned zero, returned one, invited nonresponse. Even $g=1$ leaves ambiguity if some assigned outcomes do not complete.

The **tiny** 0.001 gap at 99.9% completion is part of the result: high actual return narrows what remains unknown, but does not generally point-identify it. No statement about practical effect magnitude, superpopulation sampling uncertainty, correlated time-series trajectories or nominal functional confidence-band coverage follows from this existence counterexample.

## Website publication/release gates

The [article](../articles/w3-r93-exact-observed-law-nonidentification.md), [methods](../articles/w3-r93-exact-observability-methods.md), [sharp-set figure](../assets/w3-r93-sharp-binary-mean-sets.svg) and [exact observable-law figure](../assets/w3-r93-identical-observed-law-latent-worlds.svg) are documentation-only candidates. They require a strict documentation CI build and **all 25 exact-head PR workflows**, followed by a separately verified protected-main GitHub Pages `docs-build` and `deploy` success. Original research and audit PR #456/#457 remain draft/unmerged.

Unrestricted actual outcome-dependent return is not identified by randomized invitations alone. R93 does not claim identification for real missing gaze, arbitrarily correlated functional data, source-specific slope models or validated 90% simultaneous bands. Blockers [#296](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/296) and [#289](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/289) stay open. Public 1.1.0 unchanged, **v1.2/GitHub Release/PyPI HOLD**.
