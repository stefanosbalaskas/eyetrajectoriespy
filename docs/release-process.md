# Coordinated GitHub Release and PyPI publication

Version 0.57 adds release machinery but does **not** publish the development
version to production PyPI.

The intended first public release remains \`0.9.0rc1\`, after 0.57 hardening,
branch protection, TestPyPI rehearsal and PyPI environment configuration are
complete.

## One build, two publication surfaces

\`.github/workflows/release.yml\` owns the coordinated release:

~~~text
verified version tag
        |
        v
build wheel + sdist once
        |
        +--> twine check
        +--> fresh-wheel smoke test
        +--> fresh-sdist smoke test
        |
        v
upload immutable release-dist artifact
        |
        v
production governance gate
        |
        v
manual approval through pypi environment
        |
        v
publish exact files to PyPI through OIDC
        |
        v
create GitHub Release and attach the same wheel + sdist
        |
        v
install exact PyPI version and run smoke test
~~~

The distributions are never rebuilt separately for GitHub and PyPI.

## Production trigger

Production publication has **no manual workflow-dispatch path**. It is triggered
only by a version tag matching \`v*\`.

Before publication, the workflow requires:

1. tag/version agreement across \`pyproject.toml\`, package \`__version__\`,
   \`CITATION.cff\`, canonical/validation/tolerance/performance manifests and
   the status roadmap;
2. a non-development production version;
3. \`main\` reported protected by GitHub;
4. issue #64 closed;
5. the release tag to target current \`main\`;
6. an annotated tag whose signature GitHub reports as verified;
7. the full exact-main required check set to have completed successfully;
8. the \`pypi\` environment to expose explicit acknowledgements that Trusted
   Publishing and the required-reviewer gate are configured.

The \`pypi\` publishing job receives \`id-token: write\` and no stored PyPI API
token.

## TestPyPI rehearsal

Manual dispatch supports only:

- \`build-only\`;
- \`testpypi\`.

The TestPyPI path downloads the same \`release-dist\` artifact, publishes through
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
\`TESTPYPI_TRUSTED_PUBLISHING_CONFIGURED=true\`.

## Production environment

For production PyPI, configure the Trusted Publisher as:

~~~text
Owner:       stefanosbalaskas
Repository:  eyetrajectoriespy
Workflow:    release.yml
Environment: pypi
~~~

The \`pypi\` GitHub environment should require a reviewer before deployment.
After configuration, set these environment variables:

~~~text
PYPI_TRUSTED_PUBLISHING_CONFIGURED=true
PYPI_REQUIRED_REVIEWER_CONFIGURED=true
~~~

These acknowledgements are not substitutes for the environment protection; they
make the intended configuration fail-closed and auditable from the workflow.

## First public release ceremony

After 0.57 is closed:

1. enable/verify the \`main\` ruleset and close issue #64;
2. complete one TestPyPI rehearsal;
3. configure the protected \`pypi\` environment and production Trusted
   Publisher;
4. update \`RELEASE_READINESS.json\` through a reviewed PR;
5. change all release-version declarations to \`0.9.0rc1\`;
6. merge the release PR only after the complete matrix passes;
7. create a signed annotated \`v0.9.0rc1\` tag at exact \`main\`;
8. allow \`release.yml\` to build once and reach the \`pypi\` environment;
9. approve the protected deployment;
10. let OIDC publish to PyPI;
11. create the GitHub Release from the same distributions;
12. verify installation of exactly \`eyetrajectoriespy==0.9.0rc1\`.

Because \`0.9.0rc1\` is a prerelease, ordinary dependency resolution should not
be described as equivalent to a final stable release. The verification command
uses \`--pre\` explicitly.
