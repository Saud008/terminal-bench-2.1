package readiness

import (
    "github.com/terminus/chmutled/internal/detach"
    "github.com/terminus/chmutled/internal/mutver"
    "github.com/terminus/chmutled/internal/replag"
)

func State(detached bool, lagMax, threshold, version int, maxVersion int) string {
    if detach.IsDetached([]bool{detached}) {
        return "detached"
    }
    if replag.Suppressed(lagMax, threshold) {
        return "suppressed"
    }
    if mutver.Greater(version, maxVersion) {
        return "ready"
    }
    if version == maxVersion {
        return "ready"
    }
    return "pending"
}
