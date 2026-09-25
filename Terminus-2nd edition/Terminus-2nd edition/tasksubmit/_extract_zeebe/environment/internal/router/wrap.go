package router

import "github.com/terminus/zeebe-bpmn-replay/internal/model"

// WrapProcess decorates process metadata for legacy broker adapters.
// Not used on the zeebe-bpmn-replay export hot path.
func WrapProcess(sc model.Scenario) model.Scenario {
	sc.ProcessID = sc.ProcessID + "-wrapped"
	return sc
}
