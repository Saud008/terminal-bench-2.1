package ingest

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/terminus/mlflow-provenance-curator/internal/model"
)

func ScenarioPath(dir, scenario string) string {
	return filepath.Join(dir, scenario+".json")
}

func LoadScenario(path, seed string) (model.ScenarioFile, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.ScenarioFile{}, err
	}
	var sc model.ScenarioFile
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.ScenarioFile{}, err
	}
	if sc.ScenarioName == "" {
		return model.ScenarioFile{}, fmt.Errorf("missing scenario_name")
	}
	_ = seed
	return sc, nil
}

func ScopeRunID(seed, runID string) string {
	x := uint32(2166136261)
	for _, b := range []byte(seed + ":" + runID) {
		x ^= uint32(b)
		x *= 16777619
	}
	return fmt.Sprintf("%s-%08x", runID, x)
}

func Materialize(sc model.ScenarioFile, seed string) []model.ScopedRun {
	out := make([]model.ScopedRun, 0, len(sc.Runs))
	for _, r := range sc.Runs {
		parent := r.ParentRunID
		if parent != "" {
			parent = ScopeRunID(seed, parent)
		}
		out = append(out, model.ScopedRun{
			RunID:       ScopeRunID(seed, r.RunID),
			ParentRunID: parent,
			Params:      r.Params,
			Metrics:     append([]model.MetricPoint(nil), r.Metrics...),
			Artifacts:   append([]model.Artifact(nil), r.Artifacts...),
			DatasetPins: append([]model.DatasetPin(nil), r.DatasetPins...),
		})
	}
	return out
}

func FindRun(runs []model.ScopedRun, scopedID string) (model.ScopedRun, bool) {
	for _, r := range runs {
		if r.RunID == scopedID {
			return r, true
		}
	}
	return model.ScopedRun{}, false
}

func ChildrenOf(runs []model.ScopedRun, parentID string) []string {
	var kids []string
	for _, r := range runs {
		if strings.TrimSpace(r.ParentRunID) == parentID {
			kids = append(kids, r.RunID)
		}
	}
	return kids
}
