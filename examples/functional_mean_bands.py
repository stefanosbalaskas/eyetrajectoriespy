"""Participant-level simultaneous functional mean bands."""

from eyetrajectoriespy import (
    functional_mean_band_frame,
    functional_mean_band_reporting_text,
    multiplier_functional_mean_band,
    simulate_planar_trajectories,
)


def main() -> None:
    gaze = simulate_planar_trajectories(
        n_participants=20,
        trials_per_participant=4,
        n_time=81,
        random_state=2026,
    )

    band = multiplier_functional_mean_band(
        gaze,
        confidence_level=0.95,
        n_multiplier=1000,
        unit="participant",
        participant_column="participant_id",
        random_state=2026,
    )

    print(functional_mean_band_frame(band).head().to_string(index=False))
    print()
    print(functional_mean_band_reporting_text(band))


if __name__ == "__main__":
    main()
