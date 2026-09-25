package icebridge

import "github.com/terminus/iceexpctl/internal/planemit"

func SealExpiryPlan(scenario, planPath, orphanPath string) error {
    return planemit.Emit(scenario, planPath, orphanPath)
}
