package scheduler

import (
	"github.com/terminus/riverbench/internal/model"
)

// ApplyFailure increments attempts and schedules retry or poison.
func ApplyFailure(job model.Job, nowMs int64, baseMs int64, errMsg string) model.Job {
	job.Attempts++
	job.LastError = errMsg
	if job.Attempts >= job.MaxAttempts {
		job.State = model.StatePoison
		job.AvailableAt = 0
		return job
	}
	job.State = model.StatePending
	job.AvailableAt = nowMs + BackoffDelayMs(job.Attempts, baseMs, nowMs)
	return job
}
