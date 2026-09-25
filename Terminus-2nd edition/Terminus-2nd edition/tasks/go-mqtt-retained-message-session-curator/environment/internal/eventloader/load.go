package eventloader

import (
    "encoding/json"
    "os"
    "path/filepath"
    "sort"
    "strings"
)

import "github.com/edgeiot/mqttsessctl/internal/model"

func LoadJournal(broker, scenario, fixtureRoot string) ([]model.JournalEvent, error) {
    path := filepath.Join(fixtureRoot, "broker-journals", scenario, "events.jsonl")
    raw, err := os.ReadFile(path)
    if err != nil {
        return nil, err
    }
    var events []model.JournalEvent
    for _, line := range splitLines(string(raw)) {
        var ev model.JournalEvent
        if err := json.Unmarshal([]byte(line), &ev); err != nil {
            return nil, err
        }
        events = append(events, ev)
    }
    sort.Slice(events, func(i, j int) bool { return events[i].Seq < events[j].Seq })
    return events, nil
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
