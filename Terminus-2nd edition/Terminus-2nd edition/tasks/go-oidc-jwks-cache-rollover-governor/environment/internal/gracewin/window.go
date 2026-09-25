package gracewin

import (
    "os"
    "strconv"
)

const DefaultGrace = 120

func GraceSec(fallback int) int {
    if raw := os.Getenv("TB3_GRACE_SEC"); raw != "" {
        if v, err := strconv.Atoi(raw); err == nil && v >= 0 {
            return v
        }
    }
    if fallback > 0 {
        return fallback
    }
    return DefaultGrace
}

// InGrace evaluates grace-window-contract.md inclusive bounds.
func InGrace(signatureEpoch, retiredEpoch, graceSec int) bool {
    return signatureEpoch > retiredEpoch && signatureEpoch <= retiredEpoch+graceSec
}
