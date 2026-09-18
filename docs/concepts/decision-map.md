# Analysis decision map

**Where does gaze move over trial time?**  
Use joint 2-D MFPCA on x/y trajectories.

**How does distance from a target evolve?**  
Create a landmark-distance function and use univariate FPCA or another functional model.

**Are stable participant strategies different from trial-to-trial fluctuations?**  
Use multilevel FPCA.

**How does allocation among several AOIs evolve?**  
Use compositional AOI probability functions. Do not run independent PCA on probabilities that must sum to one.

**Do people use a similar spatial route but at different speeds/times?**  
Compare unregistered and registered/elastic analyses. Preserve the warping functions as phase outcomes.

**Does a trajectory predict a scalar response?**  
Use retained FPCA scores as a transparent low-dimensional approximation, or a specialist functional regression estimator when required.

## Before fitting anything

1. Verify coordinate geometry is comparable.
2. Decide whether absolute latency is part of the construct.
3. Resolve missingness explicitly.
4. Decide whether smoothing is defensible.
5. Decide whether channels retain native scales or are equalized.
6. Pre-specify component retention and interpretation.
