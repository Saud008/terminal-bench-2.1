# LAB delta and drift classes

CIE76 delta_e is the numerical Euclidean distance in LAB space: sqrt((L1-L2)^2 + (a1-a2)^2 + (b1-b2)^2) rounded to six decimals half-up. Verifier tolerance is 1e-4 on delta_e comparisons against independent reference math.

warn_delta_e and fail_delta_e come from /app/config/shadedrift.json. drift_class is within when delta_e is less than or equal to warn_delta_e, watch when greater than warn and less than or equal to fail, reject when greater than fail.
