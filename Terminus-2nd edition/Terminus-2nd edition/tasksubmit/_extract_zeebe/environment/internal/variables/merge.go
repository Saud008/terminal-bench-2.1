package variables

import "github.com/terminus/zeebe-bpmn-replay/internal/model"

// MergeIncidentVariables builds working and resolved outputs after incidents.
func MergeIncidentVariables(v model.VariableBlock) model.VariableSnapshot {
	working := map[string]int{}
	for k, val := range v.Inputs {
		working[k] = val
	}
	resolved := map[string]int{}
	for outKey, srcKey := range v.OutputMapping {
		resolved[outKey] = working[srcKey]
	}
	for k, val := range v.IncidentOverlay {
		resolved[k] = val
	}
	return model.VariableSnapshot{Working: working, ResolvedOutputs: resolved}
}
