package fixtureio

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"

	"github.com/terminus/wfhistctl/internal/chronorder"
	"github.com/terminus/wfhistctl/internal/model"
)

func fixtureRoot(override string) string {
	if override != "" {
		return override
	}
	return "/app/fixtures"
}

func LoadHistory(ns, scenario, fixtureDir string) ([]model.HistoryEvent, error) {
	_ = ns
	root := fixtureRoot(fixtureDir)
	path := filepath.Join(root, "workflow-histories", scenario, "events.jsonl")
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var events []model.HistoryEvent
	for _, line := range splitLines(string(raw)) {
		var ev model.HistoryEvent
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			return nil, err
		}
		events = append(events, ev)
	}
	return chronorder.SortEvents(events), nil
}

func splitLines(s string) []string {
	var out []string
	for _, line := range strings.Split(s, "\n") {
		line = strings.TrimSpace(line)
		if line != "" {
			out = append(out, line)
		}
	}
	return out
}
