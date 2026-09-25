//go:build ignore

package tz

import (
	"time"

	"github.com/terminus/gocron-overlap-repair/internal/model"
)

// ResolveLocation picks the IANA zone for a job.
func ResolveLocation(job model.JobSpec, defaultLoc string) (*time.Location, error) {
	name := job.Location
	if tag, ok := job.Tags["tz"]; ok && tag != "" {
		name = tag
	}
	if name == "" {
		name = defaultLoc
	}
	return time.LoadLocation(name)
}
