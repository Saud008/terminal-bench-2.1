package variables

import "github.com/terminus/zeebe-bpmn-replay/internal/model"

func MergeIncidentVariables(v model.VariableBlock) model.VariableSnapshot {
	working := map[string]int{}
	for k, val := range v.Inputs {
		working[k] = val
	}
	protected := map[string]struct{}{}
	for _, srcKey := range v.OutputMapping {
		protected[srcKey] = struct{}{}
	}
	for k, val := range v.IncidentOverlay {
		if _, ok := protected[k]; ok {
			continue
		}
		working[k] = val
	}
	resolved := map[string]int{}
	for outKey, srcKey := range v.OutputMapping {
		resolved[outKey] = working[srcKey]
	}
	return model.VariableSnapshot{Working: working, ResolvedOutputs: resolved}
}
