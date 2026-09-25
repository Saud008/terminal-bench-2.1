package replay

import (
	"sort"
	"time"

	"github.com/terminus/gocron-overlap-repair/internal/clock"
	"github.com/terminus/gocron-overlap-repair/internal/croncalc"
	"github.com/terminus/gocron-overlap-repair/internal/ledger"
	"github.com/terminus/gocron-overlap-repair/internal/lock"
	"github.com/terminus/gocron-overlap-repair/internal/model"
	"github.com/terminus/gocron-overlap-repair/internal/runtracker"
	"github.com/terminus/gocron-overlap-repair/internal/staging"
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
	scenarioStart, err := time.Parse(time.RFC3339, in.Scenario.WindowStart)
	if err != nil {
		return err
	}
	// TB3_CLOCK_START overrides the fake-clock / window start for the tick loop.
	fk := clock.FromEnv(scenarioStart)
	tick := clock.TickMs(in.Cfg.TickMs)
	lease := lock.NewLease(time.Duration(in.Cfg.LockLeaseMs) * time.Millisecond)
	guard := lock.NewSingletonGuard()
	tracker := runtracker.New()

	// Planned fires stay anchored to the scenario window so staging digests remain valid.
	fires, err := croncalc.ComputeFires(in.Scenario, in.Cfg.DefaultLocation)
	if err != nil {
		return err
	}
	sort.Slice(fires, func(i, j int) bool {
		if fires[i].AtMs == fires[j].AtMs {
			return fires[i].JobID < fires[j].JobID
		}
		return fires[i].AtMs < fires[j].AtMs
	})

	endAt := scenarioStart.Add(time.Duration(in.Scenario.WindowEndMs) * time.Millisecond)
	windowStartMs := scenarioStart.UnixMilli()
	prevMs := fk.Now.UnixMilli() - 1
	for !fk.Now.After(endAt) {
		atMs := fk.Now.UnixMilli()
		var held []model.JobSpec
		lastInstant := int64(-1)
		for _, fire := range fires {
			if fire.AtMs <= prevMs || fire.AtMs > atMs {
				continue
			}
			// Coalesce per fire instant: release singleton holds before the next at_ms.
			if lastInstant >= 0 && fire.AtMs != lastInstant {
				for _, j := range held {
					guard.Exit(j)
				}
				held = nil
			}
			lastInstant = fire.AtMs
			job := findJob(in.Scenario.Jobs, fire.JobID)
			if job.Singleton || job.Tags["singleton_group"] != "" {
				if !guard.TryEnter(job) {
					_ = in.Store.Insert(model.ExecutionRow{
						JobID: fire.JobID, FiredAtMs: fire.AtMs, Status: "deduped", Deduped: true,
					})
					continue
				}
				held = append(held, job)
			}
			if !lease.TryAcquire(fire.JobID, fk.Now) {
				continue
			}
			tracker.Start(fire.JobID)
			row := model.ExecutionRow{
				JobID: fire.JobID, FiredAtMs: fire.AtMs, Status: "fired",
				LockHeld: lease.HeldBy(fire.JobID, fk.Now),
			}
			if err := in.Store.Insert(row); err != nil {
				return err
			}
		}
		for _, j := range held {
			guard.Exit(j)
		}
		for _, ev := range in.Scenario.Events {
			evAt := windowStartMs + ev.AtMs
			if evAt <= prevMs || evAt > atMs {
				continue
			}
			switch ev.Action {
			case "reschedule":
				if st := tracker.Reschedule(ev.JobID); st == "aborted" {
					_ = in.Store.Insert(model.ExecutionRow{
						JobID: ev.JobID, FiredAtMs: evAt, Status: "aborted",
					})
				}
			case "panic":
				lease.RenewAfterPanic(ev.JobID, true, fk.Now)
				_ = in.Store.Insert(model.ExecutionRow{
					JobID: ev.JobID, FiredAtMs: evAt, Status: "panic", LockHeld: false,
				})
			}
		}
		for _, job := range in.Scenario.Jobs {
			if !tracker.Running(job.ID) {
				continue
			}
			if tracker.Status(job.ID) == "aborted" {
				guard.Exit(job)
				lease.Release(job.ID)
				continue
			}
			tracker.Finish(job.ID, "success")
			guard.Exit(job)
			lease.Release(job.ID)
		}
		prevMs = atMs
		fk.Advance(tick)
	}
	gen, err := staging.BumpGeneration(staging.GenerationPath(), in.Seed, in.ScenarioName)
	if err != nil {
		return err
	}
	return staging.UpdateReplayGeneration(in.StagingPath, gen)
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
