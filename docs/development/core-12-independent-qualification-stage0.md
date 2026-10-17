# Independent core 1.2 release-qualification track (stage 0)

!!! danger "NOT a 1.2.0rc2 candidate or publication authorization"
    Source identity remains `1.2.0rc2.dev0`. The only declared stable public
    version remains `1.1.0`. The purpose of this draft is to establish and
    test a *separate, non-Bayesian release scope*; it does **not** declare
    the full core API scientifically qualified or create a literal release.

## Two tracks and hard isolation boundary

**Candidate core track**: existing mature W1–W4/estimator functionality that
can pass its own independent source, installed-wheel, known-truth, performance,
documentation, portability and exact-version acceptance contracts. A frozen
root export inventory and reviewed scientific support claims must be approved
before the literal release candidate stage. Stage 0 captures root export
count/hash only; it does **not** misrepresent that inventory as already
independently frozen.

**Experimental research track**: draft Bayesian B6/B7 NUTS/native Gibbs
(including R4/R5), experimental F1 inferential group permutation, F5
dependence-sensitive change-point p-values and F2/F3/F4/F6 extensions
awaiting their own scientific gates. No unqualified inferential claims
shall be added to core release documentation or public root exports.

The connected repository's [Bayesian blocker #255](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/255),
[F5 blocker #256](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/256),
[F1–F6 expansion #226](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/226)
and [literal RC2 qualification #225](https://github.com/stefanosbalaskas/eyetrajectoriespy/issues/225)
are independently tracked. None is closed by this scope audit.

## Fresh development-source checks, not relabelled RC1 evidence

1. Verify the development version in pyproject, root __version__ and
   RELEASE_READINESS.json; publication remains disarmed.
2. Parse the public package root with AST. Fail closed on imports from
   experimental namespaces and direct exposure of known unsupported
   inferential symbols; retain root-source SHA256 and export count.
3. Test the fail-closed rule by deliberately injecting a forbidden export,
   arming release readiness and substituting a literal version in a copy.
4. Build a **new** development wheel, validate with Twine, install into an
   isolated virtual environment, and run the existing FPCA release smoke
   outside the source checkout with runtime path and version checks.
5. Archive source and installed-wheel evidence with exact commit/workflow
   provenance. No GitHub Release, tag, TestPyPI or PyPI upload occurs.

## Candidate decision deferred

The subsequent literal `1.2.0rc2` qualification branch must replace
development identity consistently, regenerate fresh exact-version scientific
and performance ledgers, freeze and review all supported exports and defaults,
run Linux/macOS/Windows × Python 3.11–3.13 plus installed wheel/sdist
and documentation checks on PR head and protected main. Neither immutable
RC1 evidence nor experimental Bayesian findings may be relabelled as RC2.

Only a subsequent independent governance approval may arm publication.
