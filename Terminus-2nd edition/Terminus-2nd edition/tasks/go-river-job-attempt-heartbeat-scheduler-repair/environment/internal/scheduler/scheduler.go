package scheduler

import (
	"fmt"

	"github.com/terminus/riverbench/internal/clock"
	"github.com/terminus/riverbench/internal/model"
	"github.com/terminus/riverbench/internal/store"
)

type Scheduler struct {
	Store      *store.Store
	Clock      clock.Clock
	LeaseMs    int64
	BackoffBase int64
	DefaultMax int
}

func (s *Scheduler) Claim(workerID string) (model.Job, error) {
	now := s.Clock.NowMs()
	pending, err := s.Store.ListPendingReady(now)
	if err != nil {
		return model.Job{}, err
	}
	job, ok := SelectNext(pending)
	if !ok {
		return model.Job{}, fmt.Errorf("no jobs available")
	}
	job.State = model.StateRunning
	if err := s.Store.UpdateJob(job); err != nil {
		return model.Job{}, err
	}
	lease := model.Lease{
		JobID:       job.ID,
		WorkerID:    workerID,
		ExpiresAtMs: now + s.LeaseMs,
		HeartbeatMs: now,
	}
	if err := s.Store.UpsertLease(lease); err != nil {
		return model.Job{}, err
	}
	return job, nil
}

func (s *Scheduler) Heartbeat(workerID, jobID string) (model.Lease, error) {
	return ExtendHeartbeat(s.Store, workerID, jobID, s.Clock.NowMs(), s.LeaseMs)
}

func (s *Scheduler) Ack(workerID, jobID string) error {
	job, err := s.Store.GetJob(jobID)
	if err != nil {
		return err
	}
	lease, err := s.Store.GetLease(jobID)
	if err != nil {
		return fmt.Errorf("lease missing")
	}
	if lease.WorkerID != workerID {
		return fmt.Errorf("worker mismatch")
	}
	return s.Store.MarkFinished(job, s.Clock.NowMs())
}

func (s *Scheduler) Fail(workerID, jobID, errMsg string) error {
	job, err := s.Store.GetJob(jobID)
	if err != nil {
		return err
	}
	lease, err := s.Store.GetLease(jobID)
	if err != nil {
		return fmt.Errorf("lease missing")
	}
	if lease.WorkerID != workerID {
		return fmt.Errorf("worker mismatch")
	}
	updated := ApplyFailure(job, s.Clock.NowMs(), s.BackoffBase, errMsg)
	if err := s.Store.UpdateJob(updated); err != nil {
		return err
	}
	return s.Store.DeleteLease(jobID)
}
