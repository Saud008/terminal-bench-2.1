package export

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"

	"github.com/terminus/asynq-archive-repair/internal/archive"
	"github.com/terminus/asynq-archive-repair/internal/model"
	"github.com/terminus/asynq-archive-repair/internal/queue"
	"github.com/terminus/asynq-archive-repair/internal/staging"
)

func BuildManifest(store *queue.Store, stagingPath, seed, scenario string) (model.Manifest, error) {
	snap, err := staging.ReadSnapshot(stagingPath)
	if err != nil {
		return model.Manifest{}, err
	}
	base := filepath.Join("/app/work/archives", fmt.Sprintf("%s-%s", seed, scenario))
	idx, err := archive.ReadIndex(base + ".idx.json")
	if err != nil {
		return model.Manifest{}, err
	}
	final := map[string]model.TaskRecord{}
	for _, member := range idx.Members {
		tasks, err := archive.ReadMemberTasks(base+".bundle", member)
		if err != nil {
			return model.Manifest{}, err
		}
		for _, t := range tasks {
			final[t.ID] = t
		}
	}
	var ordered []string
	for _, id := range snap.OrderedIDs {
		if _, ok := final[id]; ok {
			ordered = append(ordered, id)
		}
	}
	priorities := map[string]int{}
	retries := map[string]int{}
	for _, id := range ordered {
		t := final[id]
		priorities[id] = t.Priority
		retries[id] = t.Retry
	}
	return model.Manifest{
		Seed:       seed,
		Scenario:   scenario,
		OrderedIDs: ordered,
		Priorities: priorities,
		Retries:    retries,
	}, nil
}

func WriteManifest(path string, m model.Manifest) error {
	raw, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, raw, 0o644)
}
