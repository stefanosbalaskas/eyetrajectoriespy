"""Optional scikit-fda basis projection with explicit basis specification."""

from eyetrajectoriespy import simulate_planar_trajectories, to_skfda_basis


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=8,
        trials_per_participant=2,
        n_time=61,
    )
    projection = to_skfda_basis(
        gaze,
        dimension="x",
        basis="bspline",
        n_basis=10,
        order=4,
    )
    print("basis:", projection.basis_type)
    print("n_basis:", projection.n_basis)
    print("coefficient shape:", projection.backend_object.coefficients.shape)


if __name__ == "__main__":
    main()
