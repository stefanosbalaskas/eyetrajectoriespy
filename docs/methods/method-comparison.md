# Method comparison

| Question | Functional trajectory method | What it is not |
|---|---|---|
| Preserve unequal sample times before analysis | native irregular trajectory representation | automatic resampling during import |
| Assess whether FPC shape is reproducible | bootstrap component matching | a significance test |
| Simultaneous mean uncertainty on a common grid | studentized Gaussian multiplier maximum | independent pointwise intervals treated as a global band |
| Flag trajectories for functional review | reconstruction + robust score-space diagnostics | an automatic exclusion rule |
| Assess whether one participant/group drives the basis | leave-one-group-out FPCA influence | proof that the group is invalid |
| Quantify what registration changes | pre/post registration FPC matching | proof that registration is beneficial |
| Model timing deformation itself | phase FPCA on warpings | ordinary spatial FPCA |
| Dominant whole-curve variation | FPCA/MFPCA | time-point significance testing |
| Participant vs trial variation | multilevel FPCA | ordinary PCA treating trials as independent |
| Same shape, different timing | registration / elastic FDA | automatically “better preprocessing” |
| AOI allocation over time | compositional FPCA | independent PCA of bounded proportions |
| Condition-specific smooth mean | often GAMM | FPCA by itself |
| Exact onset of divergence | specialized onset methods | FPCA loading inspection |
| Predict scalar outcome | functional regression / score regression | causal mediation by default |
| Predict an external scalar outcome while tuning retained FPC count | fold-local FPCA regression CV / nested CV | variance-explained or reconstruction selection |

FDA and GAMMs are complementary: FPCA summarizes covariance and dominant modes; GAMMs model conditional mean structure over time.


## Pointwise versus simultaneous FPC uncertainty

| Goal | Preferred tool | Important boundary |
|---|---|---|
| visualize local bootstrap variability of an FPC | matched pointwise envelope | descriptive only; no whole-curve coverage claim |
| whole-grid uncertainty statement for one FPC | component-wise simultaneous FPC band | observed grid only; individual axis must be identifiable |
| joint whole-grid statement across several FPCs | familywise simultaneous FPC band | more conservative; near-tied axes still require subspace interpretation |
| robust interpretation under near-tied eigenvalues | principal-angle subspace analysis | answers an eigenspace question, not individual-axis uncertainty |
