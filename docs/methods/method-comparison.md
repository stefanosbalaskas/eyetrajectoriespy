# Method comparison

| Question | Functional trajectory method | What it is not |
|---|---|---|
| Preserve unequal sample times before analysis | native irregular trajectory representation | automatic resampling during import |
| Assess whether FPC shape is reproducible | bootstrap component matching | a significance test |
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

FDA and GAMMs are complementary: FPCA summarizes covariance and dominant modes; GAMMs model conditional mean structure over time.
