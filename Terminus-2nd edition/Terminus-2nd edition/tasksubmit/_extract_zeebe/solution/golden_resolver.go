package incident

import "github.com/terminus/zeebe-bpmn-replay/internal/model"

func ActivationBarrierMs(sc model.Scenario, job model.JobSpec) (int64, string) {
	for _, inc := range sc.Incidents {
		if inc.JobKey != job.JobKey {
			continue
		}
		at := inc.MarkerPersistedAtMs
		if job.IntentAtMs > at {
			at = job.IntentAtMs
		}
		return at, "incident_marker_persisted"
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
