# R94 methods: sharp binary mean sets conditional on externally guaranteed response floors

*Exact rational source derivation and independent immutable-original replay · 23 October 2026*

## Scope and observation sigma-field

Condition on one originally missing binary-outcome target stratum. Let $Z\in\{0,1\}$ with $p=P(Z=1)$; audit invitation $I$ is independent of $Z$, with known probability $g>0$; if invited, a completed return indicator $R$ may depend on $Z$. The observable event law consists of not invited, invited-returned $Z=0$, invited-returned $Z=1$, and invited-nonreturn. Its masses are $1-g,gq_0,gq_1,g(1-q_0-q_1)$, where $q_z=P(R=1,Z=z\mid I=1)$.

Assume only for sensitivity analysis that some **external information** guarantees actual completion probabilities $c_z=P(R=1\mid I=1,Z=z)\ge\ell_z$. These guarantees are not derived from the observed returns and must not be represented as measurements of eye-tracker recovery.

## Sharp identified-set derivation

The mass constraints $q_1=pc_1$ and $q_0=(1-p)c_0$, with $c_0,c_1\le1$, imply $p\ge q_1$ and $p\le1-q_0$. For positive $\ell_0,\ell_1$, $c_0\ge\ell_0$ implies $p\ge1-q_0/\ell_0$, and $c_1\ge\ell_1$ implies $p\le q_1/\ell_1$. Thus

$$
L=\max\{q_1,1-q_0/\ell_0\},\qquad
U=\min\{1-q_0,q_1/\ell_1\}.
$$

Drop the associated ratio term for each zero floor. If $L>U$, no binary source law satisfies all assumptions. Otherwise every $p\in[L,U]$ has valid witness $c_0=q_0/(1-p)$, $c_1=q_1/p$; in particular both endpoints are attainable and the region is **sharp**.

### Independent proof parameterization

R94-A did not call the original interval routine. It wrote the missing outcome $Z=1$ mass as $t\in[0,\delta]$, with $\delta=1-q_0-q_1$. Then $p=q_1+t$, the hidden $Z=0$ mass is $\delta-t$, and the response-floor constraints independently imply

$$
t\ge \delta-q_0(1/\ell_0-1),\quad
t\le q_1(1/\ell_1-1),
$$

where each condition is omitted if its floor is zero. Intersect this with $[0,\delta]$. Agreement of these independently derived intervals with original R94 across the immutable 54-record archive, including every endpoint witness and every empty region, is the audit contract.

## Frozen factorial, negative controls and arithmetic

Three nonresponse fractions $\delta\in\{1/1000,1/100,1/20\}$, three invitation probabilities $g\in\{1/4,1/2,1\}$, and six prespecified external floor scenarios form exactly 54 cells. Define symmetric observation masses $q_0=q_1=(1-\delta)/2$. The invited nonreturn is exactly $\delta$; the *unconditional* event mass of nonreturn is $g\delta$. Therefore $g$ changes event frequencies, not the conditional-on-invitation sharp region.

The six floor regimes are: $(0,0)$; $(1-2\delta,1-2\delta)$; $(1-3\delta/2,1-3\delta/2)$; $(1-\delta,1-\delta)$; $(1-\delta,1-2\delta)$; and $(1-\delta/2,1-\delta/2)$. The first two must leave the region width at $\delta$; the third has width $\delta/[2(1-1.5\delta)]$; the fourth gives a singleton $1/2$; the fifth has width $\delta/2$; and the sixth is incompatible for every positive frozen $\delta$.

Each original and independent calculation uses Python's exact rational Fraction type, canonical numerator/denominator strings in the archived JSON, deterministic row ordering and a SHA256 manifest. **There are no random seeds, Monte Carlo observations, fitted models, resampling estimators or independent data-generating blocks.** Cells do not provide frequentist coverage evidence.

## Verification and reproducibility

- Original draft research PR #459, frozen head 142d63a551d0e61d776f3b604b5d3cd865b0c2e7: dedicated workflow #39863137968, **4/4 successful** (Python 3.11–3.13 identity/integrity tests and SHA256 output archive). Actual original artifact **#12461918445** contains all 54 source cells.
- Separate draft research/audit PR #460, frozen head ff6d8ec2a77452e79a1c6f041e3609996a9be908: dedicated workflow #39863696029, **4/4 successful** (independent three-version tests and mandatory download/checksum/full replay of the actual original archive). Independent audit artifact **#12462204809**. The auditor imports no original R94 proof script and no package inference implementation.
- The 54 cells contain **45 compatible** source/assumption laws with explicit endpoint witnesses and **9 incompatible** external-floor assumptions. This is 45 and 9 distinct frozen *mathematical cases*, not independent participants, fits or coverage trials.

## Interpretive and publication limits

Sharp *population* identification conditional on externally warranted minimum completion probabilities does not prove that the minimum completion probabilities hold in real records. In noisy finite samples an empty population identified region must not be mistaken for an automatic statistical rejection. This binary i.i.d. countermodel cannot be transferred without proof to dependent continuous gaze, functional slopes, irregular trajectories or physiological features. Neither W3 field-MNAR blocker #296 nor whole-grid nominal-90% simultaneous-band blocker #289 is resolved.

The original and independent research PRs stay draft/unmerged; docs publication is documentation-only after an independent exact-head CI/strict build and successful protected-main Pages deployment. Stable 1.1.0, v1.2 release hold, public API, PyPI and tags remain unchanged.
