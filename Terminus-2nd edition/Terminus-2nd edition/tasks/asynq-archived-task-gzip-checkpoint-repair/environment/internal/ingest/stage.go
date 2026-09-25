package ingest

import (
	"bufio"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"github.com/terminus/asynq-archive-repair/internal/model"
	"github.com/terminus/asynq-archive-repair/internal/queue"
)

func NamespacedID(seed, raw string) string {
	return fmt.Sprintf("%s:%s", seed, raw)
}

func LoadScenario(path, seed, defaultQueue string) ([]model.TaskRecord, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	var out []model.TaskRecord
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var t model.TaskRecord
		if err := json.Unmarshal([]byte(line), &t); err != nil {
			return nil, err
		}
		if t.Queue == "" {
			t.Queue = defaultQueue
		}
		t.ID = NamespacedID(seed, t.ID)
		out = append(out, t)
	}
	return out, sc.Err()
}

func ArchivedTimesFromScenario(path, seed string) (map[string]int64, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	out := map[string]int64{}
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if line == "" {
			continue
		}
		var row struct {
			ID           string `json:"id"`
			ArchivedAtMs int64  `json:"archived_at_ms"`
		}
		if err := json.Unmarshal([]byte(line), &row); err != nil {
			return nil, err
		}
		if row.ArchivedAtMs > 0 {
			out[NamespacedID(seed, row.ID)] = row.ArchivedAtMs
		}
	}
	return out, sc.Err()
}

func SeedQueue(store *queue.Store, tasks []model.TaskRecord) error {
	for _, t := range tasks {
		if err := store.InsertPending(t); err != nil {
			return err
		}
	}
	return nil
}

func CanonicalOrder(tasks []model.TaskRecord) []string {
	seen := map[string]struct{}{}
	var ids []string
	for _, t := range tasks {
		if _, ok := seen[t.ID]; ok {
			continue
		}
		seen[t.ID] = struct{}{}
		ids = append(ids, t.ID)
	}
	return ids
}

func StageSnapshot(path string, snap model.Snapshot) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
