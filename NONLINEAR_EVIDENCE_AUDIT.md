# Nonlinear evidence audit

**Audit date:** 2026-09-23

Nonlinear dynamics, recurrence analysis, local divergence/Lyapunov estimation, surrogate testing, and empirical return-map context for eyetrajectoriespy.

## Evidence rule

Verification means that the bibliographic record was recovered from a primary publisher, PubMed/PMC, or another authoritative scholarly index. Failure to verify a candidate citation is not evidence that no related work exists and must never be used as proof of novelty.

The evidence tiers are intentionally descriptive:

- **Direct behavioral-gaze evidence:** Peer-reviewed application or methods paper using recurrence/RQA on behavioral eye-movement or fixation-sequence data.
- **Direct eye/pupil signal evidence:** Peer-reviewed application/methods paper using the method on eye-movement or pupil time-series signals, but not necessarily continuous behavioral scanpath analysis.
- **General methodological evidence:** Foundational or methodological source supporting the algorithm, estimator, null model, or recurrence framework outside a specific behavioral-gaze application.

A verified citation supports only the claim stated in **Supports**. The **Does not support** field is part of the scientific contract and prevents a nearby real paper from being used to justify a stronger claim.

## Direct behavioral-gaze evidence

### Anderson, N. C., Bischof, W. F., Laidlaw, K. E. W., Risko, E. F., & Kingstone, A. (2013). Recurrence quantification analysis of eye movements. Behavior Research Methods, 45(3), 842-856.

- **DOI:** https://doi.org/10.3758/s13428-012-0299-5
- **Method tags:** `rqa`, `fixation_sequences`, `eye_movements`
- **Verification source:** https://pubmed.ncbi.nlm.nih.gov/23344735/
- **Supports:** Direct behavioral eye-movement precedent for RQA applied to fixation sequences and temporal scanpath structure.
- **Does not support:** Does not by itself validate every continuous-state, windowed, cross-recurrence, or functional-RQA design choice in eyetrajectoriespy.

### Gurtner, L. M., Bischof, W. F., & Mast, F. W. (2019). Recurrence quantification analysis of eye movements during mental imagery. Journal of Vision, 19(1), 17.

- **DOI:** https://doi.org/10.1167/19.1.17
- **Method tags:** `rqa`, `eye_movements`, `mental_imagery`
- **Verification source:** https://pubmed.ncbi.nlm.nih.gov/30699229/
- **Supports:** Direct behavioral-gaze precedent for RQA as a temporal eye-movement analysis alongside spatial scanpath methods.
- **Does not support:** Does not establish independence of overlapping windowed RQA values or an FDA inferential theorem for RQA-derived functions.

## Direct eye/pupil signal evidence

### Korda, A. I., Asvestas, P. A., Matsopoulos, G. K., Ventouras, E. M., & Smyrnis, N. (2018). Automatic identification of eye movements using the largest Lyapunov exponent. Biomedical Signal Processing and Control, 41, 10-20.

- **DOI:** https://doi.org/10.1016/j.bspc.2017.11.004
- **Method tags:** `largest_lyapunov`, `local_divergence`, `saccades`, `blinks`
- **Verification source:** https://www.sciencedirect.com/science/article/pii/S1746809417302574
- **Supports:** Direct eye-movement signal-analysis precedent for largest-Lyapunov/log-divergence methods in saccade and blink identification.
- **Does not support:** Does not establish that a positive behavioral-scanpath LLE proves deterministic chaos, nor that LLE is a novel eye-movement method.

### Mesin, L., Monaco, A., & Cattaneo, R. (2013). Investigation of nonlinear pupil dynamics by recurrence quantification analysis. BioMed Research International, 2013, 420509.

- **DOI:** https://doi.org/10.1155/2013/420509
- **Method tags:** `rqa`, `pupil`, `nonlinear_dynamics`
- **Verification source:** https://pubmed.ncbi.nlm.nih.gov/24187665/
- **Supports:** Direct pupil-signal precedent for nonlinear recurrence quantification.
- **Does not support:** Does not establish a behavioral scanpath interpretation for pupil recurrence metrics.

### Piu, P., Serchi, V., Rosini, F., & Rufa, A. (2019). A cross-recurrence analysis of the pupil size fluctuations in steady scotopic conditions. Frontiers in Neuroscience, 13, 407.

- **DOI:** https://doi.org/10.3389/fnins.2019.00407
- **Method tags:** `cross_recurrence`, `pupil`, `crqa`
- **Verification source:** https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2019.00407/full
- **Supports:** Direct pupil-signal precedent for cross-recurrence analysis.
- **Does not support:** Does not imply that cross-recurrence automatically time-aligns two trajectories or establishes causal synchronization.

### Fink, L., Simola, J., Tavano, A., Lange, E., Wallot, S., & Laeng, B. (2024). From pre-processing to advanced dynamic modeling of pupil data. Behavior Research Methods, 56, 1376-1412.

- **DOI:** https://doi.org/10.3758/s13428-023-02098-1
- **Method tags:** `pupil`, `rqa`, `dynamic_modeling`, `methods_review`
- **Verification source:** https://pubmed.ncbi.nlm.nih.gov/37351785/
- **Supports:** Modern methodological precedent discussing RQA and signal-to-signal dynamic analysis for pupil time series, including assumptions and software context.
- **Does not support:** Does not make every recurrence analysis design appropriate for gaze coordinates or remove the need for method-specific sampling contracts.

## General methodological evidence

### Eckmann, J.-P., Oliffson Kamphorst, S., & Ruelle, D. (1987). Recurrence plots of dynamical systems. Europhysics Letters, 4(9), 973-977.

- **DOI:** https://doi.org/10.1209/0295-5075/4/9/004
- **Method tags:** `recurrence_plot`, `dynamical_systems`
- **Verification source:** https://doi.org/10.1209/0295-5075/4/9/004
- **Supports:** Foundational recurrence-plot methodology.
- **Does not support:** Does not provide eye-tracking-specific interpretation or parameter-selection rules.

### Marwan, N., Romano, M. C., Thiel, M., & Kurths, J. (2007). Recurrence plots for the analysis of complex systems. Physics Reports, 438(5-6), 237-329.

- **DOI:** https://doi.org/10.1016/j.physrep.2006.11.001
- **Method tags:** `recurrence_plot`, `rqa`, `cross_recurrence`
- **Verification source:** https://doi.org/10.1016/j.physrep.2006.11.001
- **Supports:** General definitions, variants, interpretation, and cautions for recurrence plots and RQA.
- **Does not support:** Does not establish behavioral-eye-tracking novelty or an automatic parameter policy.

### Coco, M. I., & Dale, R. (2014). Cross-recurrence quantification analysis of categorical and continuous time series: an R package. Frontiers in Psychology, 5, 510.

- **DOI:** https://doi.org/10.3389/fpsyg.2014.00510
- **Method tags:** `cross_recurrence`, `crqa`, `behavioral_time_series`
- **Verification source:** https://pubmed.ncbi.nlm.nih.gov/25018736/
- **Supports:** General CRQA methodology for continuous and categorical behavioral time series, including lag/coupling interpretation.
- **Does not support:** Does not mean cross-recurrence performs synchronization or time alignment automatically.

### Wallot, S., & Leonardi, G. (2018). Analyzing multivariate dynamics using cross-recurrence quantification analysis (CRQA), diagonal-cross-recurrence profiles (DCRP), and multidimensional recurrence quantification analysis (MdRQA) - a tutorial in R. Frontiers in Psychology, 9, 2232.

- **DOI:** https://doi.org/10.3389/fpsyg.2018.02232
- **Method tags:** `cross_recurrence`, `crqa`, `multidimensional_rqa`
- **Verification source:** https://pubmed.ncbi.nlm.nih.gov/30564161/
- **Supports:** Practical CRQA and multidimensional recurrence methodology in cognitive/behavioral time-series analysis.
- **Does not support:** Does not establish that CRQA alone identifies causal coupling.

### Fraser, A. M., & Swinney, H. L. (1986). Independent coordinates for strange attractors from mutual information. Physical Review A, 33(2), 1134-1140.

- **DOI:** https://doi.org/10.1103/PhysRevA.33.1134
- **Method tags:** `embedding_delay`, `average_mutual_information`
- **Verification source:** https://doi.org/10.1103/PhysRevA.33.1134
- **Supports:** Average-mutual-information motivation for delay diagnostics.
- **Does not support:** Does not justify silent automatic delay selection for finite noisy gaze data.

### Kennel, M. B., Brown, R., & Abarbanel, H. D. I. (1992). Determining embedding dimension for phase-space reconstruction using a geometrical construction. Physical Review A, 45(6), 3403-3411.

- **DOI:** https://doi.org/10.1103/PhysRevA.45.3403
- **Method tags:** `embedding_dimension`, `false_nearest_neighbors`
- **Verification source:** https://doi.org/10.1103/PhysRevA.45.3403
- **Supports:** False-nearest-neighbor diagnostic methodology.
- **Does not support:** Does not provide a universal eye-tracking embedding-dimension cutoff.

### Rosenstein, M. T., Collins, J. J., & De Luca, C. J. (1993). A practical method for calculating largest Lyapunov exponents from small data sets. Physica D, 65(1-2), 117-134.

- **DOI:** https://doi.org/10.1016/0167-2789(93)90009-P
- **Method tags:** `largest_lyapunov`, `local_divergence`
- **Verification source:** https://doi.org/10.1016/0167-2789(93)90009-P
- **Supports:** Estimator family implemented by eyetrajectoriespy for nearest-neighbor mean log-divergence and fitted slope.
- **Does not support:** Does not create a universal minimum sample-size threshold or prove chaos from a positive fitted slope.

### Kantz, H. (1994). A robust method to estimate the maximal Lyapunov exponent of a time series. Physics Letters A, 185(1), 77-87.

- **DOI:** https://doi.org/10.1016/0375-9601(94)90991-1
- **Method tags:** `largest_lyapunov`, `local_divergence`, `sensitivity`
- **Verification source:** https://www.sciencedirect.com/science/article/pii/0375960194909911
- **Supports:** Independent methodological precedent for local-divergence-based maximal Lyapunov estimation and sensitivity thinking.
- **Does not support:** Is not the estimator currently exposed by eyetrajectoriespy and should not be cited as if Kantz's algorithm were implemented.

### Schreiber, T., & Schmitz, A. (1996). Improved surrogate data for nonlinearity tests. Physical Review Letters, 77(4), 635-638.

- **DOI:** https://doi.org/10.1103/PhysRevLett.77.635
- **Method tags:** `surrogate_testing`, `iaaft`
- **Verification source:** https://pubmed.ncbi.nlm.nih.gov/10062864/
- **Supports:** IAAFT-style iterative surrogate construction and null-model framing.
- **Does not support:** Does not make rejection proof of deterministic chaos or a unique nonlinear mechanism.

### Schreiber, T., & Schmitz, A. (2000). Surrogate time series. Physica D, 142(3-4), 346-382.

- **DOI:** https://doi.org/10.1016/S0167-2789(00)00043-9
- **Method tags:** `surrogate_testing`, `null_model`
- **Verification source:** https://www.sciencedirect.com/science/article/pii/S0167278900000439
- **Supports:** Surrogate-data hypothesis-testing framework, practical caveats, and the requirement to state the null model.
- **Does not support:** Does not validate independent univariate IAAFT as a multivariate x-y gaze surrogate preserving cross-structure.

## Unverified candidate citations from the research report

The following entries were present in the supplied research report but were not recovered by the exact-title/author verification pass used for this audit. They are **not treated as false citations**, and their absence from this search is **not evidence of novelty or nonexistence**. They are excluded from the package bibliography unless independently verified.

### Recurrence analysis of eye movements in visual search

- **Attributed authors:** Klaffehn, Heimann, & Gilchrist
- **Attributed year:** 2021
- **Audit status:** `not_verified_in_2026-09-23_audit`
- **Action:** Exact-title/author searches used for this audit did not recover a matching scholarly record. Do not cite unless independently verified.

### Cross-recurrence quantification analysis of pupil and gaze trajectories

- **Attributed authors:** Dixon & DiBiasio
- **Attributed year:** 2016
- **Audit status:** `not_verified_in_2026-09-23_audit`
- **Action:** Exact-title/author searches used for this audit did not recover a matching scholarly record. Genuine nearby CRQA/pupil literature exists, but it is not this citation.

### Lyapunov exponents of eye movements in ADHD vs. control

- **Attributed authors:** Chang et al.
- **Attributed year:** 2018
- **Audit status:** `not_verified_in_2026-09-23_audit`
- **Action:** Exact-title/author searches used for this audit did not recover a matching scholarly record. Use verified Korda et al. 2018 for direct eye-movement LLE precedent.

### Dynamical systems and eye movements: Attractor dimension predicts search efficiency

- **Attributed authors:** Bruineberg et al.
- **Attributed year:** 2018
- **Audit status:** `not_verified_in_2026-09-23_audit`
- **Action:** Exact-title/author searches used for this audit did not recover a matching scholarly record. Do not cite unless independently verified.

### Attractor reconstruction from eye movement series in strabismus and nystagmus

- **Attributed authors:** Hayen, Harper, & Henson
- **Attributed year:** 2015
- **Audit status:** `not_verified_in_2026-09-23_audit`
- **Action:** Exact-title/author searches used for this audit did not recover a matching scholarly record. Do not cite unless independently verified.

## Package evidence hierarchy

1. **Embedding + recurrence/RQA:** core methodology with direct behavioral eye-movement precedent.
2. **Local divergence / Rosenstein LLE + surrogate testing:** advanced methodology; LLE has direct eye-movement signal precedent, but behavioral-scanpath interpretation remains conditional and requires stronger safeguards.
3. **Empirical Poincare return-map stability:** experimental observational descriptor; no claim of classical Floquet stability is made.
4. **Classical Floquet, monodromy, numerical continuation, SINDy/Koopman/neural ODEs:** outside the raw-gaze core unless an explicit validated dynamical model is introduced.

## Novelty language

The package does not infer novelty from a failed literature or package search. Allowed wording is limited to statements such as "no implementation was identified in the searches performed" or "not verified in this audit."

Website evidence page: https://stefanosbalaskas.github.io/eyetrajectoriespy/methods/nonlinear-evidence-audit/
