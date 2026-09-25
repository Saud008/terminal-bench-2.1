package ingest

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/natsjetstream/internal/types"
)

// LoadJournal reads JSONL journal events in file order.
func LoadJournal(path string) ([]types.JournalEvent, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var out []types.JournalEvent
	scanner := bufio.NewScanner(f)
	lineNo := 0
	for scanner.Scan() {
		lineNo++
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var ev types.JournalEvent
		if err := json.Unmarshal(line, &ev); err != nil {
			return nil, fmt.Errorf("line %d: %w", lineNo, err)
		}
		out = append(out, ev)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	return out, nil
}

// BuildSubjectCatalog collects unique PUB subjects in journal order.
func BuildSubjectCatalog(events []types.JournalEvent) []string {
	seen := map[string]struct{}{}
	var out []string
	for _, ev := range events {
		if ev.Op != "PUB" || ev.Subject == "" {
			continue
		}
		if _, ok := seen[ev.Subject]; ok {
			continue
		}
		seen[ev.Subject] = struct{}{}
		out = append(out, ev.Subject)
	}
	sort.Strings(out)
	return out
}
