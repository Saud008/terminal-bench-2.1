package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/ballotmesh/internal/model"
	"github.com/terminus/ballotmesh/internal/staging"
)

func WriteReport(output string, _ string) error {
	raw, err := os.ReadFile(staging.ManifestPath())
	if err != nil {
		return err
	}
	var snap model.SurveySnapshot
	if err := json.Unmarshal(raw, &snap); err != nil {
		return err
	}
	report := model.SurveyReport{
		ReportVersion:      1,
		TableSuffix:        snap.TableSuffix,
		MeshID:             snap.MeshID,
		SurveyID:           snap.SurveyID,
		Records:            snap.Records,
		FinalTally:         snap.FinalTally,
		TotalWeighted:      snap.TotalWeighted,
		PartialRespondents: snap.PartialRespondents,
		ExportSource:       "staging_manifest",
	}
	out, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(output, out, 0o644)
}
