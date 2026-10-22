# R95 methods: monotone completion shape and exact sharp population mean sets

*Algebraic, not empirical; 23 October 2026*

## Population experiment

Condition on a fixed originally missing binary outcome $Z\in\{0,1\}$. $p=P(Z=1)$ is latent, randomized audit invitation $I$ has known $g=P(I=1)>0$, and actual completed return $R$ has unknown outcomes-specific $c_0=P(R=1\mid Z=0,I=1)$ and $c_1=P(R=1\mid Z=1,I=1)$. Observed returned-outcome masses conditional on invitation are $q_0=(1-p)c_0$, $q_1=pc_1$, total invited nonresponse $\delta=1-q_0-q_1$.

The four mutually exclusive *observable* events and their probabilities are: $I=0$ with mass $1-g$; returned $Z=0$ with mass $gq_0$; returned $Z=1$ with mass $gq_1$; invited nonreturn with mass $g\delta$. Each latent completion model in the exact research archive reproduces these four masses exactly.

## Exact shape-conditioned identification

The unrestricted sharp mean interval is $p\in[q_1,1-q_0]$. Positive response probabilities imply

$$
\frac{c_1}{c_0}=\frac{q_1(1-p)}{q_0p}.
$$

Therefore, for an *externally justified* known direction:

$$
\begin{array}{ll}
c_1\ge c_0:&p\in[q_1,q_1/(q_0+q_1)],\\
c_0\ge c_1:&p\in[q_1/(q_0+q_1),1-q_0],\\
c_1=c_0:&p=q_1/(q_0+q_1).
\end{array}
$$

If the stronger positive directional ratio bound $1\le c_1/c_0\le1+\delta$ is also externally justified, the sharp set becomes

$$
p\in\left[\max\left\{q_1,\frac{q_1}{q_1+(1+\delta)q_0}\right\},
\frac{q_1}{q_0+q_1}\right].
$$

An unknown *sign* of monotonicity is the union of the two directional sets, hence the unrestricted region; one must not report it as informative. Every feasible $p$ is witnessed by the exact latent completion probabilities $c_0=q_0/(1-p)$, $c_1=q_1/p$, establishing sharpness.

## Independent unseen-mass derivation

R95-A independently defines unknown unreturned $Z=1$ mass $t\in[0,\delta]$ so $p=q_1+t$. $c_1\ge c_0$ becomes $t\le q_1\delta/(q_0+q_1)$; reverse direction requires $\ge$; equality sets $t$ to that value. The additional upper ratio bound gives

$$
t\ge\frac{q_1(\delta-\delta q_0)}{q_1+(1+\delta)q_0}.
$$

Intersect those inequalities with $[0,\delta]$, then return $p=q_1+t$ at both endpoints. This independent derivation does not import the original R95 source module or a production package estimator.

## Frozen design and arithmetic verification

Three exact invited nonreturn fractions $1/1000,1/100,1/20$, three invitation probabilities $1/4,1/2,1$, and six externally stipulated shape regimes yield **54 deterministic exact rational records**. Each has $q_0=q_1=(1-\delta)/2$. The six regimes are unrestricted, $c_1\ge c_0$, $c_0\ge c_1$, $c_1=c_0$, $1\le c_1/c_0\le1+\delta$, and direction unknown. The last regime is a deliberately negative restriction-control: it must never tighten the unrestricted set.

Three Python-version original identity/integrity checks precede the immutable original SHA256 evidence artifact. Independently programmed R95-A contract checks precede mandatory full SHA256 replay of the **original** archived 54 cells. No random seeds, simulated participants, confidence coverage evaluations or sample replicates occur. A case is a mathematical condition, not an independent unit of evidence.

In this frozen symmetric population law, the six widths are $\delta,\delta/2,\delta/2,0,\delta/[2(2+\delta)],\delta$ respectively. The sharp set is invariant to $g$ because the returned masses are conditional on being invited, though observable joint event probabilities depend on $g$.

## Qualification boundary

The identified sets are conditional on externally warranted sign/equality/ratio restrictions. The observed likelihood alone does not establish any direction. These bounds do not generalize automatically to functional dependent gaze trajectories, multitime missingness processes or simultaneous 90% functional slope confidence bands. A mathematically zero-width identified set under the strong equality restriction is not a validated real-data estimator.

Both research PRs remain draft/unmerged. Release blockers #289/#296 remain open; no public package API update, v1.2 release, tag or PyPI action is authorized.
