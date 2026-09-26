# Coordinated GitHub Release and PyPI publication

Version 0.57 added the coordinated release machinery. The `0.9.0rc1`
release branch now exercises that machinery under the exact prerelease version,
but production publication remains fail-closed until branch protection,
TestPyPI rehearsal and PyPI environment/Trusted Publishing configuration are
complete.

## One build, two publication surfaces

`.github/workflows/release.yml` owns the coordinated release:

~~~text
merge the qualified release-candidate PR to protected main
        |
        v
build wheel + sdist once
        |
        +--> twine check
        +--> fresh-wheel smoke test
        +--> fresh-sdist smoke test
        |
        v
wait for exact-main required checks
        |
        v
create annotated version tag + GitHub prerelease
attach the exact wheel + sdist + SHA256SUMS
        |
        v
manual approval through pypi environment
        |
        v
publish the SAME wheel + sdist to PyPI through OIDC
        |
        v
install exact PyPI version and run smoke test
~~~

The distributions are never rebuilt separately for GitHub and PyPI.

## Production trigger

Production publication has **no manual workflow-dispatch path**. It starts from
the protected `main` push created by merging the qualified release-candidate
PR. The workflow waits for the exact-main required checks before creating the
version tag and GitHub Release.

Before publication, the workflow requires:

1. tag/version agreement across `pyproject.toml`, package `__version__`,
   `CITATION.cff`, canonical/validation/tolerance/performance manifests and
   the status roadmap;
2. a non-development production/prerelease version;
3. `main` reported protected by GitHub;
4. issue #64 closed;
5. the release commit to equal current `main`;
6. the full exact-main required check set to have completed successfully;
7. creation of an annotated version tag at that exact commit;
8. the `pypi` environment to expose explicit acknowledgements that Trusted
   Publishing and the required-reviewer gate are configured before PyPI
   publication.

The `pypi` publishing job receives `id-token: write` and no stored PyPI API
token.

## Optional TestPyPI rehearsal

Manual dispatch supports only:

- `build-only`;
- `testpypi`.

The TestPyPI path downloads the same `release-dist` artifact, publishes through
OIDC, installs the exact TestPyPI version while allowing dependencies from
normal PyPI, and runs the installed-package smoke test.

Before using it, configure a TestPyPI Trusted Publisher for:

~~~text
Owner:       stefanosbalaskas
Repository:  eyetrajectoriespy
Workflow:    release.yml
Environment: testpypi
~~~

and set the environment variable
`TESTPYPI_TRUSTED_PUBLISHING_CONFIGURED=true`.

## Production environment

For production PyPI, configure the Trusted Publisher as:

~~~text
Owner:       stefanosbalaskas
Repository:  eyetrajectoriespy
Workflow:    release.yml
Environment: pypi
~~~

The `pypi` GitHub environment should require a reviewer before deployment.
After configuration, set these environment variables:

~~~text
PYPI_TRUSTED_PUBLISHING_CONFIGURED=true
PYPI_REQUIRED_REVIEWER_CONFIGURED=true
~~~

These acknowledgements are not substitutes for the environment protection; they
make the intended configuration fail-closed and auditable from the workflow.

## First public release ceremony

For `0.9.0rc1`:

1. verify the active `main` ruleset and close issue #64;
2. configure the protected `pypi` environment and production Trusted
   Publisher;
3. keep `RELEASE_READINESS.json` truthful about GitHub-release and PyPI state;
4. align all release-version declarations to `0.9.0rc1`;
5. merge the release PR only after the complete PR-head matrix passes;
6. let the `main` push run `release.yml`;
7. wait for all exact-main required checks;
8. create annotated tag `v0.9.0rc1` and the GitHub prerelease first;
9. approve the protected `pypi` environment;
10. publish the exact same distributions to PyPI through OIDC;
11. verify installation of exactly `eyetrajectoriespy==0.9.0rc1`.

A TestPyPI rehearsal remains available but is not required for this GitHub-first
release sequence.

Because `0.9.0rc1` is a prerelease, ordinary dependency resolution should not
be described as equivalent to a final stable release. The verification command
uses `--pre` explicitly.
