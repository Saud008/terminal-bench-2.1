package ingest

import (
	"encoding/json"
	"os"

	"yaracor/internal/model"
)

func LoadEvents(path string) ([]model.ScanEvent, error) {
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var events []model.ScanEvent
	for _, line := range splitLines(string(raw)) {
		if line == "" {
			continue
		}
		var ev model.ScanEvent
		if err := json.Unmarshal([]byte(line), &ev); err != nil {
			return nil, err
		}
		events = append(events, ev)
	}
	return events, nil
}

func splitLines(s string) []string {
	var out []string
	start := 0
	for i := 0; i < len(s); i++ {
		if s[i] == '\n' {
			out = append(out, s[start:i])
			start = i + 1
		}
	}
	if start < len(s) {
		out = append(out, s[start:])
	}
	return out
}
