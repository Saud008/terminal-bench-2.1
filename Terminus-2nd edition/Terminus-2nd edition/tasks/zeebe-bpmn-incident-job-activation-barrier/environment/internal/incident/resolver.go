package incident

import "github.com/terminus/actplay/internal/model"

// ActivationBarrierMs returns when a job may activate given incident gating.
func ActivationBarrierMs(sc model.Scenario, job model.JobSpec) (int64, string) {
	for _, inc := range sc.Incidents {
		if inc.JobKey != job.JobKey {
			continue
		}
		at := inc.ResolvedAtMs
		if job.IntentAtMs > at {
			at = job.IntentAtMs
		}
		return at, "incident_marker_persisted"
	}
	if job.IntentAtMs > 0 {
		return job.IntentAtMs, "none"
	}
	return job.IntentAtMs, "none"
}

func IndexIncidents(sc model.Scenario) map[string]model.Incident {
	out := make(map[string]model.Incident, len(sc.Incidents))
	for _, inc := range sc.Incidents {
		out[inc.IncidentKey] = inc
	}
	return out
}
