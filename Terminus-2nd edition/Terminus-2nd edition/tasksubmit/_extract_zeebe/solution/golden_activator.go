package job

import "github.com/terminus/zeebe-bpmn-replay/internal/model"

func DeadlineMs(sc model.Scenario) int64 {
	return sc.ProcessClockMs + sc.JobTimeoutMs
}

func LookupJob(sc model.Scenario, jobKey string) (model.JobSpec, bool) {
	for _, j := range sc.Jobs {
		if j.JobKey == jobKey {
			return j, true
		}
	}
	return model.JobSpec{}, false
}
