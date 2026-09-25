# Feature standardization

Compute mean and population standard deviation (divide by n, not n-1) for each feature using ONLY examples whose split role is `train` (see group-holdout-split.md).

standardized_x_i = (x_i - mean_i) / max(std_i, 1e-8)

Then multiply the entire standardized vector by `feature_scale` (env TB3_FEATURE_SCALE if set, else config).

Do not use validation or test rows when estimating mean/std.
