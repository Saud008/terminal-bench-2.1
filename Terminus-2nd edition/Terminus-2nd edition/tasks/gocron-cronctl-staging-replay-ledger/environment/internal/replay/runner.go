package replay

import (
	"time"

	"github.com/terminus/gocron-overlap-repair/internal/clock"
	"github.com/terminus/gocron-overlap-repair/internal/croncalc"
	"github.com/terminus/gocron-overlap-repair/internal/ledger"
	"github.com/terminus/gocron-overlap-repair/internal/lock"
	"github.com/terminus/gocron-overlap-repair/internal/model"
	"github.com/terminus/gocron-overlap-repair/internal/runtracker"
)

type RunInput struct {
	Seed         string
	ScenarioName string
	StagingPath  string
	Scenario     model.Scenario
	Cfg          model.Config
	Store        *ledger.Store
}

func Run(in RunInput) error {
	start, err := time.Parse(time.RFC3339, in.Scenario.WindowStart)
	if err != nil {
		return err
	}
	fk := clock.FromEnv(start)
	tick := clock.TickMs(in.Cfg.TickMs)
	lease := lock.NewLease(time.Duration(in.Cfg.LockLeaseMs) * time.Millisecond)
	guard := lock.NewSingletonGuard()
	tracker := runtracker.New()

	fires, err := croncalc.ComputeFires(in.Scenario, in.Cfg.DefaultLocation)
	if err != nil {
		return err
	}
	fireIndex := map[int64][]model.PlannedFire{}
	for _, f := range fires {
		fireIndex[f.AtMs] = append(fireIndex[f.AtMs], f)
	}

	endAt := start.Add(time.Duration(in.Scenario.WindowEndMs) * time.Millisecond)
	for fk.Now.Before(endAt) {
		atMs := fk.Now.UnixMilli()
		for _, fire := range fireIndex[atMs] {
			job := findJob(in.Scenario.Jobs, fire.JobID)
			wrapped := lock.WrapJob(job.ID, job.Cron)
			if job.Singleton && !guard.TryEnter(wrapped) {
				_ = in.Store.Insert(model.ExecutionRow{
					JobID: fire.JobID, FiredAtMs: atMs, Status: "deduped", Deduped: true,
				})
				continue
			}
			if !lease.TryAcquire(fire.JobID, fk.Now) {
				continue
			}
			tracker.Start(fire.JobID)
			row := model.ExecutionRow{
				JobID: fire.JobID, FiredAtMs: atMs, Status: "fired",
				LockHeld: lease.HeldBy(fire.JobID, fk.Now),
			}
			if err := in.Store.Insert(row); err != nil {
				return err
			}
		}
		for _, ev := range in.Scenario.Events {
			if ev.AtMs != atMs {
				continue
			}
			switch ev.Action {
			case "reschedule":
				tracker.Reschedule(ev.JobID)
			case "panic":
				lease.RenewAfterPanic(ev.JobID, true, fk.Now)
			}
		}
		for _, job := range in.Scenario.Jobs {
			if !tracker.Running(job.ID) {
				continue
			}
			wrapped := lock.WrapJob(job.ID, job.Cron)
			status := tracker.Status(job.ID)
			if status == "success" {
				tracker.Finish(job.ID, "success")
			} else if status != "running" && status != "idle" {
				continue
			} else {
				tracker.Finish(job.ID, "success")
				status = "success"
			}
			_ = status
			guard.Exit(wrapped)
			lease.Release(job.ID)
		}
		fk.Advance(tick)
	}
	return nil
}

func findJob(jobs []model.JobSpec, id string) model.JobSpec {
	for _, j := range jobs {
		if j.ID == id {
			return j
		}
	}
	return model.JobSpec{ID: id}
}

func ComputeFires(sc model.Scenario, defaultLoc string) ([]model.PlannedFire, error) {
	return croncalc.ComputeFires(sc, defaultLoc)
}
