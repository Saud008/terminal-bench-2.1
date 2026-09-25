//go:build ignore

package scheduler

import "github.com/terminus/gocron-overlap-repair/internal/model"

type JobSpecView struct {
	ID   string
	Cron string
}

type JobLike interface {
	Spec() JobSpecView
}

func SpecView(job model.JobSpec) JobSpecView {
	return JobSpecView{ID: job.ID, Cron: job.Cron}
}
