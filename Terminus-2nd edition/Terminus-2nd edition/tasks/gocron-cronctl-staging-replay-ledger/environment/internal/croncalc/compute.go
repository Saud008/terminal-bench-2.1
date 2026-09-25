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
			if gap := springForwardGap(next, loc); !gap.IsZero() && gap.Before(end) && gap.UnixMilli() != next.UnixMilli() {
				fires = append(fires, model.PlannedFire{JobID: job.ID, AtMs: gap.UnixMilli()})
			}
			cursor = next
		}
	}
	return fires, nil
}

func springForwardGap(t time.Time, loc *time.Location) time.Time {
	dayStart := time.Date(t.Year(), t.Month(), t.Day(), 0, 0, 0, 0, loc)
	_, offStart := dayStart.Zone()
	for m := 0; m < 24*60; m++ {
		probe := dayStart.Add(time.Duration(m) * time.Minute)
		_, off := probe.Zone()
		if off > offStart+1800 {
			return time.Date(t.Year(), t.Month(), t.Day(), 2, 30, 0, 0, loc)
		}
	}
	return time.Time{}
}
