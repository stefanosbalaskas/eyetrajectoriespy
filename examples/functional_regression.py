"""Predict a scalar outcome from continuous gaze through FPCA scores."""
import numpy as np
from eyetrajectoriespy import fit_mfpca, fit_scalar_on_function_regression, simulate_planar_trajectories

def main() -> None:
    gaze = simulate_planar_trajectories(n_participants=24, trials_per_participant=3, n_time=81, random_state=21)
    fit = fit_mfpca(gaze, n_components=5, scaling="dimension_sd")
    rng = np.random.default_rng(21)
    outcome = 2.0 + 0.8 * fit.scores[:, 0] - 0.4 * fit.scores[:, 1] + rng.normal(0, 0.15, gaze.n_curves)
    result = fit_scalar_on_function_regression(fit, outcome, n_components=3)
    print(result.coefficients)
    print("R2:", result.model.rsquared)

if __name__ == "__main__":
    main()
