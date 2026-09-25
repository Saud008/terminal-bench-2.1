# Qubit readout drift

Readout drift factors from staging correct normalized probabilities before mitigation matrix application.

Each qubit entry in readout_drift provides a factor multiplier. For normalized probability vector p for qubit q, compute adjusted[i] = p[i] * factor for every bin i.

After multiplication, renormalize the adjusted vector so it sums to 1.0 within tolerance 1e-9.

Drift must never be applied additively as p[i] + (factor - 1.0). Additive drift corrupts shot-noise envelope width.

Drift-corrected vectors are mitigated using the selected matrix. Mitigation applies standard matrix-vector multiplication: mitigated[i] = sum_j matrix[i][j] * drift_corrected[j].
