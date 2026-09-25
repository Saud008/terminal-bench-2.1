package boundary

import "github.com/terminus/actplay/internal/model"

func CanFire(sc model.Scenario, b model.BoundaryEvent) bool {
	for _, job := range sc.Jobs {
		if job.ElementID != b.AttachedElement {
			continue
		}
		if b.FireAtMs < job.ActivatingUntilMs {
			return false
		}
	}
	return true
}
