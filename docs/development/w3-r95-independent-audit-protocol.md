# R95-A independent frozen original-data observed-law and monotonicity audit

This is a separately implemented rational identity verification of R95, **not a new simulation**. The independent auditor never imports the original R95 routine or production estimators.

The original research draft [PR #462](https://github.com/stefanosbalaskas/eyetrajectoriespy/pull/462) has frozen source SHA 1223015d70cb74c31e8f8cdeb0d088ccf0855b25. Its dedicated [science workflow #39872191344](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39872191344) passed 4/4. Its original archive [#12466408311](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/runs/39872191344/artifacts/12466408311) contains 54 exact rational cases and SHA256SUMS.

### Independent mathematical factorization

Let invited returned subprobabilities be $q_0,q_1$, invited nonreturn fraction $\delta=1-q_0-q_1$, and hidden unreturned $Z=1$ mass $t\in[0,\delta]$. Then true binary outcome mean is $p=q_1+t$. The assumption $c_1\ge c_0$ is independently equivalent to $t\le q_1\delta/(q_0+q_1)$; reverse direction gives the opposite inequality; equality fixes $t$ at that boundary. An externally stipulated response ratio cap $c_1/c_0\le1+\delta$ and positive direction implies $t\ge q_1(\delta-\delta q_0)/(q_1+(1+\delta)q_0)$. Intersections with $[0,\delta]$ construct sharp bounds and exact latent response witnesses.

Full immutable replay verifies every original record, its complete four-category observed-data likelihood, response ratio witnesses, hypothetical assumption label, archived SHA256 checksum and no-release flags. Any tampered, omitted, duplicated or noncanonical record fails closed.

### Publication gate

The independent CI must pass three separate Python-version contract jobs AND its mandatory pinned-artifact original full replay job. Only then may a separate documentation-only PR be prepared with article, methods, figures, provenance ledger and website navigation; that PR requires full exact-head CI and its own protected-main Pages publication gate.

This result is conditional binary population identification under externally known direction and does not identify the actual gaze response mechanism, supply finite-sample confidence intervals, calibrate W3 90% functional confidence bands or authorize v1.2/PyPI release. Research source PRs remain draft/unmerged; blockers #289/#296 remain OPEN.
