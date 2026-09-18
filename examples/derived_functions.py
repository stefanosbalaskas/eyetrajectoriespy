"""Continuous speed, landmark distance, and path-length functions."""
from eyetrajectoriespy import cumulative_path_length, distance_to_landmark_function, simulate_planar_trajectories, speed_function

def main() -> None:
    gaze = simulate_planar_trajectories(n_participants=6, trials_per_participant=2, n_time=81)
    speed = speed_function(gaze)
    distance = distance_to_landmark_function(gaze, landmark_x=0.78, landmark_y=0.32)
    path = cumulative_path_length(gaze)
    print("mean speed:", speed.values.mean())
    print("minimum evidence distance:", distance.values.min())
    print("mean final path length:", path.values[:, -1, 0].mean())

if __name__ == "__main__":
    main()
