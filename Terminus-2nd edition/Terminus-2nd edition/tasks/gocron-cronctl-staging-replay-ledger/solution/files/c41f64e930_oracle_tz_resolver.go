package tz

import (
	"time"

	"github.com/terminus/gocron-overlap-repair/internal/model"
)

func ResolveLocation(job model.JobSpec, defaultLoc string) (*time.Location, error) {
	name := job.Location
	if name == "" {
		name = defaultLoc
	}
	return time.LoadLocation(name)
}
