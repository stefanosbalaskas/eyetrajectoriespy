# References

## Eye-tracking functional data analysis

Dong M, Telesca D, Sugar C, et al. *A Functional Model for Studying Common Trends Across Trial Time in Eye Tracking Experiments*. Statistics in Biosciences. 2023;15:261–287. doi:10.1007/s12561-022-09354-6.

Kwan B, Sugar CA, Qian Q, et al. *Constrained Multivariate Functional Principal Components Analysis for Novel Outcomes in Eye-Tracking Experiments*. Statistics in Biosciences. 2024;16:578–603. doi:10.1007/s12561-023-09399-1.

## Sparse functional data / PACE

Yao F, Müller H-G, Wang J-L. *Functional Data Analysis for Sparse Longitudinal Data*. Journal of the American Statistical Association. 2005;100(470):577–590. doi:10.1198/016214504000001745.

FDApy 1.0.3 documentation: irregular functional-data representation, sparse UFPCA, covariance-operator estimation, and PACE score transformation.

Golovkine S. *FDApy: A Python Package to Analyze Functional Data*. Software repository/Zenodo release, 2024.

## General FDA

Ramsay JO, Silverman BW. *Functional Data Analysis*. 2nd ed. Springer; 2005.

Wang J-L, Chiou J-M, Müller H-G. Functional Data Analysis. *Annual Review of Statistics and Its Application*. 2016;3:257–295.

## FPCA dimension selection and uncertainty

Hall P, Hosseini-Nasab M. *On Properties of Functional Principal Components Analysis*. Journal of the Royal Statistical Society: Series B. 2006;68(1):109–126. doi:10.1111/j.1467-9868.2005.00535.x.

Li Y, Wang N, Carroll RJ. *Selecting the Number of Principal Components in Functional Data*. Journal of the American Statistical Association. 2013;108(504). doi:10.1080/01621459.2013.788980.

Goldsmith J, Greven S, Crainiceanu C. *Corrected Confidence Bands for Functional Data Using Principal Components*. Biometrics. 2013;69(1):41–51. doi:10.1111/j.1541-0420.2012.01808.x.

## Eigenspace stability and principal angles

Björck Å, Golub GH. *Numerical Methods for Computing Angles Between Linear Subspaces*. Mathematics of Computation. 1973;27(123):579–594. doi:10.1090/S0025-5718-1973-0348991-3.

Hall P, Hosseini-Nasab M. *On Properties of Functional Principal Components Analysis*. Journal of the Royal Statistical Society: Series B. 2006;68(1):109–126. doi:10.1111/j.1467-9868.2005.00535.x.

Stewart GW, Sun J-G. *Matrix Perturbation Theory*. Academic Press; 1990.

## Software backends

`scikit-fda` provides general Python functional-data representations and estimators. `fdasrsf` provides elastic registration and SRVF curve statistics. `eyetrajectoriespy` adds eye-tracking-specific contracts, representations, safeguards, and workflows.


## Additional functional-data software

scikit-fda documentation: grid and basis representations, B-spline/Fourier bases, and FPCA.

FDApy documentation: dense, irregular, basis, and multivariate functional data representations, including sparse/irregular FPCA examples.

fdasrsf documentation: SRVF-based registration, multivariate curve alignment, Karcher means, warping functions, and shape PCA.


## Functional outlier diagnostics

Sun Y, Genton MG. Functional Boxplots. Journal of Computational and Graphical Statistics. 2011;20(2):316–334.

Dai W, Genton MG. Multivariate Functional Data Visualization and Outlier Detection. Journal of Computational and Graphical Statistics. 2018;27(4):923–934.

scikit-fda documentation includes functional boxplot, magnitude-shape, depth/outlyingness, and FPCA reconstruction-error outlier examples.
