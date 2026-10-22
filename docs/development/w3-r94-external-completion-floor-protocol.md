# R94 research-only protocol: sharp identification with externally assumed response floors

**Frozen 23 October 2026, before CI.** This is an exact mathematical sensitivity analysis extending the R93 binary nonidentification counterexample. It does not create a gaze estimator, identify field MNAR, validate 90% simultaneous bands or authorize a release. Original and independent scientific PRs stay draft/unmerged, issues #289 and #296 stay open, v1.2/GitHub/PyPI remain on hold.

In the originally missing binary stratum define observed masses conditional on randomized audit invitation: $q_0=P(R=1,Z=0\mid I=1)$, $q_1=P(R=1,Z=1\mid I=1)$. Invitation rate $g>0$ is known. Add hypothetical **external** lower guarantees on actual completion $c_0\ge\ell_0$ and $c_1\ge\ell_1$. The guarantees are NOT estimated or identified from the observed audit outcomes.

The exact sharp population identification region for $p=P(Z=1)$ is

$$
p\in\left[\max\left\{q_1,\,1-\frac{q_0}{\ell_0}\right\},
\min\left\{1-q_0,\,\frac{q_1}{\ell_1}\right\}\right],
$$

omitting a ratio term when its floor is zero. An empty interval means the stipulated guarantees are incompatible with the observed population law. At every feasible $p$ the completion model $c_0=q_0/(1-p)$, $c_1=q_1/p$ reproduces the exact observed law and satisfies both lower bounds. These endpoint witnesses establish sharpness, rather than merely necessary inequalities.

**Frozen 54 cases:** 3 nonreturn rates $\delta=0.001,0.01,0.05$ × 3 known invitation rates $g=.25,.50,1$ × 6 floor scenarios. Fix $q_0=q_1=(1-\delta)/2$. External floor scenarios: unrestricted $(0,0)$; weak common $(1-2\delta,1-2\delta)$; moderate common $(1-3\delta/2,1-3\delta/2)$; strong common $(1-\delta,1-\delta)$; asymmetric $(1-\delta,1-2\delta)$; and deliberately overstrong incompatible $(1-\delta/2,1-\delta/2)$.

**Prospectively specified tests:** all 54 cases without silent exclusions, exact rational Fractions, 3 Python-version tests and tamper-sensitive SHA256 artifact. The unrestricted and weak cases must retain width $\delta$; moderate must shrink without point identification; strong common must produce the singleton $p=1/2$; asymmetric must halve the original width; overstrong must be flagged as logically incompatible. Invitation randomization alone must not change conditional identified sets. **An independently coded R94-A auditor must download and fully replay the immutable original 54-case artifact** before the results may be published as documentation or SVG figures.

**Interpretive boundary:** strong externally guaranteed outcome-specific response floors are assumptions about information unavailable from observed outcomes; in this symmetric construction a minimum at the observed aggregate response rate forces both propensities to that rate. This does not empirically establish uniform return. These are sharp *population* identified regions, not confidence intervals, Monte Carlo coverage or functional-slope uncertainty statements. No package, tag, GitHub release, PyPI or API update is authorized.
