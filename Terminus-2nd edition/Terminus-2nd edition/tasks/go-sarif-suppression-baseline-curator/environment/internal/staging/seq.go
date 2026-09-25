package staging

import (
	"encoding/json"
	"os"

	"github.com/terminus/sarbctl-curator/internal/model"
)

func Read(path string) (model.FindingStaging, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.FindingStaging{}, err
	}
	var snap model.FindingStaging
	if err := json.Unmarshal(raw, &snap); err != nil {
		return model.FindingStaging{}, err
	}
	return snap, nil
}

func BumpSeq(path string) (int, error) {
	seq := model.StagingSeq{}
	if raw, err := os.ReadFile(path); err == nil {
		_ = json.Unmarshal(raw, &seq)
	}
	seq.ScanRevision++
	if err := os.MkdirAll("/app/state", 0o755); err != nil {
		return 0, err
	}
	out, err := json.MarshalIndent(seq, "", "  ")
	if err != nil {
		return 0, err
	}
	if err := os.WriteFile(path, out, 0o644); err != nil {
		return 0, err
	}
	return seq.ScanRevision, nil
}
