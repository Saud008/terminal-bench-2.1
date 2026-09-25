//go:build ignore

package scheduler

import "github.com/terminus/gocron-overlap-repair/internal/model"

// OverlapKey returns a dedup key for overlapping entries keyed by cron expression.
func OverlapKey(job model.JobSpec) string {
	return job.Cron
}

func OverlapKeyView(view JobSpecView) string {
	return view.Cron
}

func HasOverlap(a, b model.JobSpec) bool {
	return OverlapKey(a) == OverlapKey(b)
}
