package ingest

import (
	"sort"

	"github.com/terminus/actplay/internal/model"
)

// PendingJobKeys lists incident-gated job keys blocked on marker persistence.
func PendingJobKeys(sc model.Scenario) []string {
	jobByKey := map[string]model.JobSpec{}
	for _, job := range sc.Jobs {
		jobByKey[job.JobKey] = job
	}
	seen := map[string]bool{}
	var pending []string
	for _, inc := range sc.Incidents {
		if seen[inc.JobKey] {
			continue
		}
		job, ok := jobByKey[inc.JobKey]
		if !ok {
			continue
		}
		if inc.MarkerPersistedAtMs <= job.IntentAtMs {
			continue
		}
		pending = append(pending, inc.JobKey)
		seen[inc.JobKey] = true
	}
	sort.Strings(pending)
	return pending
}
