# Confusion, Brier, ECE

On the test split with the selected threshold:

Confusion counts: TP, FP, TN, FN using score >= threshold.

Brier score = mean over test of (score - label)^2.

ECE (expected calibration error):
- Partition scores into 10 equal-width bins on [0,1]: [0,0.1), [0.1,0.2), ..., [0.9,1.0] (last bin inclusive of 1.0).
- For each non-empty bin: |mean(score) - mean(label)| * (bin_count / n_test)
- ECE = sum over bins.

Empty bins contribute 0.
