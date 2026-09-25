package readiness

import (
    "github.com/terminus/chmutled/internal/replag"
)

func State(detached bool, lagMax, threshold, version int, maxVersion int) string {
    if detached {
        return "detached"
    }
    if replag.Suppressed(lagMax, threshold) {
        return "suppressed"
    }
    if version == maxVersion {
        return "ready"
    }
    return "pending"
}
