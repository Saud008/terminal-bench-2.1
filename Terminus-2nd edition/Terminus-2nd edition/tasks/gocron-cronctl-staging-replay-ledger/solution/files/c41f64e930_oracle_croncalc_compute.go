package croncalc

import (
	"time"

	"github.com/robfig/cron/v3"
	"github.com/terminus/gocron-overlap-repair/internal/model"
	"github.com/terminus/gocron-overlap-repair/internal/tz"
)

func ComputeFires(sc model.Scenario, defaultLoc string) ([]model.PlannedFire, error) {
	start, err := time.Parse(time.RFC3339, sc.WindowStart)
	if err != nil {
		return nil, err
	}
	end := start.Add(time.Duration(sc.WindowEndMs) * time.Millisecond)
	var fires []model.PlannedFire
	for _, job := range sc.Jobs {
		loc, err := tz.ResolveLocation(job, defaultLoc)
		if err != nil {
			return nil, err
		}
		parser := cron.NewParser(cron.Minute | cron.Hour | cron.Dom | cron.Month | cron.Dow)
		sched, err := parser.Parse(job.Cron)
		if err != nil {
			return nil, err
		}
		cursor := start.Add(-time.Nanosecond).In(loc)
		for {
			next := sched.Next(cursor)
			if next.IsZero() || !next.Before(end) {
				break
			}
			fires = append(fires, model.PlannedFire{JobID: job.ID, AtMs: next.UnixMilli()})
			cursor = next
		}
	}
	return fires, nil
}
