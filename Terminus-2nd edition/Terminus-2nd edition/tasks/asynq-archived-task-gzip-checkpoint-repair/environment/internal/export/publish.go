package export

import (
	"encoding/json"
	"os"

	"github.com/terminus/asynq-archive-repair/internal/model"
	"github.com/terminus/asynq-archive-repair/internal/queue"
	"github.com/terminus/asynq-archive-repair/internal/staging"
)

func BuildManifest(store *queue.Store, stagingPath, seed, scenario string) (model.Manifest, error) {
	ids, err := store.PendingIDs()
	if err != nil {
		return model.Manifest{}, err
	}
	priorities := map[string]int{}
	retries := map[string]int{}
	for _, id := range ids {
		p, err := store.PendingPriority(id)
		if err != nil {
			return model.Manifest{}, err
		}
		priorities[id] = p
		retries[id] = p
	}
	_, _ = staging.ReadSnapshot(stagingPath)
	return model.Manifest{
		Seed:       seed,
		Scenario:   scenario,
		OrderedIDs: ids,
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
