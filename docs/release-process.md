# Coordinated GitHub Release and PyPI publication

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

## Production trigger

Production publication is now explicit-dispatch only. Normal pushes and merges
to `main` never publish. A maintainer must run `release.yml` manually with
`target=production` from the exact protected `main` commit after the version
has been changed from a `.devN` line to a qualified release version.

The workflow verifies:

1. all current version declarations agree;
2. the selected target is explicitly `production`;
3. the version is not a development release;
4. GitHub reports `main` protected;
5. governance issue #64 is closed;
6. the dispatched commit is current `main`;
7. all required exact-main scientific, packaging, documentation, examples,
   optional-backend, performance and release-readiness checks have completed
   successfully.

Only then is the annotated final tag and GitHub Release created.

## Production PyPI

The PyPI job has `id-token: write` and uses
`pypa/gh-action-pypi-publish`; no long-lived PyPI API token is stored.

The successful 0.9.0rc1 ceremony proved the production Trusted Publishing/OIDC
path and production-PyPI clean-install verification. For the 0.9.0 final
release, the same registered publisher claim is retained so the final ceremony
can reproduce the proven path.

At present the working production Trusted Publisher claim is bound to the
GitHub environment named `testpypi`. This naming is not ideal and is tracked
in issue #69. It does not change the destination: the production job publishes
to `https://upload.pypi.org/legacy/`. Before a later release, migrate that
publisher claim to the dedicated protected `pypi` environment and update the
workflow/acknowledgement variables together.

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
