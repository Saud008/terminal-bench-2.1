# Stable sigmoid

logit = bias + sum_i weight_i * standardized_x_i

score = sigmoid(logit) with overflow-safe implementation:
- if logit >= 0: 1 / (1 + exp(-logit))
- if logit < 0: exp(logit) / (1 + exp(logit))

Do not call exp(logit) for large positive logits.
