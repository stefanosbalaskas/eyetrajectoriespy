# Derived continuous functions

Available helpers include `speed_function()`, `acceleration_magnitude_function()`, `distance_to_landmark_function()`, `cumulative_path_length()`, `heading_function()`, `signed_curvature_function()`, `turning_rate_function()`, and `trajectory_tortuosity()`.

## Derivatives amplify noise

Velocity and acceleration are numerical derivatives. The package does not automatically smooth before differentiating.

## Landmark distance

Distance to a source card, disclosure, or decision target can create a single interpretable continuous function.

## Path length

Cumulative path length captures exploratory extent over trial time but does not preserve direction or location.


## Continuous planar geometry

Version 0.31 extends the derived-function layer from kinematics to planar differential geometry.

- \`heading_function()\` returns wrapped direction in radians;
- \`signed_curvature_function()\` returns local signed path curvature;
- \`turning_rate_function()\` returns signed angular change per unit time;
- \`trajectory_tortuosity()\` returns observed path length divided by endpoint displacement.

These quantities remain conditional on the declared coordinate metric. Separately normalized horizontal/vertical axes can distort Euclidean geometry, and screen \(y\)-axis direction affects the visual interpretation of signed curvature.

## Low speed is explicit

Curvature and turning direction become unstable as speed approaches zero. The package does not add a small denominator epsilon or choose a near-zero threshold silently.

Use \`min_speed\` and \`undefined_policy\` explicitly. Missing geometry remains \`NaN\` rather than being converted to zero.

## Heading is circular

Wrapped angles near \(-\pi\) and \(+\pi\) are physically close but numerically distant. Standard Euclidean FPCA is therefore not automatically appropriate for wrapped heading.

## More detail

See the [continuous trajectory geometry method guide](../methods/trajectory-geometry.md), [worked example](../examples/trajectory-geometry.md), and [mathematical reference](../methods/mathematical-reference.md#trajectory-geometry).
