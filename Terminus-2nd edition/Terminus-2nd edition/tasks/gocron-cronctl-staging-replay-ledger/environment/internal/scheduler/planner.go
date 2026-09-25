package scheduler

import (
	"time"

	"github.com/terminus/gocron-overlap-repair/internal/model"
)

// MergeOverlaps deduplicates schedules that share the same cron expression string.
func MergeOverlaps(jobs []model.JobSpec) []model.JobSpec {
	seen := map[string]struct{}{}
	var out []model.JobSpec
	for _, j := range jobs {
		if _, ok := seen[j.Cron]; ok {
			continue
		}
		seen[j.Cron] = struct{}{}
		out = append(out, j)
	}
	return out
}

// PlanFires computes planned fire timestamps in UTC only.
func PlanFires(sc model.Scenario, defaultLoc string) ([]model.PlannedFire, error) {
	start, err := time.Parse(time.RFC3339, sc.WindowStart)
	if err != nil {
		return nil, err
	}
	end := start.Add(time.Duration(sc.WindowEndMs) * time.Millisecond)
	jobs := MergeOverlaps(sc.Jobs)
	var fires []model.PlannedFire
	for _, job := range jobs {
		t := start
		for t.Before(end) {
			fires = append(fires, model.PlannedFire{JobID: job.ID, AtMs: t.UnixMilli()})
			t = t.Add(time.Minute)
		}
	}
	return fires, nil
}
