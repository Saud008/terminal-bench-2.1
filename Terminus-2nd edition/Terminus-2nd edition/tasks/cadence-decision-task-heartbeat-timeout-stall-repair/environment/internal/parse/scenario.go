package parse

import (
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/cadence-replay/internal/model"
)

func LoadScenario(path string) (model.Scenario, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return model.Scenario{}, err
	}
	var sc model.Scenario
	if err := json.Unmarshal(raw, &sc); err != nil {
		return model.Scenario{}, err
	}
	if sc.WorkflowID == "" {
		return model.Scenario{}, fmt.Errorf("workflow_id required")
	}
	sort.Slice(sc.HistoryEvents, func(i, j int) bool {
		if sc.HistoryEvents[i].Seq == sc.HistoryEvents[j].Seq {
			return sc.HistoryEvents[i].AtMs < sc.HistoryEvents[j].AtMs
		}
		return sc.HistoryEvents[i].Seq < sc.HistoryEvents[j].Seq
	})
	sort.Slice(sc.Heartbeats, func(i, j int) bool {
		return sc.Heartbeats[i].AtMs < sc.Heartbeats[j].AtMs
	})
	sort.Slice(sc.StickyGenerations, func(i, j int) bool {
		return sc.StickyGenerations[i].AtMs < sc.StickyGenerations[j].AtMs
	})
	return sc, nil
}
