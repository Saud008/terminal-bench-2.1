package ingest

import (
	"github.com/terminus/zeebe-bpmn-replay/internal/model"
	"github.com/terminus/zeebe-bpmn-replay/internal/staging"
)

// StageScenario persists ingest snapshot before export stage runs.
func StageScenario(sc model.Scenario) error {
	snap := model.Snapshot{
		ProcessID:                 sc.ProcessID,
		PartitionID:               sc.PartitionID,
		IncidentMarkerPersistedMs: map[string]int64{},
		PendingJobKeys:            PendingJobKeys(sc),
		BoundaryEventsFired:       []string{},
		DedupPairs:                []string{},
		StagingWritten:            false,
	}
	for _, inc := range sc.Incidents {
		snap.IncidentMarkerPersistedMs[inc.IncidentKey] = inc.MarkerPersistedAtMs
	}
	return staging.WriteSnapshot(snap)
}
