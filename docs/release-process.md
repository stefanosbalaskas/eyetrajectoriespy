# Coordinated GitHub Release and PyPI publication

## 1.0.0rc1 exact-version qualification

The 1.0 release candidate is qualified as a literal package identity over the frozen 455-stable/3-experimental API boundary. Historical 0.12 release evidence remains immutable. Fresh RC performance, the full pull-request matrix, protected-main merge, and the full exact-main matrix are required before a separate governance-only change may arm publication.


## Final 0.12.0 exact-version qualification

Final `0.12.0` is qualified as a literal package identity, not by relabelling `0.12.0rc1`. The RC release, production-installed observation, and archived RC performance evidence remain immutable inputs. Final qualification must generate fresh package-wide and sparse-MFPCA performance evidence under `0.12.0`, pass the complete pull-request matrix, merge through protected `main`, and pass the complete exact-main matrix. GitHub and PyPI publication remain disarmed until a separate governance-only arming change.



## 0.12.0rc1 qualification

Stable `0.11.0` remains the current public release. `0.12.0rc1` freezes the
fully qualified native sparse multivariate FPCA/joint-PACE 0.12 surface. The RC
may correct packaging, documentation, reproducibility, or release-governance
defects, but it must not add a new estimator, hidden default, or unqualified
statistical pathway.

The sequence is:

~~~text
align active version/citation/validation/docs contracts to 0.12.0rc1
        |
        v
generate a fresh exact-version performance envelope
        |
        v
rerun sparse-MFPCA recovery, sensitivity, external comparator,
observation stress, dedicated performance and ordinary package CI
        |
        v
merge exact qualified RC state through protected main
        |
        v
rerun complete exact-main 0.12.0rc1 matrix
        |
        v
arm publication in a separate reviewed governance-only change
        |
        v
manual target=production dispatch only
~~~

Pre-RC evidence is retained as development evidence and is never relabelled as
RC evidence. Publication remains fail-closed until the post-merge exact-main
matrix passes.

## 0.12.0rc1 release-candidate decision and qualification

Protected main commit `6b02310b4abb2d16e9df96293e9c8f1a63c34984`
closes the planned pre-RC evidence collection for native sparse multivariate
FPCA/joint PACE. The seven promotion criteria in the 0.12 design contract are
satisfied: the direct estimator/public API exists, analytical checks pass,
known-truth recovery passes, the internal two-stage benchmark is characterized,
mGSFPCA 0.2.2 sensitivity is reproducible, observation-process stress is
retained separately, and portability/docs/examples/performance/cross-platform
qualification are green.

The release decision is therefore **go to exact-version RC qualification**.
It is not a publication decision.

The 0.12 scientific/API surface is frozen during RC qualification. Only
release-version alignment, packaging/installability, documentation,
reproducibility, governance, and demonstrated defect fixes may change. A
scientific estimator, public parameter, hidden analytical default, automatic
selection rule, or post-0.12 research feature requires reopening development
rather than being slipped into the RC.

The RC sequence is:

~~~text
retain stable package identity 0.11.0 while recording the RC decision
        |
        v
align every active version declaration to 0.12.0rc1
        |
        v
generate fresh exact-version sparse-MFPCA and package performance evidence
        |
        v
rerun native recovery, comparator sensitivity, observation stress,
general simulation validation/stress, docs/examples and optional backends
        |
        v
pass the complete pull-request matrix
        |
        v
merge the exact qualified RC state through protected main
        |
        v
pass the complete exact-main 0.12.0rc1 matrix
        |
        v
arm GitHub/PyPI publication in a separate reviewed governance-only change
        |
        v
manual target=production release dispatch
        |
        v
verify GitHub Release, checksums/attestations and production PyPI
        |
        v
run fresh production-installed 0.12.0rc1 qualification
~~~

Pre-RC performance/recovery evidence remains evidence for the development
surface and must not be relabelled as exact-version `0.12.0rc1` evidence.

The production governance gate for 0.12 additionally requires successful
`sparse-mfpca-recovery`, `sparse-mfpca-sensitivity`,
`two-stage-sensitivity`, `mgsfpca-sensitivity`,
`observation-process-stress`, and
`sparse-mfpca-performance-envelope` checks. The sparse-MFPCA performance job
has a unique check name so it cannot be confused with the package-wide
`performance-envelope` gate.

The existing installed-RC workflow remains pinned to immutable published
`0.11.0rc1` until `0.12.0rc1` exists on production PyPI. Publication
readiness remains disarmed throughout RC qualification and is armed only in a
later reviewed change after exact-main qualification passes.

See the [planned 0.12.0rc1 release contract](releases/0.12.0rc1.md).

## Final 0.11.0 qualification and publication

Published `0.11.0rc1` is the feature-frozen public scientific candidate.
Final `0.11.0` is a version-only promotion of that surface: no estimator,
numerical method, generalized family, public API expansion, or hidden
analytical default may be added during final qualification.

Before final-version promotion, the production-installed rc1 artifact was
exercised outside the repository checkout. Exact protected-main commit
`a37214653c2f72839e356d603c4f87a514f01056` passed all eleven workflow
groups, including `installed-rc-qualification` run `36622305877`. That run
verified exact production-PyPI installation on Python 3.11–3.13, retained all
42 threshold-free stress replicate records, and exercised deterministic
scenario replay, dense FPCA recovery, mixed-effects recovery, registration
recovery, portable result round trips, reporting, and plotting.

The final sequence is:

~~~text
archive immutable 0.11.0rc1 performance evidence
        |
        v
align package/citation/validation/docs contracts to exact 0.11.0
and deliberately disarm publication readiness
        |
        v
generate a fresh 0.11.0 performance envelope
        |
        v
pass the complete pull-request qualification matrix
        |
        v
merge through protected main
        |
        v
pass the complete exact-main 0.11.0 matrix
        |
        v
arm release readiness in a separate reviewed governance-only change
        |
        v
manual target=production dispatch only
        |
        v
verify GitHub Release, checksums/attestations, PyPI publication,
and a fresh eyetrajectoriespy==0.11.0 production-PyPI install
~~~

The rc1 tag, GitHub Release, wheel, sdist, checksums, attestations, installed-RC
evidence, and performance snapshot remain immutable. Final qualification created
new exact-version evidence rather than relabeling rc1 evidence.

Final publication is complete. PR #121 armed publication only after the exact
final-version matrix passed; its protected-main merge commit
`2616675ad2dfc095bf17a442c1d350ba88fd030a` then passed the complete post-arming
matrix. Production release workflow #13 (run `36628220308`) created annotated
tag and GitHub Release `v0.11.0`, published the exact wheel and sdist to
production PyPI through OIDC Trusted Publishing with digital attestations, and
passed a fresh `eyetrajectoriespy==0.11.0` production-PyPI installation smoke
test. Post-publication readiness is disarmed again so ordinary pushes and merges
cannot republish the immutable release.

The threshold-free stress evidence remains descriptive. The known
estimated-noise diagonal-difference failures remain in the denominator and are
not converted to successful estimates by clipping or threshold widening.

## 0.11.0rc1 qualification

Stable `0.10.0` remains the current public release. `0.11.0rc1` promotes the
feature-frozen known-truth simulation/recovery laboratory from qualified
`0.11.0.dev0` without adding a new estimator, numerical method, generalized
family, hidden default, or post-0.11 research feature.

The rc1 qualification sequence is:

~~~text
archive immutable 0.11.0.dev0 performance evidence
        |
        v
align package/citation/validation/docs contracts to 0.11.0rc1
        |
        v
generate a fresh 0.11.0rc1 performance envelope
        |
        v
rerun functional-simulation qualification + threshold-free stress evidence
        |
        v
pass tests/docs/examples/optional-backend/sparse-native/release-readiness matrix
        |
        v
merge the exact qualified RC state
        |
        v
rerun exact release-state qualification
        |
        v
arm GitHub/PyPI publication in a separate reviewed change
        |
        v
manual target=production release dispatch
~~~

The stress workflow has no scientific pass/fail thresholds. Its success means
the declared stress study executed reproducibly and retained failed replicates;
it does not relabel difficult regimes as scientifically successful.

The qualification and expanded exact-main gates are now complete. A separate reviewed governance-only change arms GitHub and production readiness. No GitHub Release or PyPI upload occurs until the explicit manual `target=production` dispatch.

## Final 0.10.0 qualification and publication

Published `0.10.0rc2` is the corrected public scientific candidate. Final `0.10.0` is a promotion of that code line only: no estimator, numerical method, API contract, or hidden analytical default may be added during final qualification.

The final sequence is:

~~~text
align all active version declarations to 0.10.0
archive the immutable 0.10.0rc2 performance snapshot
        |
        v
generate a fresh 0.10.0 performance envelope
        |
        v
pass the complete pull-request matrix
        |
        v
merge through protected main
        |
        v
pass the complete exact-main matrix
        |
        v
arm release readiness in a separate reviewed change
        |
        v
manual target=production dispatch only
        |
        v
verify GitHub Release, PyPI artifacts, checksums/attestations,
and a fresh eyetrajectoriespy==0.10.0 production-PyPI install
~~~

The rc1 and rc2 tags, GitHub Releases, PyPI files, checksums and performance evidence remain immutable. Final qualification must create new exact-version evidence rather than relabeling either release candidate.

Final exact-version qualification and publication are complete. PR #106 exact head `3c24ba411700ebc1199057537056c411944071cd` passed all eight pull-request workflow groups; protected-main commit `b9172a578a07e433cce6cb9ec53825ccbd5d2d04` passed the first final-version exact-main matrix; PR #107 armed publication; and exact protected-main commit `1a14f2f6544b18740e73729ebe193ed348cb23bc` passed the complete post-arming main matrix. Production release workflow #11 (run `36550274400`) then created `v0.10.0`, published the checksum-verified wheel and sdist to production PyPI through Trusted Publishing, generated digital attestations, and passed a fresh `eyetrajectoriespy==0.10.0` production-PyPI installation smoke test. Publication readiness is disarmed after release.

## 0.10.0rc2 qualification

Published `0.10.0rc1` remains immutable. Recovery validation subsequently
identified a numerical defect in diagonal-difference measurement-noise
estimation: the latent diagonal was taken from the generic local-linear
covariance surface rather than the PACE-specific diagonal smoother.

`0.10.0rc2` contains the correction only. It introduces no new estimator
surface. The qualification sequence is:

~~~text
merge the source-faithful diagonal correction to protected main
        |
        v
align all version declarations to 0.10.0rc2
archive the immutable 0.10.0rc1 performance snapshot
        |
        v
generate a fresh 0.10.0rc2 performance envelope
        |
        v
pass the complete pull-request matrix
        |
        v
merge through protected main
        |
        v
pass the complete exact-main matrix
        |
        v
arm release readiness in a separate reviewed change
        |
        v
manual target=production dispatch only
~~~

The rc1 artifacts, tag and PyPI files remain immutable. The rc2 pull-request and exact-main qualification matrices passed, and production release workflow #10 subsequently published rc2 to GitHub and PyPI and verified a fresh production-PyPI installation. rc2 is therefore the immutable public candidate used as the scientific basis for final 0.10.0 promotion.

## Historical 0.10.0rc1 qualification and publication

The first 0.10 publication candidate was `0.10.0rc1`. It contains the native
sparse/irregular FPCA + PACE tranche already integrated into protected
`main`. Release-candidate qualification must not introduce a new scientific
estimator or hidden analytical default.

The qualification sequence is:

~~~text
align all version declarations to 0.10.0rc1
        |
        v
archive the 0.10.0.dev0 performance snapshot
        |
        v
generate a fresh 0.10.0rc1 performance envelope
        |
        v
pass the complete pull-request matrix
        |
        v
merge through protected main
        |
        v
pass the complete exact-main matrix
        |
        v
arm release readiness in a reviewed change
        |
        v
manual target=production dispatch only
~~~

The qualification branch and its pull request do not publish anything. A
production dispatch remains a separate deliberate action.

For the historical 0.10.0rc1 candidate, the fresh performance envelope, complete
pull-request matrix, protected-main merge, and complete exact-main matrix have
all passed. Release readiness is now jointly armed for GitHub and production
publication through a reviewed change. The remaining publication action is the
explicit manual `release.yml` dispatch with `target=production`; ordinary
pushes and merges remain non-publishing.

Version 0.9.0 uses the release machinery qualified during the 0.9.0rc1
ceremony. The final release is a separate immutable version; the RC remains a
prerelease record.

## One build, two publication surfaces

`.github/workflows/release.yml` owns the final ceremony:

~~~text
merge the fully qualified 0.9.0 PR to protected main
        |
        v
build wheel + sdist once
        |
        +--> twine check
        +--> fresh-wheel install + smoke test
        +--> fresh-sdist install + smoke test
        |
        v
wait for every exact-main required check
        |
        v
create annotated tag v0.9.0
create final GitHub Release
attach wheel + sdist + SHA256SUMS
        |
        v
download those exact GitHub Release assets
verify SHA256SUMS
remove checksum manifest from upload directory
        |
        v
publish the SAME wheel + sdist to production PyPI through OIDC
        |
        v
install eyetrajectoriespy==0.9.0 from production PyPI
run installed-package smoke test
~~~

The wheel and sdist are never rebuilt separately for GitHub and PyPI.

## Production and recovery triggers

Release automation is manual-dispatch only. Normal pushes and merges to
`main` never publish.

The workflow exposes four explicit targets:

~~~text
build-only
testpypi
production
resume-production
~~~

`production` is the ordinary publication path. It is intentionally strict:

1. all version declarations must agree;
2. the version must not be a development release;
3. GitHub must report exact protected `main`;
4. governance issue #64 must be closed;
5. all required exact-main qualification checks must pass, including `recovery`, threshold-free `stress-evidence`, and native sparse/PACE `sparse-performance`, `stress-recovery`, and `noise-variance-recovery` for the 0.11 release line;
6. the target GitHub tag/release must not already exist;
7. the target PyPI version must not already exist.

If any release/tag/version already exists, ordinary production fails. It does
not silently retain an existing GitHub Release and it does not use
`skip-existing` on production PyPI.

`resume-production` is a deliberately separate recovery path. It requires an
existing GitHub Release for the same version whose tag resolves to exact current
`main`. It then reuses those immutable GitHub Release artifacts and may use
PyPI `skip-existing` semantics to recover from a partially completed upload or
post-upload verification failure.

This separation enforces the ordinary invariant:

~~~text
one production invocation -> one previously unpublished version
~~~

while still providing an explicit audited recovery mechanism.

## Dedicated production PyPI authority

Production and recovery jobs use only:

~~~text
environment: pypi
PYPI_TRUSTED_PUBLISHING_CONFIGURED
PYPI_REQUIRED_REVIEWER_CONFIGURED
~~~

The `testpypi` environment is no longer accepted as production authority.
Issue #69 is closed: the obsolete production-publisher cleanup was completed,
and the dedicated production PyPI Trusted Publisher is registered with:

~~~text
Owner:       stefanosbalaskas
Repository:  eyetrajectoriespy
Workflow:    release.yml
Environment: pypi
~~~

The successful 0.9.0rc1, 0.9.0, 0.10.0rc2, and 0.10.0 OIDC publications are historical evidence that Trusted Publishing works. The dedicated `pypi` publisher claim remains the production authority for future release ceremonies.

## Optional TestPyPI rehearsal

Manual workflow dispatch remains available for:

- `build-only`;
- `testpypi`.

TestPyPI is optional for the final 0.9.0 ceremony because the RC already
exercised the complete production PyPI path successfully. It remains useful for
future publisher/environment migrations.

## Final 0.9.0 ceremony

1. Align package, citation, validation, workflow and documentation versions to
   `0.9.0`.
2. Archive the qualified RC performance snapshot.
3. Qualify a fresh `0.9.0` performance envelope.
4. Pass the complete pull-request matrix.
5. Merge to protected `main`.
6. Pass the complete exact-main matrix.
7. Create annotated tag `v0.9.0` and final GitHub Release.
8. Attach the exact wheel, sdist and `SHA256SUMS`.
9. Download and checksum-verify those exact release assets.
10. Publish only the wheel and sdist to production PyPI through OIDC.
11. Install exactly `eyetrajectoriespy==0.9.0` from production PyPI.
12. Run the installed-package canonical smoke test.

The ceremony is complete only after step 12 succeeds.


## Post-release development

After a stable release, `main` moves to a development version such as
`0.9.1.dev0`, and `RELEASE_READINESS.json` is disarmed. Ordinary development
therefore cannot accidentally republish the previous version or create a new
GitHub Release. A future release requires a reviewed version/readiness change
plus explicit `target=production` dispatch.
