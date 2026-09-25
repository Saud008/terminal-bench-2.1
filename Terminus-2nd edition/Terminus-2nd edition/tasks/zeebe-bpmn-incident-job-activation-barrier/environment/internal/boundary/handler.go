package boundary

import "github.com/terminus/actplay/internal/model"

// CanFire returns whether a boundary may fire given job activating windows.
func CanFire(sc model.Scenario, b model.BoundaryEvent) bool {
	for _, job := range sc.Jobs {
		if job.ElementID != b.AttachedElement {
			continue
		}
		if b.FireAtMs < job.IntentAtMs {
			return false
		}
	}
	return true
}
