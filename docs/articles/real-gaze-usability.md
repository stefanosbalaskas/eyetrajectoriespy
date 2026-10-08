# Authentic gaze E1–E4: research usability qualification

This reproduces a **real published eye-tracking observation** workflow, not a known-truth accuracy benchmark. The runnable source is [real_gaze_e1_e4_usability.py](https://github.com/stefanosbalaskas/eyetrajectoriespy/blob/main/examples/real_gaze_e1_e4_usability.py). Its [GitHub Actions qualification](https://github.com/stefanosbalaskas/eyetrajectoriespy/actions/workflows/real-gaze-usability.yml) retains audit CSVs, the figures and the generated reporting manifest.

## Source and permissions

The data are sourced from the [DFKI Disagreement Detection Dataset (CHI 2026)](https://github.com/DFKI-Interactive-Machine-Learning/Disagreement-Detection-Dataset-CHI-26), pinned to upstream Git commit `1a92e69487c862a80496d7a80c86e8f4f5a857bf`. This third-party dataset is released under **Creative Commons Attribution–NonCommercial 4.0 (CC BY-NC 4.0)**. Retain attribution and comply with that licence when running or reusing the case. This repository does **not** distribute the original raw gaze data or relicense them.

The script downloads exactly 16 prespecified per-trial CSVs and verifies each original Git blob SHA1 and raw-byte SHA256. It reads only timestamp, x and y gaze columns; it neither uses outcome/disagreement classification labels nor facial or other participant attributes. Derived reports use freshly pseudonymized participant/trial keys, not source filenames.

## Exact pipeline

1. **Source identity:** retrieve source files from immutable upstream Git commit; fail closed on missing, altered or malformed files; record per-record source fingerprints.
2. **Measured samples:** retain the actual first 0–480 ms at 4 ms intervals, using an *exact* timestamp intersection, with absent gaze cells left missing. Do not perform nearest-neighbour interpolation.
3. **Sample accounting:** record all 16 considered windows, all missing coordinates and any excluded windows; only fully observed windows enter the *explicitly declared* complete-case dense FPCA. This analyst decision can cause selection bias and must not be concealed.
4. **E2:** run preflight on the full pre-exclusion set, recording observed/missing support, units and participant/trial nesting.
5. **E1:** on the declared complete-case subset, run mild Gaussian smoothing (which may affect saccade profiles), then affine time normalization. Retain the full step and units audit.
6. **FPCA + E3:** fit a two-component dense planar FPCA workflow and compare the descriptive retained-variance fraction under one, two and three components. An intentionally invalid component count is retained as a recorded failed fit—never a zero numeric estimate.
7. **E4:** produce a manuscript-oriented Markdown report, four derived figures, input sample accounting, workflow decisions, warnings and SHA256 evidence manifest.

The raw source material is **not copied into workflow artifacts**.

## Run locally

```bash
python -m pip install -e ".[dev]"
python examples/real_gaze_e1_e4_usability.py --output build/real-gaze-usability
```

Run from an exact 1.2 development checkout with network access to the pinned source repository. The command will fail if a source changes, the temporal grid is incompatible, the declared complete-case sample is too small or the failed-sensitivity record is absent. No synthetic observations are substituted.

The report includes `scientific-report/report.md`, `scientific-report/manifest.json`, four genuine observation/result-derived SVG figures, `input-selection-audit.csv`, `preflight-original-support.csv`, `preprocessing-audit.csv`, `sensitivity-values.csv` and `usability-evidence.json`. Sample exclusions, stage execution times and missingness are preserved rather than silently optimized.

## Interpretation and limitations

The successful CI run on the first 16 trial files fitted 15 complete-case windows and retained one excluded window in the audit. This is an **end-to-end research usability demonstration** of authentic eye-tracking complications, not a representative population analysis, a hypothesis test, or a known-truth validation of FPCA components. No claim about the source paper's behavioral findings follows from this software case. The complete-case rule may bias the represented trials; the chosen early window and smoothing choices are methodological decisions, not universally recommended defaults.

The stable release remains **1.1.0**. Experimental E1–E4 interfaces and this case remain **unpublished 1.2 development surfaces** until separate candidate qualification, exact-main checks and release governance succeed.
