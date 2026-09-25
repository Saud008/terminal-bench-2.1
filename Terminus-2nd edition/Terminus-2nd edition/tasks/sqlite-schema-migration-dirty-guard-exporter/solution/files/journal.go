package ingest

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"sort"

	"github.com/terminus/sqlitemigrate/internal/types"
)

// LoadJournal reads JSONL migration journal entries sorted by seq.
func LoadJournal(path string) ([]types.JournalEntry, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()

	var out []types.JournalEntry
	scanner := bufio.NewScanner(f)
	lineNo := 0
	for scanner.Scan() {
		lineNo++
		line := scanner.Bytes()
		if len(line) == 0 {
			continue
		}
		var ev types.JournalEntry
		if err := json.Unmarshal(line, &ev); err != nil {
			return nil, fmt.Errorf("line %d: %w", lineNo, err)
		}
		out = append(out, ev)
	}
	if err := scanner.Err(); err != nil {
		return nil, err
	}
	sort.SliceStable(out, func(i, j int) bool { return out[i].Seq < out[j].Seq })
	return out, nil
}
