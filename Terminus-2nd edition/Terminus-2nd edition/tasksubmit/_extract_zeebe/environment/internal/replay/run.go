package replay

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/zeebe-bpmn-replay/internal/boundary"
	"github.com/terminus/zeebe-bpmn-replay/internal/export"
	"github.com/terminus/zeebe-bpmn-replay/internal/incident"
	"github.com/terminus/zeebe-bpmn-replay/internal/ingest"
	"github.com/terminus/zeebe-bpmn-replay/internal/job"
	"github.com/terminus/zeebe-bpmn-replay/internal/model"
	"github.com/terminus/zeebe-bpmn-replay/internal/parse"
	"github.com/terminus/zeebe-bpmn-replay/internal/staging"
)

func ExportScenario(scenarioPath, outputPath string) error {
	sc, err := parse.LoadScenario(scenarioPath)
	if err != nil {
		return err
	}
	if err := ingest.StageScenario(sc); err != nil {
		return err
	}
	snap := model.Snapshot{
		ProcessID:                 sc.ProcessID,
		PartitionID:               sc.PartitionID,
		IncidentMarkerPersistedMs: map[string]int64{},
		PendingJobKeys:            ingest.PendingJobKeys(sc),
		BoundaryEventsFired:       []string{},
		DedupPairs:                []string{},
		StagingWritten:            false,
	}
	for _, inc := range sc.Incidents {
		snap.IncidentMarkerPersistedMs[inc.IncidentKey] = inc.MarkerPersistedAtMs
	}
	jobByKey := map[string]model.JobSpec{}
	for _, j := range sc.Jobs {
		jobByKey[j.JobKey] = j
	}
	var activations []model.ActivationRecord
	dupSkipped := 0
	seq := 1
	deadline := job.DeadlineMs(sc)
	for _, batch := range sc.ReplayBatches {
		for _, jobKey := range batch.JobKeys {
			if !ShouldActivate(&snap, batch, jobKey) {
				dupSkipped++
				continue
			}
			js, ok := jobByKey[jobKey]
			if !ok {
				continue
			}
			at, barrier := incident.ActivationBarrierMs(sc, js)
			activations = append(activations, model.ActivationRecord{
				JobKey:        jobKey,
				ActivatedAtMs: at,
				DeadlineMs:    deadline,
				Barrier:       barrier,
				SequenceNo:    seq,
			})
			seq++
			RecordActivation(&snap, batch, jobKey)
		}
	}
	sort.Slice(activations, func(i, j int) bool {
		return activations[i].SequenceNo < activations[j].SequenceNo
	})
	var boundaries []model.BoundaryRecord
	for _, b := range sc.Boundaries {
		if !boundary.CanFire(sc, b) {
			continue
		}
		boundaries = append(boundaries, model.BoundaryRecord{
			BoundaryID:      b.BoundaryID,
			AttachedElement: b.AttachedElement,
			FiredAtMs:       b.FireAtMs,
			Interrupting:    b.Interrupting,
		})
		snap.BoundaryEventsFired = append(snap.BoundaryEventsFired, b.BoundaryID)
	}
	if err := staging.WriteSnapshot(snap); err != nil {
		return err
	}
	report, err := export.BuildReport(sc, activations, boundaries, dupSkipped)
	if err != nil {
		return err
	}
	raw, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(outputPath, append(raw, '\n'), 0o644)
}

func ExportCLI(scenarioPath, outputPath string) int {
	if _, err := os.Stat(scenarioPath); err != nil {
		fmt.Fprintf(os.Stderr, "scenario not found: %s\n", scenarioPath)
		return 2
	}
	if err := ExportScenario(scenarioPath, outputPath); err != nil {
		fmt.Fprintf(os.Stderr, "export failed: %v\n", err)
		return 3
	}
	return 0
}
