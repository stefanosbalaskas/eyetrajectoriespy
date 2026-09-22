# References

## Eye-tracking functional data analysis

Dong M, Telesca D, Sugar C, et al. *A Functional Model for Studying Common Trends Across Trial Time in Eye Tracking Experiments*. Statistics in Biosciences. 2023;15:261–287. doi:10.1007/s12561-022-09354-6.

Kwan B, Sugar CA, Qian Q, et al. *Constrained Multivariate Functional Principal Components Analysis for Novel Outcomes in Eye-Tracking Experiments*. Statistics in Biosciences. 2024;16:578–603. doi:10.1007/s12561-023-09399-1.

## Sparse functional data / PACE

Yao F, Müller H-G, Wang J-L. *Functional Data Analysis for Sparse Longitudinal Data*. Journal of the American Statistical Association. 2005;100(470):577–590. doi:10.1198/016214504000001745.

FDApy 1.0.3 documentation: irregular functional-data representation, sparse UFPCA, covariance-operator estimation, and PACE score transformation.

Golovkine S. *FDApy: a Python package for functional data*. Journal of Open Source Software. 2025;10(107):7526. doi:10.21105/joss.07526.

Golovkine S. *FDApy: a Python package for functional data*. Version 1.0.3. Zenodo. 2025. doi:10.5281/zenodo.14944699.

## General FDA

Ramsay JO, Silverman BW. *Functional Data Analysis*. 2nd ed. Springer; 2005.

Wang J-L, Chiou J-M, Müller H-G. Functional Data Analysis. *Annual Review of Statistics and Its Application*. 2016;3:257–295.

## FPCA dimension selection and uncertainty

Hall P, Hosseini-Nasab M. *On Properties of Functional Principal Components Analysis*. Journal of the Royal Statistical Society: Series B. 2006;68(1):109–126. doi:10.1111/j.1467-9868.2005.00535.x.

Li Y, Wang N, Carroll RJ. *Selecting the Number of Principal Components in Functional Data*. Journal of the American Statistical Association. 2013;108(504). doi:10.1080/01621459.2013.788980.

Goldsmith J, Greven S, Crainiceanu C. *Corrected Confidence Bands for Functional Data Using Principal Components*. Biometrics. 2013;69(1):41–51. doi:10.1111/j.1541-0420.2012.01808.x.

## Sparse functional data and PACE

Yao F, Müller H-G, Wang J-L. *Functional Data Analysis for Sparse Longitudinal Data*. Journal of the American Statistical Association. 2005;100(470):577–590. doi:10.1198/016214504000001745.

Zhang X, Wang J-L. *From Sparse to Dense Functional Data and Beyond*. The Annals of Statistics. 2016;44(5):2281–2321. doi:10.1214/16-AOS1446.

FDApy documentation: `IrregularFunctionalData`, `UFPCA(method="covariance")`, and `transform(..., method="PACE")`.

## Eigenspace stability and principal angles

Björck Å, Golub GH. *Numerical Methods for Computing Angles Between Linear Subspaces*. Mathematics of Computation. 1973;27(123):579–594. doi:10.1090/S0025-5718-1973-0348991-3.

Hall P, Hosseini-Nasab M. *On Properties of Functional Principal Components Analysis*. Journal of the Royal Statistical Society: Series B. 2006;68(1):109–126. doi:10.1111/j.1467-9868.2005.00535.x.

Stewart GW, Sun J-G. *Matrix Perturbation Theory*. Academic Press; 1990.

## Software backends

`scikit-fda` provides general Python functional-data representations and estimators. `FDApy` provides dense/irregular functional representations and the sparse covariance-UFPCA/PACE backend used by the optional sparse workflow. `fdasrsf` provides elastic registration and SRVF curve statistics. `eyetrajectoriespy` adds eye-tracking-specific contracts, representations, safeguards, and workflows.


## Additional functional-data software

scikit-fda documentation: grid and basis representations, B-spline/Fourier bases, and FPCA.

FDApy documentation: dense, irregular, basis, and multivariate functional data representations, including sparse/irregular FPCA examples.

fdasrsf documentation: SRVF-based registration, multivariate curve alignment, Karcher means, warping functions, and shape PCA.


## Functional outlier diagnostics

Sun Y, Genton MG. Functional Boxplots. Journal of Computational and Graphical Statistics. 2011;20(2):316–334.

Dai W, Genton MG. Multivariate Functional Data Visualization and Outlier Detection. Journal of Computational and Graphical Statistics. 2018;27(4):923–934.

scikit-fda documentation includes functional boxplot, magnitude-shape, depth/outlyingness, and FPCA reconstruction-error outlier examples.


## Simultaneous functional mean inference

Degras D. *Simultaneous confidence bands for the mean of functional data*. WIREs Computational Statistics. 2017;9(3):e1397.

Liebl D, Reimherr M. *Fast and fair simultaneous confidence bands for functional parameters*. Journal of the Royal Statistical Society Series B. 2023;85(3):842–868. doi:10.1093/jrsssb/qkad026.

The current eyetrajectoriespy implementation uses a studentized Gaussian multiplier maximum over the observed common grid. It is intentionally narrower in scope than general continuous-domain confidence-band frameworks.


## Predictive functional principal-component regression

Hall P, Yang Y-J. *Ordering and Selecting Components in Multivariate or Functional Data Linear Prediction*. Journal of the Royal Statistical Society: Series B. 2010;72(1):93–110. doi:10.1111/j.1467-9868.2009.00727.x.

The fda.usc package documents cross-validation of the number of FPC predictors for scalar functional regression through `fregre.pc.cv`.

For binary probability prediction, log loss and Brier loss are proper scoring rules; eyetrajectoriespy therefore does not use thresholded accuracy as its FPC-count selection objective.


## Simultaneous FPC/eigensystem inference

- Hall, P., & Hosseini-Nasab, M. (2006). On properties of functional principal components analysis. *Journal of the Royal Statistical Society: Series B*, 68(1), 109–126. https://doi.org/10.1111/j.1467-9868.2005.00535.x
- Cai, L., & Hu, Q. (2024). Simultaneous inference and uniform test for eigensystems of functional data. *Computational Statistics & Data Analysis*, 192, 107900. https://doi.org/10.1016/j.csda.2023.107900
- Liebl, D., & Reimherr, M. (2023). Fast and fair simultaneous confidence bands for functional parameters. *Journal of the Royal Statistical Society: Series B*, 85(3), 842–868. https://doi.org/10.1093/jrsssb/qkad026

The eyetrajectoriespy FPC-band implementation is a matched/sign-aligned nonparametric bootstrap with studentized maximum calibration on the observed grid. It is not an implementation of the B-spline oracle eigensystem estimator of Cai and Hu, nor of the non-resampling fast-and-fair construction of Liebl and Reimherr.


## FPCA spectrum inference

- Hall, P., & Hosseini-Nasab, M. (2006). On properties of functional principal components analysis. *Journal of the Royal Statistical Society: Series B*, 68(1), 109–126. https://doi.org/10.1111/j.1467-9868.2005.00535.x
- Cai, L., & Hu, Q. (2024). Simultaneous inference and uniform test for eigensystems of functional data. *Computational Statistics & Data Analysis*, 192, 107900. https://doi.org/10.1016/j.csda.2023.107900

Hall and Hosseini-Nasab provide the theoretical motivation for bootstrap inference on FPCA eigenvalues/eigenfunctions and show that eigengap effects differ between eigenvalue and eigenfunction estimation. Cai and Hu construct asymptotically correct eigenvalue intervals and simultaneous eigensystem inference for dense B-spline-smoothed functional data.

The eyetrajectoriespy spectrum routine is a matched nonparametric studentized bootstrap around the package's grid-based FPCA/MFPCA estimator, not an implementation of Cai and Hu's spline oracle estimator.


## FPC score and decomposition uncertainty

- Yao, F., Müller, H.-G., Clifford, A. J., Dueker, S. R., Follett, J., Lin, Y., Buchholz, B. A., & Vogel, J. S. (2003). Shrinkage estimation for functional principal component scores with application to the population kinetics of plasma folate. *Biometrics*, 59(3), 676–685.
- Yao, F., Müller, H.-G., & Wang, J.-L. (2005). Functional data analysis for sparse longitudinal data. *Journal of the American Statistical Association*, 100(470), 577–590.
- Goldsmith, J., Greven, S., & Crainiceanu, C. (2013). Corrected confidence bands for functional data using principal components. *Biometrics*, 69(1), 41–51. https://doi.org/10.1111/j.1541-0420.2012.01808.x
- Fast Bayesian Functional Principal Components Analysis (2025). *Journal of Computational and Graphical Statistics*. https://doi.org/10.1080/10618600.2025.2592768

PACE/conditional-expectation methods explicitly treat subject-specific scores as estimated latent quantities for sparse data. Goldsmith et al. show that conditioning on an estimated FPC decomposition can understate uncertainty and use bootstrap decompositions in an iterated expectation/variance construction. Recent Bayesian FPCA work similarly emphasizes uncertainty in FPC estimates and downstream score use.

The eyetrajectoriespy 0.11 routine has a narrower purpose: fixed-target score sensitivity to re-estimation of the common-grid FPCA basis. It is not a PACE uncertainty estimator, the Goldsmith mixed-model correction, or a fully Bayesian FPCA.


## Functional principal-component regression inference

- González-Manteiga, W., & Martínez-Calvo, A. (2011). Bootstrap in functional linear regression. *Journal of Statistical Planning and Inference*, 141(1), 453–461. https://doi.org/10.1016/j.jspi.2010.06.027
- Khademnoe, O., & Hosseini-Nasab, S. M. E. (2016). On properties of percentile bootstrap confidence intervals for prediction in functional linear regression. *Journal of Statistical Planning and Inference*, 170, 129–143. https://doi.org/10.1016/j.jspi.2015.10.001
- Yeon, H. (2026). Gaussian and bootstrap approximations for functional principal component regression. arXiv:2603.12518. https://arxiv.org/abs/2603.12518
- Goldsmith, J., Greven, S., & Crainiceanu, C. (2013). Corrected confidence bands for functional data using principal components. *Biometrics*, 69(1), 41–51. https://doi.org/10.1111/j.1541-0420.2012.01808.x

The first two references motivate bootstrap inference and prediction in scalar-on-function functional linear regression. Yeon (2026) develops a distinct operator-scaled FPCR theory for Gaussian/bootstrap approximation and slope-significance testing. The eyetrajectoriespy 0.12 API is a paired full-pipeline percentile bootstrap and does not claim to reproduce that operator-scaled test.


## Gaussian FPCR slope bands and simultaneous inference

- Imaizumi, M., & Kato, K. (2019). A simple method to construct confidence bands in functional linear regression. *Statistica Sinica*, 29(4), 2055–2081. https://doi.org/10.5705/ss.202017.0208
- Yeon, H. (2026). Gaussian and bootstrap approximations for functional principal component regression. arXiv:2603.12518. https://arxiv.org/abs/2603.12518
- González-Manteiga, W., & Martínez-Calvo, A. (2011). Bootstrap in functional linear regression. *Journal of Statistical Planning and Inference*, 141(1), 453–461. https://doi.org/10.1016/j.jspi.2010.06.027

Imaizumi and Kato provide a theoretically justified PCA-based confidence-band construction for scalar-response functional linear regression. Yeon develops a distinct operator-scaled FPCR Gaussian/bootstrap theory and significance test. The eyetrajectoriespy 0.13 routine should be described more narrowly as a finite observed-grid studentized maximum calibration of its retained paired-bootstrap FPCR slope distribution.


## Functional-linear prediction intervals

- Cai, T. T., & Hall, P. (2006). Prediction in functional linear regression. *The Annals of Statistics*, 34(5), 2159–2179. https://doi.org/10.1214/009053606000000830
- González-Manteiga, W., & Martínez-Calvo, A. (2011). Bootstrap in functional linear regression. *Journal of Statistical Planning and Inference*, 141(1), 453–461. https://doi.org/10.1016/j.jspi.2010.06.027
- Khademnoe, O., & Hosseini-Nasab, S. M. E. (2016). On properties of percentile bootstrap confidence intervals for prediction in functional linear regression. *Journal of Statistical Planning and Inference*, 170, 129–143. https://doi.org/10.1016/j.jspi.2015.10.001
- Yeon, H., Dai, X., & Nordman, D. (2026). Wild bootstrap for mean response inference in functional linear regression models. arXiv:2606.16089.

The 0.14 implementation follows the conceptual separation between model-estimation uncertainty and response-noise uncertainty in bootstrap prediction. It does not implement the 2026 wild bootstrap and does not claim heteroscedasticity robustness.


## Conformal anomaly detection for functional data

- Kim, H., & Park, J. (2026). Conformal outlier detection for multivariate functional data. *Computational Statistics*, 41, Article 88. https://doi.org/10.1007/s00180-026-01763-1
- Adams, J., Berman, B., Michalenko, J., & Tucker, J. D. (2025). Conformal Anomaly Detection for Functional Data with Elastic Distance Metrics. *Proceedings of the Fourteenth Symposium on Conformal and Probabilistic Prediction with Applications*, PMLR 266, 666–686.
- Bates, S., Candès, E., Lei, L., Romano, Y., & Sesia, M. (2023). Testing for outliers with conformal p-values. *The Annals of Statistics*, 51(1), 149–178.

Kim and Park extend conformal outlier detection to multivariate functional data using functional-depth nonconformity and discuss marginal versus calibration-conditional p-values and FDR control. Adams et al. demonstrate inductive conformal anomaly detection using elastic functional distances, particularly for shape outliers.

eyetrajectoriespy 0.15 uses the standard marginal split-conformal p-value construction with package-native FPCA reconstruction or score-space Mahalanobis nonconformity. It does not claim to reproduce either paper's nonconformity score or the broader calibration-conditional/FDR procedures.


## Heteroscedastic functional-linear wild bootstrap

- Yeon, H., Dai, X., & Nordman, D. (2026). Wild bootstrap for mean response inference in functional linear regression models. *Statistica Sinica*, future paper / preprint SS-2025-0307; arXiv:2606.16089. https://arxiv.org/abs/2606.16089
- Mammen, E. (1993). Bootstrap and wild bootstrap for high dimensional linear models. *The Annals of Statistics*, 21(1), 255–285. https://doi.org/10.1214/aos/1176349025

Yeon, Dai & Nordman develop a fixed-regressor wild bootstrap for functional-linear mean-response inference that accommodates heterogeneous errors, separates residual/pseudo-truth/inference truncations, and emphasizes bootstrap-level studentization. Their companion BTSinFLRM implementation exposes several multiplier choices.

The eyetrajectoriespy 0.16 implementation is a narrower score-space analogue for common-grid Gaussian FPCR: g is fixed to k, h is explicit, normal and mathematically mean-zero/unit-variance Mammen multipliers are exposed, and only target-wise centered-projection intervals are returned.


### Stabilized-volatility truncation selection

Section 5.1 of Yeon, Dai & Nordman (2026) proposes the stabilized volatility method for selecting the wild-bootstrap inference truncation h.

With k selected separately and g=k, the method scans consecutive h values, tracks interval width and center, defines stability through absolute adjacent changes below rho_w and rho_c, and selects the earliest h beginning a run governed by a small integer r.

Their numerical study uses rho_w=rho_c=0.01 as an illustration. eyetrajectoriespy does not treat that simulation setting as a universal package default.


### Simultaneous fixed-target post-calibration

The 0.18 layer reuses the studentized roots generated by the heteroscedastic functional-linear wild-bootstrap construction and calibrates their replicate-wise maximum absolute value across a declared fixed-target family.

This follows the standard maximum-statistic logic used for simultaneous bootstrap inference while retaining the 0.16 fixed-regressor, heteroscedastic-studentization contract. The package describes this narrowly as a **familywise fixed-target post-calibration**; it does not claim a joint future-response prediction region or a new clustered-bootstrap theorem.

Primary methodological context remains:

- Yeon, H., Dai, X., & Nordman, D. (2026). Wild bootstrap for mean response inference in functional linear regression models. *Statistica Sinica*, future paper / preprint SS-2025-0307; arXiv:2606.16089.
- Mammen, E. (1993). Bootstrap and wild bootstrap for high dimensional linear models. *The Annals of Statistics*, 21(1), 255–285. https://doi.org/10.1214/aos/1176349025

The simultaneous family, confidence level, k/g/h truncations, and multiplier choice remain analyst-visible parts of the inferential contract.


### MaxT testing and adjusted p-values

- Hothorn, L. A., Ritz, C., Schaarschmidt, F., Jensen, S. M., & Ristl, R. (2024). Simultaneous Inference Using Multiple Marginal Models. *Pharmaceutical Statistics*, 24(1), e2428. https://doi.org/10.1002/pst.2428
- Westfall, P. H. (2011). On Using the Bootstrap for Multiple Comparisons. *Journal of Biopharmaceutical Statistics*, 21(6), 1187–1205.
- Yeon, H., Dai, X., & Nordman, D. (2026). Wild bootstrap for mean response inference in functional linear regression models. *Statistica Sinica*, future paper / preprint SS-2025-0307; arXiv:2606.16089.

Hothorn et al. describe low-dimensional simultaneous inference in which a maxT statistic provides a global union-intersection test and supports adjusted p-values alongside simultaneous intervals. Westfall discusses bootstrap maxT/minP approaches and the distinction between resampling-based multiplicity procedures and stronger familywise claims.

eyetrajectoriespy 0.19 uses a narrower construction: the studentized target-root matrix already generated by the 0.16 heteroscedastic functional-regression wild bootstrap is post-processed into target-wise tail probabilities, a single-step replicate-wise max-|t| adjustment, and one complete-family global test. The package does not automatically assume subset pivotality, does not run closed/step-down testing, and does not regenerate bootstrap samples under an imposed target null.

## Finite Monte Carlo precision for resampling p-values

- North, B. V., Curtis, D., & Sham, P. C. (2002). A note on the calculation of empirical P values from Monte Carlo procedures. *The American Journal of Human Genetics*, 71(2), 439–441. https://doi.org/10.1086/341527
- Phipson, B., & Smyth, G. K. (2010). Permutation P-values should never be zero: calculating exact P-values when permutations are randomly drawn. *Statistical Applications in Genetics and Molecular Biology*, 9(1), Article 39. https://doi.org/10.2202/1544-6115.1585
- Stoepker, I. V., & Castro, R. M. (2024). Inference with Sequential Monte-Carlo Computation of p-values: Fast and Valid Approaches. arXiv:2409.18908.

North, Curtis & Sham and Phipson & Smyth motivate finite-resampling corrections such as (r+1)/(B+1), rather than treating a zero observed exceedance count as a zero p-value. The 0.20 diagnostic keeps the configured 0.19 p-value rule unchanged and separately treats the retained exceedance count as a binomial Monte Carlo quantity for precision reporting.

Exact Clopper-Pearson intervals are used only to describe the finite-bootstrap exceedance probability conditional on the completed analysis. They are not confidence intervals for the scientific estimand. Stoepker & Castro emphasize that adaptive/sequential Monte Carlo stopping requires its own validity framework; eyetrajectoriespy 0.20 does not implement an always-valid sequential stopping procedure.
