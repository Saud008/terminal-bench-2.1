# F-beta threshold search

On validation examples only, search thresholds in {0.05, 0.10, ..., 0.95}.

Predict positive when score >= threshold (inclusive).

For each threshold compute F-beta with beta=1.5:
  precision = TP / max(TP+FP, 1)
  recall = TP / max(TP+FN, 1)
  f_beta = (1+beta^2) * precision * recall / max(beta^2 * precision + recall, 1e-12)

Select the threshold with maximum f_beta. Tie-break: prefer the **lower** threshold. If still tied, prefer the threshold that yields higher recall.
