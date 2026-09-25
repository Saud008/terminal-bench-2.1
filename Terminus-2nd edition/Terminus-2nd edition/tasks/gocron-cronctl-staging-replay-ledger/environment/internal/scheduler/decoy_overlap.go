package scheduler

import "github.com/terminus/gocron-overlap-repair/internal/model"

// MergeOverlapsByCron keeps one schedule row per distinct cron expression string.
func MergeOverlapsByCron(jobs []model.JobSpec) []model.JobSpec {
	return MergeOverlaps(jobs)
}
