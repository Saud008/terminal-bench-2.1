package export

import (
	"github.com/terminus/zeebe-bpmn-replay/internal/model"
	"github.com/terminus/zeebe-bpmn-replay/internal/staging"
	"github.com/terminus/zeebe-bpmn-replay/internal/variables"
)

func BuildReport(sc model.Scenario, activations []model.ActivationRecord, boundaries []model.BoundaryRecord, dupSkipped int) (model.ExportReport, error) {
	_, err := staging.LoadSnapshot()
	if err != nil {
		return model.ExportReport{}, err
	}
	if activations == nil {
		activations = []model.ActivationRecord{}
	}
	if boundaries == nil {
		boundaries = []model.BoundaryRecord{}
	}
	vars := variables.MergeIncidentVariables(sc.Variables)
	return model.ExportReport{
		ProcessID:                   sc.ProcessID,
		PartitionID:                 sc.PartitionID,
		ActivationSequence:          activations,
		BoundaryEvents:              boundaries,
		VariableSnapshot:            vars,
		DuplicateActivationsSkipped: dupSkipped,
		DeadlineClockSource:         "broker",
	}, nil
}
